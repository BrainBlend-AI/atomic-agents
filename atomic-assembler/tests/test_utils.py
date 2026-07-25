import json
import os
import tempfile
from pathlib import Path

import git
import pytest

from atomic_assembler import main as assembler_main
from atomic_assembler import utils as assembler_utils
from atomic_assembler.constants import DEFAULT_SOURCES, ForgeSource, redact_source_url
from atomic_assembler.utils import AtomicToolManager, GithubRepoCloner, load_sources, save_sources


def _symlinks_supported() -> bool:
    with tempfile.TemporaryDirectory() as probe_dir:
        try:
            (Path(probe_dir) / "link").symlink_to("target")
        except (OSError, NotImplementedError):
            return False
    return True


requires_symlinks = pytest.mark.skipif(
    not _symlinks_supported(),
    reason="creating symlinks requires a privilege this platform does not grant",
)


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


def test_github_repo_cloner_rejects_credentials_before_clone(monkeypatch):
    clone_called = False

    def clone_from(repo_url, repo_path, branch):
        nonlocal clone_called
        clone_called = True

    monkeypatch.setattr("atomic_assembler.utils.git.Repo.clone_from", clone_from)

    with pytest.raises(ValueError) as error:
        GithubRepoCloner("https://example.com/forge.git?access_token=diagnostic-secret")

    assert "diagnostic-secret" not in str(error.value)
    assert not clone_called


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


@requires_symlinks
@pytest.mark.parametrize(
    ("link_path", "link_target"),
    [
        (Path("escape.txt"), Path("..", "outside.txt")),
        (Path("nested", "escape.txt"), Path("..", "..", "outside.txt")),
    ],
)
def test_copy_atomic_tool_rejects_symlinks_that_escape_tool_directory(tmp_path, link_path, link_target):
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("sensitive")
    tool_path = tmp_path / "example_tool"
    tool_path.mkdir()
    symlink = tool_path / link_path
    symlink.parent.mkdir(parents=True, exist_ok=True)
    symlink.symlink_to(link_target)
    destination = tmp_path / "downloaded"

    with pytest.raises(ValueError, match="unsafe symlink"):
        AtomicToolManager.copy_atomic_tool_to_destination(tool_path, destination)

    assert not destination.exists()


@requires_symlinks
def test_copy_atomic_tool_preserves_safe_relative_symlink(tmp_path):
    tool_path = tmp_path / "example_tool"
    tool_path.mkdir()
    (tool_path / "target.txt").write_text("tool data")
    (tool_path / "link.txt").symlink_to("target.txt")
    destination = tmp_path / "downloaded"

    AtomicToolManager.copy_atomic_tool_to_destination(tool_path, destination)

    copied_link = destination / "link.txt"
    assert copied_link.is_symlink()
    assert copied_link.readlink() == Path("target.txt")


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


def test_add_source_accepts_ssh_uri(tmp_path, monkeypatch):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)
    source_url = "ssh://git@github.com/eigenwise/atomic-agents.git"

    assert assembler_main.add_source("team", source_url, "main", "tools") == 0
    assert load_sources(config_path) == [*DEFAULT_SOURCES, ForgeSource("team", source_url, "main", "tools")]


def test_add_source_accepts_scp_style_ssh_url(tmp_path, monkeypatch):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)
    source_url = "git@github.com:eigenwise/atomic-agents.git"

    assert assembler_main.add_source("team", source_url, "main", "tools") == 0
    assert load_sources(config_path) == [*DEFAULT_SOURCES, ForgeSource("team", source_url, "main", "tools")]


def test_add_source_rejects_ssh_password_without_exposing_it(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)

    assert (
        assembler_main.add_source("team", "ssh://git:super-secret@github.com/eigenwise/atomic-agents.git", "main", "tools")
        == 1
    )

    assert not config_path.exists()
    error = capsys.readouterr().err
    assert "super-secret" not in error
    assert "ssh://***@github.com/eigenwise/atomic-agents.git" in error


@pytest.mark.parametrize(
    ("url", "secret", "redacted_url"),
    [
        ("https://example.com/forge.git?access_token=query-secret", "query-secret", "https://example.com/forge.git?***"),
        ("https://example.com/forge.git#token=fragment-secret", "fragment-secret", "https://example.com/forge.git#***"),
    ],
)
def test_add_source_rejects_url_credentials_outside_userinfo(tmp_path, monkeypatch, capsys, url, secret, redacted_url):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)

    assert assembler_main.add_source("team", url, "main", "tools") == 1

    assert not config_path.exists()
    error = capsys.readouterr().err
    assert secret not in error
    assert redacted_url in error


def test_save_sources_revalidates_url_before_persistence(tmp_path):
    config_path = tmp_path / "sources.json"
    source = ForgeSource("team", "https://example.com/forge.git", "main", "tools")
    object.__setattr__(source, "url", "https://example.com/forge.git?access_token=stored-secret")

    with pytest.raises(ValueError) as error:
        save_sources([source], config_path)

    assert "stored-secret" not in str(error.value)
    assert not config_path.exists()


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


