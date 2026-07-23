import json
import tomllib
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = FORGE_ROOT / "tools"
INDEX_PATH = FORGE_ROOT / "index.json"


def first_readme_paragraph(readme_path: Path) -> str:
    paragraphs: list[str] = []
    lines: list[str] = []

    for line in readme_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            lines.append(line.strip())
        elif lines:
            paragraphs.append(" ".join(lines))
            lines = []

    if lines:
        paragraphs.append(" ".join(lines))

    return paragraphs[0] if paragraphs else ""


def tool_record(tool_path: Path) -> dict[str, object]:
    with (tool_path / "pyproject.toml").open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]

    description = project.get("description", "").strip()
    if not description:
        description = first_readme_paragraph(tool_path / "README.md")

    return {
        "name": project["name"],
        "path": tool_path.relative_to(FORGE_ROOT).as_posix(),
        "description": description,
        "version": project["version"],
        "dependencies": project.get("dependencies", []),
    }


def build_index() -> dict[str, object]:
    tools = sorted(
        (tool_record(tool_path) for tool_path in TOOLS_ROOT.iterdir() if (tool_path / "pyproject.toml").is_file()),
        key=lambda tool: str(tool["name"]),
    )
    return {"schema": 1, "name": "atomic-forge", "tools": tools}


def main() -> None:
    INDEX_PATH.write_text(json.dumps(build_index(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
