import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from atomic_assembler.app import AtomicAssembler
from atomic_assembler.constants import ForgeSource
from atomic_assembler.utils import AtomicToolManager, GithubRepoCloner, load_sources, save_sources


def setup_logging(enable_logging: bool):
    if enable_logging:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            handlers=[logging.FileHandler("atomic_assembler.log")],
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)


def build_parser(pkg_version: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Atomic Assembler", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=f"Version: {pkg_version}"
    )
    parser.add_argument("--enable-logging", action="store_true", help="Enable logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {pkg_version}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("list", help="List available Atomic Forge tools")
    download_parser = subparsers.add_parser("download", help="Download an Atomic Forge tool")
    download_parser.add_argument("name", help="Name of the tool, or source/name when names overlap")
    download_parser.add_argument("--dest", help="Directory where the tool will be copied")

    sources_parser = subparsers.add_parser("sources", help="Manage Atomic Forge sources")
    source_commands = sources_parser.add_subparsers(dest="sources_command", required=True)
    source_commands.add_parser("list", help="List configured Forge sources")
    add_parser = source_commands.add_parser("add", help="Add a Forge source")
    add_parser.add_argument("name")
    add_parser.add_argument("url")
    add_parser.add_argument("--branch", default="main")
    add_parser.add_argument("--tools-path", default="atomic-forge/tools")
    remove_parser = source_commands.add_parser("remove", help="Remove a Forge source")
    remove_parser.add_argument("name")
    return parser


def source_tools(source: ForgeSource) -> list[dict]:
    cloner = GithubRepoCloner(source.url, branch=source.branch, tools_path=source.tools_path)
    try:
        cloner.clone()
        tools = AtomicToolManager.get_indexed_forge_tools(cloner.repo_path, cloner.tools_path)
        return [{**tool, "source": source.name} for tool in tools]
    finally:
        cloner.cleanup()


def get_forge_tools(sources: list[ForgeSource] | None = None) -> tuple[list[dict], list[str]]:
    tools = []
    failures = []
    for source in sources or load_sources():
        try:
            tools.extend(source_tools(source))
        except Exception as error:
            failures.append(f"Could not read source '{source.name}': {error}")
    return tools, failures


def list_tools(sources: list[ForgeSource] | None = None) -> int:
    try:
        tools, failures = get_forge_tools(sources)
    except Exception as error:
        print(f"Could not load Atomic Forge sources: {error}", file=sys.stderr)
        return 1

    for failure in failures:
        print(failure, file=sys.stderr)
    for tool in tools:
        print(f"{tool['source']}/{tool['name']} - {tool['description']}")
    return 0


def matching_tools(name: str, tools: list[dict]) -> list[dict]:
    normalized_name = name.lower()
    return [tool for tool in tools if normalized_name in {tool["name"].lower(), Path(tool["path"]).name.lower()}]


def download_tool(name: str, destination: str | None, sources: list[ForgeSource] | None = None) -> int:
    try:
        configured_sources = sources or load_sources()
    except Exception as error:
        print(f"Could not load Atomic Forge sources: {error}", file=sys.stderr)
        return 1

    source_name, separator, tool_name = name.partition("/")
    if separator:
        selected_sources = [source for source in configured_sources if source.name == source_name]
        if not selected_sources:
            print(f"Unknown source '{source_name}'.", file=sys.stderr)
            return 1
    else:
        selected_sources = configured_sources
        tool_name = name

    cloners = []
    tools = []
    try:
        for source in selected_sources:
            cloner = GithubRepoCloner(source.url, branch=source.branch, tools_path=source.tools_path)
            cloners.append(cloner)
            try:
                cloner.clone()
                tools.extend(
                    {**tool, "source": source.name}
                    for tool in AtomicToolManager.get_indexed_forge_tools(cloner.repo_path, cloner.tools_path)
                )
            except Exception as error:
                print(f"Could not read source '{source.name}': {error}", file=sys.stderr)

        matches = matching_tools(tool_name, tools)
        if not matches:
            available_tools = ", ".join(f"{tool['source']}/{tool['name']}" for tool in tools)
            print(f"Unknown tool '{name}'. Available tools: {available_tools}", file=sys.stderr)
            return 1
        if len(matches) > 1:
            choices = ", ".join(f"{tool['source']}/{tool['name']}" for tool in matches)
            print(f"Tool '{tool_name}' exists in multiple sources. Use <source>/<name>: {choices}", file=sys.stderr)
            return 1

        tool = matches[0]
        target = Path(destination) if destination else Path(tool["path"]).name
        if target.exists():
            print(f"Destination already exists: {target}", file=sys.stderr)
            return 1

        copied_path = AtomicToolManager.copy_atomic_tool_to_destination(tool["path"], target)
    except Exception as error:
        print(f"Could not download Atomic Forge tool: {error}", file=sys.stderr)
        return 1
    finally:
        for cloner in cloners:
            cloner.cleanup()

    print(f"Downloaded {tool['source']}/{tool['name']} to {copied_path}")
    print(f"Install dependencies with: pip install -r {Path(copied_path) / 'requirements.txt'}")
    return 0


def list_sources() -> int:
    try:
        sources = load_sources()
    except Exception as error:
        print(f"Could not load Atomic Forge sources: {error}", file=sys.stderr)
        return 1
    for source in sources:
        print(f"{source.name} {source.url} {source.branch} {source.tools_path}")
    return 0


def add_source(name: str, url: str, branch: str, tools_path: str) -> int:
    if "/" in name:
        print("Source names cannot contain '/'.", file=sys.stderr)
        return 1
    try:
        sources = load_sources()
    except Exception as error:
        print(f"Could not load Atomic Forge sources: {error}", file=sys.stderr)
        return 1
    if any(source.name == name for source in sources):
        print(f"Source already exists: {name}", file=sys.stderr)
        return 1
    save_sources([*sources, ForgeSource(name, url, branch, tools_path)])
    print(f"Added source '{name}'.")
    return 0


def remove_source(name: str) -> int:
    try:
        sources = load_sources()
    except Exception as error:
        print(f"Could not load Atomic Forge sources: {error}", file=sys.stderr)
        return 1
    remaining_sources = [source for source in sources if source.name != name]
    if len(remaining_sources) == len(sources):
        print(f"Unknown source '{name}'.", file=sys.stderr)
        return 1
    save_sources(remaining_sources)
    print(f"Removed source '{name}'.")
    return 0


def main() -> int:
    try:
        pkg_version = version("atomic-agents")
    except PackageNotFoundError:
        pkg_version = "unknown"

    parser = build_parser(pkg_version)
    args = parser.parse_args()
    setup_logging(args.enable_logging)

    if args.command == "list":
        return list_tools()
    if args.command == "download":
        return download_tool(args.name, args.dest)
    if args.command == "sources":
        if args.sources_command == "list":
            return list_sources()
        if args.sources_command == "add":
            return add_source(args.name, args.url, args.branch, args.tools_path)
        return remove_source(args.name)

    app = AtomicAssembler()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
