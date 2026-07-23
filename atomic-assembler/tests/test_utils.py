import json
from pathlib import Path

import git
import pytest

from atomic_assembler import main as assembler_main
from atomic_assembler import utils as assembler_utils
from atomic_assembler.constants import DEFAULT_SOURCES, ForgeSource, redact_source_url
from atomic_assembler.utils import AtomicToolManager, GithubRepoCloner, load_sources, save_sources


def test_github_repo_cloner_uses_configured_branch(monkeypatch):
    cloned = {}

    def clone_from(repo_url, repo_path, branch):
        cloned.update(repo_url=repo_url, repo_path=repo_path, branch=branch)

    monkeypatch.setattr("atomic_assembler.utils.git.Repo.clone_from", clone_from)
    cloner = GithubRepoCloner("https://github.com/example/tools.git", branch="feature/test")

    try:
        cloner.clone()
    finally:
        cloner.cleanup()

    assert cloned["branch"] == "feature/test"


def test_copy_atomic_tool_keeps_dependency_metadata(tmp_path):
    tool_path = tmp_path / "example_tool"
    tool_path.mkdir()
    for filename in ("pyproject.toml", "requirements.txt", "uv.lock", ".coveragerc"):
        (tool_path / filename).write_text(filename)

    destination = tmp_path / "destination"
    destination.mkdir()

    copied_path = Path(AtomicToolManager.copy_atomic_tool(tool_path, destination))

    assert (copied_path / "pyproject.toml").is_file()
    assert (copied_path / "requirements.txt").is_file()
    assert not (copied_path / "uv.lock").exists()
    assert not (copied_path / ".coveragerc").exists()


def test_build_parser_parses_download_destination_and_source_commands():
    parser = assembler_main.build_parser("1.2.3")
    download_args = parser.parse_args(["download", "calculator", "--dest", "tools/calculator"])
    add_args = parser.parse_args(["sources", "add", "team", "file:///tools.git", "--branch", "release"])

    assert download_args.command == "download"
    assert download_args.name == "calculator"
    assert download_args.dest == "tools/calculator"
    assert add_args.sources_command == "add"
    assert add_args.name == "team"
    assert add_args.branch == "release"


def test_source_config_uses_defaults_until_first_write(tmp_path):
    config_path = tmp_path / "sources.json"
    source = ForgeSource("team", "file:///team-forge.git", "main", "tools")

    assert load_sources(config_path) == list(DEFAULT_SOURCES)

    save_sources([source], config_path)

    assert load_sources(config_path) == [source]


def test_source_commands_create_and_update_config(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)

    assert assembler_main.add_source("team", "file:///team-forge.git", "release", "tools") == 0
    assert load_sources(config_path) == [
        *DEFAULT_SOURCES,
        ForgeSource("team", "file:///team-forge.git", "release", "tools"),
    ]
    assert assembler_main.remove_source("team") == 0
    assert load_sources(config_path) == list(DEFAULT_SOURCES)
    assert "Added source 'team'." in capsys.readouterr().out


def test_add_source_rejects_url_with_userinfo(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)

    assert assembler_main.add_source("team", "https://user:super-secret@example.com/forge.git", "main", "tools") == 1

    assert not config_path.exists()
    error = capsys.readouterr().err
    assert "super-secret" not in error
    assert "https://***@example.com/forge.git" in error


def test_load_sources_rejects_legacy_userinfo_without_exposing_credentials(tmp_path):
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "team",
                    "url": "https://user:super-secret@example.com/forge.git",
                    "branch": "main",
                    "tools_path": "tools",
                }
            ]
        )
    )

    with pytest.raises(ValueError) as error:
        load_sources(config_path)

    assert "super-secret" not in str(error.value)
    assert "https://***@example.com/forge.git" in str(error.value)