@pytest.mark.parametrize(
    ("url", "secret"),
    [
        ("https://example.com/forge.git?access_token=query-secret", "query-secret"),
        ("https://example.com/forge.git#token=fragment-secret", "fragment-secret"),
    ],
)
def test_load_sources_rejects_legacy_url_credentials_without_exposing_them(tmp_path, url, secret):
    config_path = tmp_path / "sources.json"
    config_path.write_text(json.dumps([{"name": "team", "url": url, "branch": "main", "tools_path": "tools"}]))

    with pytest.raises(ValueError) as error:
        load_sources(config_path)

    assert secret not in str(error.value)


def test_list_sources_redacts_userinfo(monkeypatch, capsys):
    source = ForgeSource("team", "https://example.com/forge.git", "main", "tools")
    object.__setattr__(source, "url", "https://user:super-secret@example.com/forge.git")
    monkeypatch.setattr(assembler_main, "load_sources", lambda: [source])

    assert assembler_main.list_sources() == 0

    output = capsys.readouterr().out
    assert "super-secret" not in output
    assert "https://***@example.com/forge.git" in output
    assert redact_source_url(source.url) in output


@pytest.mark.parametrize(
    ("url", "secret", "redacted_url"),
    [
        ("https://example.com/forge.git?access_token=query-secret", "query-secret", "https://example.com/forge.git?***"),
        ("https://example.com/forge.git#token=fragment-secret", "fragment-secret", "https://example.com/forge.git#***"),
    ],
)
def test_list_sources_redacts_url_credentials_outside_userinfo(monkeypatch, capsys, url, secret, redacted_url):
    source = ForgeSource("team", "https://example.com/forge.git", "main", "tools")
    object.__setattr__(source, "url", url)
    monkeypatch.setattr(assembler_main, "load_sources", lambda: [source])

    assert assembler_main.list_sources() == 0

    output = capsys.readouterr().out
    assert secret not in output
    assert redacted_url in output


@pytest.mark.parametrize("control", ["\x1b]52;c;clipboard\x07", "\x1b[31m", "\N{RIGHT-TO-LEFT OVERRIDE}"])
def test_source_management_output_cannot_emit_terminal_controls(monkeypatch, capsys, control):
    source = ForgeSource(
        f"team{control}",
        f"https://example.com/forge{control}.git",
        f"main{control}",
        f"tools{control}",
    )
    monkeypatch.setattr(assembler_main, "load_sources", lambda: [source])

    assert assembler_main.list_sources() == 0

    output = capsys.readouterr().out
    assert control not in output
    assert "\x1b" not in output
    assert "\x07" not in output
    assert "\N{RIGHT-TO-LEFT OVERRIDE}" not in output


@pytest.mark.parametrize("control", ["\x1b]52;c;clipboard\x07", "\x1b[31m", "\N{RIGHT-TO-LEFT OVERRIDE}"])
def test_rejected_source_url_cannot_emit_terminal_controls(tmp_path, monkeypatch, capsys, control):
    config_path = tmp_path / ".atomic-assembler" / "sources.json"
    monkeypatch.setattr(assembler_utils, "SOURCES_CONFIG_PATH", config_path)

    assert (
        assembler_main.add_source("team", f"https://example.com/forge{control}.git?access_token=secret", "main", "tools") == 1
    )

    output = capsys.readouterr().err
    assert "secret" not in output
    assert control not in output
    assert "\x1b" not in output
    assert "\x07" not in output
    assert "\N{RIGHT-TO-LEFT OVERRIDE}" not in output


@pytest.mark.parametrize("control", ["\x1b]52;c;clipboard\x07", "\x1b[31m", "\N{RIGHT-TO-LEFT OVERRIDE}"])
def test_source_errors_cannot_emit_terminal_controls(monkeypatch, capsys, control):
    source = ForgeSource(f"team{control}", "https://example.com/forge.git", "main", "tools")

    def raise_source_error(_source):
        raise RuntimeError(f"unavailable{control}")

    monkeypatch.setattr(assembler_main, "source_tools", raise_source_error)

    assert assembler_main.list_tools([source]) == 1

    output = capsys.readouterr().err
    assert control not in output
    assert "\x1b" not in output
    assert "\x07" not in output
    assert "\N{RIGHT-TO-LEFT OVERRIDE}" not in output


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


@pytest.mark.parametrize(
    ("indexed_path", "error_type", "error_message"),
    [
        ("/outside", ValueError, "stay within configured tools directory"),
        ("../outside", ValueError, "stay within configured tools directory"),
        ("tools/../tools/calculator", ValueError, "stay within configured tools directory"),
        ("tools/missing", NotADirectoryError, "not a directory"),
        ("tools/not-a-tool.txt", NotADirectoryError, "not a directory"),
    ],
)
def test_get_indexed_forge_tools_rejects_unsafe_tool_paths(tmp_path, indexed_path, error_type, error_message):
    tools_path = tmp_path / "atomic-forge" / "tools"
    (tools_path / "calculator").mkdir(parents=True)
    (tools_path / "not-a-tool.txt").write_text("not a tool")
    index_path = tools_path.parent / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "test",
                "tools": [{"name": "calculator", "path": indexed_path}],
            }
        )
    )

    with pytest.raises(error_type, match=error_message):
        AtomicToolManager.get_indexed_forge_tools(tmp_path, tools_path)


