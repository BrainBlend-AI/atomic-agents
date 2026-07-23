import json
from pathlib import Path

from atomic_assembler import main as assembler_main
from atomic_assembler.utils import AtomicToolManager, GithubRepoCloner


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


def test_build_parser_parses_download_destination():
    args = assembler_main.build_parser("1.2.3").parse_args(["download", "calculator", "--dest", "tools/calculator"])

    assert args.command == "download"
    assert args.name == "calculator"
    assert args.dest == "tools/calculator"


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


def test_list_tools_reads_forge_index(tmp_path, monkeypatch, capsys):
    forge_root = create_forge_fixture(tmp_path)
    use_forge_fixture(monkeypatch, forge_root)

    assert assembler_main.list_tools() == 0

    assert capsys.readouterr().out == "calculator - A calculator for tests\n"


def test_download_tool_copies_to_requested_destination(tmp_path, monkeypatch, capsys):
    forge_root = create_forge_fixture(tmp_path)
    use_forge_fixture(monkeypatch, forge_root)
    destination = tmp_path / "calculator"

    assert assembler_main.download_tool("calculator", str(destination)) == 0

    assert (destination / "tool" / "calculator.py").is_file()
    assert (destination / "tests" / "test_calculator.py").is_file()
    assert (destination / "README.md").is_file()
    assert (destination / "pyproject.toml").is_file()
    assert (destination / "requirements.txt").is_file()
    assert not (destination / "uv.lock").exists()
    assert not (destination / ".coveragerc").exists()
    assert "Downloaded calculator" in capsys.readouterr().out


def test_download_tool_reports_unknown_tool_and_existing_destination(tmp_path, monkeypatch, capsys):
    forge_root = create_forge_fixture(tmp_path)
    use_forge_fixture(monkeypatch, forge_root)

    assert assembler_main.download_tool("missing", str(tmp_path / "missing")) == 1
    assert "Available tools: calculator" in capsys.readouterr().err

    destination = tmp_path / "calculator"
    destination.mkdir()

    assert assembler_main.download_tool("calculator", str(destination)) == 1
    assert f"Destination already exists: {destination}" in capsys.readouterr().err


def create_forge_fixture(tmp_path):
    forge_root = tmp_path / "forge-repo"
    tool_path = forge_root / "atomic-forge" / "tools" / "calculator"
    (tool_path / "tool").mkdir(parents=True)
    (tool_path / "tests").mkdir()
    for filename in ("README.md", "pyproject.toml", "requirements.txt", "uv.lock", ".coveragerc"):
        (tool_path / filename).write_text(filename)
    (tool_path / "tool" / "calculator.py").write_text("")
    (tool_path / "tests" / "test_calculator.py").write_text("")
    (forge_root / "atomic-forge" / "index.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "test-forge",
                "tools": [
                    {
                        "name": "calculator",
                        "path": "tools/calculator",
                        "description": "A calculator for tests",
                    }
                ],
            }
        )
    )
    return forge_root


def use_forge_fixture(monkeypatch, forge_root):
    class ForgeCloner:
        def __init__(self, *_):
            self.repo_path = str(forge_root)
            self.tools_path = str(forge_root / "atomic-forge" / "tools")

        def clone(self):
            return None

        def cleanup(self):
            return None

    monkeypatch.setattr(assembler_main, "GithubRepoCloner", ForgeCloner)
