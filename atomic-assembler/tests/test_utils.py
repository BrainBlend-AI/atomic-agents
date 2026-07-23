from pathlib import Path

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