def test_list_tools_reads_each_source_and_labels_tools(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    team = create_git_forge(tmp_path, "team", "internal-search")

    assert assembler_main.list_tools([official, team]) == 0

    assert capsys.readouterr().out.splitlines() == [
        "official/calculator - calculator for tests",
        "team/internal-search - internal-search for tests",
    ]


def test_list_index_metadata_cannot_emit_terminal_sequences(tmp_path, capsys):
    source = create_git_forge(
        tmp_path,
        "official",
        "calculator",
        index_name="\x1b]52;c;clipboard\x07calculator\x1b[31m",
        description="\x1b[31mred\x1b[0m\nsecond line",
    )

    assert assembler_main.list_tools([source]) == 0

    output = capsys.readouterr().out
    assert output == "official/calculator - red second line\n"
    assert "\x1b" not in output
    assert "\x07" not in output


def test_download_error_index_name_cannot_emit_terminal_sequences(tmp_path, capsys):
    source = create_git_forge(
        tmp_path,
        "official",
        "calculator",
        index_name="\x1b]52;c;clipboard\x07calculator\x1b[31m",
    )

    assert assembler_main.download_tool("missing", str(tmp_path / "downloaded"), [source]) == 1

    output = capsys.readouterr().err
    assert "official/calculator" in output
    assert "\x1b" not in output
    assert "\x07" not in output


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


def test_download_default_destination_and_success_output_hide_tool_path_controls(tmp_path, monkeypatch, capsys):
    control_sequence = "\N{RIGHT-TO-LEFT OVERRIDE}" if os.name == "nt" else "\x1b]52;c;clipboard\x07"
    tool_directory_name = f"calculator{control_sequence}clipboard"
    source = create_git_forge(tmp_path, "official", tool_directory_name, index_name="calculator")
    monkeypatch.chdir(tmp_path)

    assert assembler_main.download_tool("calculator", None, [source]) == 0

    assert (tmp_path / tool_directory_name / "tool" / f"{tool_directory_name}.py").is_file()
    output = capsys.readouterr().out
    assert "Downloaded official/calculator" in output
    assert control_sequence not in output
    assert "\x1b" not in output
    assert "\x07" not in output


@pytest.mark.parametrize("control", ["\x1b]52;c;clipboard\x07", "\x1b[31m", "\N{RIGHT-TO-LEFT OVERRIDE}"])
def test_tool_source_qualification_cannot_emit_terminal_controls(tmp_path, capsys, control):
    source = create_git_forge(tmp_path, "team", "calculator")
    object.__setattr__(source, "name", f"team{control}")

    assert assembler_main.list_tools([source]) == 0

    list_output = capsys.readouterr().out
    assert control not in list_output
    assert "\x1b" not in list_output
    assert "\x07" not in list_output
    assert "\N{RIGHT-TO-LEFT OVERRIDE}" not in list_output

    assert assembler_main.download_tool("calculator", str(tmp_path / "downloaded"), [source]) == 0

    download_output = capsys.readouterr().out
    assert control not in download_output
    assert "\x1b" not in download_output
    assert "\x07" not in download_output
    assert "\N{RIGHT-TO-LEFT OVERRIDE}" not in download_output


def test_download_tool_requires_source_qualification_for_ambiguous_names(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    team = create_git_forge(tmp_path, "team", "calculator")

    assert assembler_main.download_tool("calculator", str(tmp_path / "downloaded"), [official, team]) == 1

    assert "Use <source>/<name>" in capsys.readouterr().err


def test_list_tools_returns_success_with_partial_source_failure(tmp_path, capsys):
    official = create_git_forge(tmp_path, "official", "calculator")
    missing = ForgeSource("missing", (tmp_path / "missing").as_uri(), "main", "atomic-forge/tools")

    assert assembler_main.list_tools([official, missing]) == 0

    captured = capsys.readouterr()
    assert "official/calculator" in captured.out
    assert "Could not read source 'missing'" in captured.err


def test_list_tools_returns_failure_when_all_sources_fail(tmp_path, capsys):
    first_missing = ForgeSource("first", (tmp_path / "first").as_uri(), "main", "atomic-forge/tools")
    second_missing = ForgeSource("second", (tmp_path / "second").as_uri(), "main", "atomic-forge/tools")

    assert assembler_main.list_tools([first_missing, second_missing]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Could not read source 'first'" in captured.err
    assert "Could not read source 'second'" in captured.err


def create_git_forge(tmp_path, name, tool_name, index_name=None, description=None):
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
                        "name": index_name or tool_name,
                        "path": f"tools/{tool_name}",
                        "description": description or f"{tool_name} for tests",
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