def test_list_sources_redacts_userinfo(monkeypatch, capsys):
    source = ForgeSource("team", "https://example.com/forge.git", "main", "tools")
    object.__setattr__(source, "url", "https://user:super-secret@example.com/forge.git")
    monkeypatch.setattr(assembler_main, "load_sources", lambda: [source])

    assert assembler_main.list_sources() == 0

    output = capsys.readouterr().out
    assert "super-secret" not in output
    assert "https://***@example.com/forge.git" in output
    assert redact_source_url(source.url) in output


def test_get_forge_tools_falls_back_to_tool_directories(tmp_path):
    tools_path = tmp_path / "atomic-forge" / "tools"
    tool_path = tools_path / "example_tool"
    tool_path.mkdir(parents=True)
    (tool_path / "README.md").write_text("# Example Tool\n\nOne-line description.\n")

    tools = AtomicToolManager.get_forge_tools(tmp_path, tools_path)

    assert tools == [
        {
            "name": "example-tool",
            "path": str(tool_path),
            "description": "One-line description.",
        }
    ]


def test_list_tools_reads_each_source_and_labels_tools(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    team = create_git_forge(tmp_path, "team", "internal-search")

    assert assembler_main.list_tools([official, team]) == 0

    assert capsys.readouterr().out.splitlines() == [
        "official/calculator - calculator for tests",
        "team/internal-search - internal-search for tests",
    ]


def test_download_tool_from_second_source(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    team = create_git_forge(tmp_path, "team", "internal-search")
    destination = tmp_path / "downloaded"

    assert assembler_main.download_tool("internal-search", str(destination), [official, team]) == 0

    assert (destination / "tool" / "internal-search.py").is_file()
    assert (destination / "pyproject.toml").is_file()
    assert (destination / "requirements.txt").is_file()
    assert "Downloaded team/internal-search" in capsys.readouterr().out


def test_download_tool_defaults_to_tool_directory_in_current_working_directory(tmp_path, monkeypatch, capsys):
    source = create_git_forge(tmp_path, "official", "calculator")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(assembler_main, "load_sources", lambda: [source])
    monkeypatch.setattr("sys.argv", ["atomic", "download", "calculator"])

    assert assembler_main.main() == 0

    destination = tmp_path / "calculator"
    assert (destination / "tool" / "calculator.py").is_file()
    assert (destination / "pyproject.toml").is_file()
    assert (destination / "requirements.txt").is_file()
    assert "Downloaded official/calculator" in capsys.readouterr().out


def test_download_tool_requires_source_qualification_for_ambiguous_names(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    team = create_git_forge(tmp_path, "team", "calculator")

    assert assembler_main.download_tool("calculator", str(tmp_path / "downloaded"), [official, team]) == 1

    assert "Use <source>/<name>" in capsys.readouterr().err


def test_list_tools_skips_bad_source(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    missing = ForgeSource("missing", (tmp_path / "missing").as_uri(), "main", "atomic-forge/tools")

    assert assembler_main.list_tools([official, missing]) == 0

    captured = capsys.readouterr()
    assert "official/calculator" in captured.out
    assert "Could not read source 'missing'" in captured.err


def create_git_forge(tmp_path, name, tool_name):
    forge_root = tmp_path / name
    tool_path = forge_root / "atomic-forge" / "tools" / tool_name
    (tool_path / "tool").mkdir(parents=True)
    for filename in ("README.md", "pyproject.toml", "requirements.txt", "uv.lock", ".coveragerc"):
        (tool_path / filename).write_text(filename)
    (tool_path / "tool" / f"{tool_name}.py").write_text("")
    index_path = forge_root / "atomic-forge" / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "tools": [
                    {
                        "name": tool_name,
                        "path": f"tools/{tool_name}",
                        "description": f"{tool_name} for tests",
                    }
                ],
            }
        )
    )

    repository = git.Repo.init(forge_root)
    with repository.config_writer() as config:
        config.set_value("user", "name", "Atomic Assembler Tests")
        config.set_value("user", "email", "tests@example.com")
    repository.index.add(["atomic-forge"])
    repository.index.commit("Add test forge")
    return ForgeSource(name, forge_root.as_uri(), repository.active_branch.name, "atomic-forge/tools")
