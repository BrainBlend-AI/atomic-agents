import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from atomic_assembler.app import AtomicAssembler
from atomic_assembler.constants import GITHUB_BASE_URL
from atomic_assembler.utils import AtomicToolManager, GithubRepoCloner


def setup_logging(enable_logging: bool):
    if enable_logging:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            handlers=[
                logging.FileHandler("atomic_assembler.log"),
            ],
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
    download_parser.add_argument("name", help="Name of the tool to download")
    download_parser.add_argument("--dest", help="Directory where the tool will be copied")
    return parser


def get_forge_tools():
    cloner = GithubRepoCloner(GITHUB_BASE_URL)
    try:
        cloner.clone()
        return AtomicToolManager.get_forge_tools(cloner.repo_path, cloner.tools_path)
    finally:
        cloner.cleanup()


def list_tools() -> int:
    try:
        tools = get_forge_tools()
    except Exception as error:
        print(f"Could not list Atomic Forge tools: {error}", file=sys.stderr)
        return 1

    for tool in tools:
        print(f"{tool['name']} - {tool['description']}")
    return 0


def download_tool(name: str, destination: str | None) -> int:
    try:
        cloner = GithubRepoCloner(GITHUB_BASE_URL)
        try:
            cloner.clone()
            tools = AtomicToolManager.get_forge_tools(cloner.repo_path, cloner.tools_path)
            tool = next(
                (
                    candidate
                    for candidate in tools
                    if name.lower() in {candidate["name"].lower(), Path(candidate["path"]).name.lower()}
                ),
                None,
            )
            if tool is None:
                available_tools = ", ".join(candidate["name"] for candidate in tools)
                print(f"Unknown tool '{name}'. Available tools: {available_tools}", file=sys.stderr)
                return 1

            target = Path(destination) if destination else Path(name)
            if target.exists():
                print(f"Destination already exists: {target}", file=sys.stderr)
                return 1

            copied_path = AtomicToolManager.copy_atomic_tool_to_destination(tool["path"], target)
        finally:
            cloner.cleanup()
    except Exception as error:
        print(f"Could not download Atomic Forge tool: {error}", file=sys.stderr)
        return 1

    print(f"Downloaded {tool['name']} to {copied_path}")
    print(f"Install dependencies with: pip install -r {Path(copied_path) / 'requirements.txt'}")
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

    app = AtomicAssembler()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
