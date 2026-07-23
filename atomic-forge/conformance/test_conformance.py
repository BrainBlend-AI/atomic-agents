from __future__ import annotations

import importlib.util
import inspect
import json
import re
import warnings
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin

import pytest

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig


TOOLS_DIR = Path(__file__).parents[1] / "tools"
INDEX_PATH = Path(__file__).parents[1] / "index.json"
REQUIRED_FILES = ("README.md", "pyproject.toml", "requirements.txt")

# TODO: Remove these exceptions after the stale requirements files are corrected.
KNOWN_DEPENDENCY_MIGRATION = {
    "searxng_search": ({"sympy"}, {"aiohttp"}),
    "tavily_search": ({"sympy"}, set()),
}


def tool_directories() -> list[Path]:
    return sorted(path for path in TOOLS_DIR.iterdir() if path.is_dir())


TOOLS = tool_directories()


def tool_id(path: Path) -> str:
    return path.name


def project_metadata(tool_dir: Path) -> dict[str, Any]:
    import tomllib

    return tomllib.loads(tool_dir.joinpath("pyproject.toml").read_text(encoding="utf-8"))["project"]


def requirement_name(entry: str) -> str:
    entry = entry.split("#", 1)[0].strip()
    match = re.match(r"(?:-e\s+)?([A-Za-z0-9][A-Za-z0-9_.-]*)", entry)
    if match is None:
        raise ValueError(f"Unsupported requirements.txt entry: {entry!r}")
    return normalize_name(match.group(1))


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def runtime_dependency_names(tool_dir: Path) -> set[str]:
    return {normalize_name(requirement_name(entry)) for entry in project_metadata(tool_dir)["dependencies"]}


def requirements_names(tool_dir: Path) -> set[str]:
    entries = tool_dir.joinpath("requirements.txt").read_text(encoding="utf-8").splitlines()
    return {requirement_name(entry) for entry in entries if entry.strip() and not entry.lstrip().startswith("#")}


@lru_cache(maxsize=None)
def load_tool_module(tool_name: str) -> ModuleType:
    tool_dir = TOOLS_DIR / tool_name
    module_path = tool_dir / "tool" / f"{tool_name}.py"
    if not module_path.is_file():
        raise AssertionError(f"{tool_name}: expected tool module at {module_path}")

    module_name = f"atomic_forge_conformance_{tool_name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"{tool_name}: could not create an import spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_classes(module: ModuleType, base_class: type) -> list[type]:
    return [
        value
        for value in vars(module).values()
        if inspect.isclass(value)
        and value.__module__ == module.__name__
        and value is not base_class
        and issubclass(value, base_class)
    ]


def main_tool_class(module: ModuleType, tool_name: str) -> type:
    classes = local_classes(module, BaseTool)
    assert len(classes) == 1, f"{tool_name}: expected one local BaseTool subclass, found {classes}"
    return classes[0]


def tool_generic_parameters(tool_class: type, tool_name: str) -> tuple[type, type]:
    generic_bases = [base for base in getattr(tool_class, "__orig_bases__", ()) if get_origin(base) is BaseTool]
    assert (
        len(generic_bases) == 1
    ), f"{tool_name}: {tool_class.__name__} must declare BaseTool[InputSchema, OutputSchema] explicitly"
    args = get_args(generic_bases[0])
    assert len(args) == 2, f"{tool_name}: {tool_class.__name__} must declare two BaseTool generic parameters"
    return args[0], args[1]


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_required_files(tool_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not tool_dir.joinpath(name).is_file()]
    missing.extend(name for name in ("tool", "tests") if not tool_dir.joinpath(name).is_dir())
    assert not missing, f"{tool_id(tool_dir)}: missing required paths: {', '.join(missing)}"


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_optional_files_warn(tool_dir: Path) -> None:
    missing = [name for name in ("uv.lock", ".coveragerc") if not tool_dir.joinpath(name).is_file()]
    for name in missing:
        warnings.warn(f"{tool_id(tool_dir)}: optional file is missing: {name}", UserWarning, stacklevel=1)


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_module_imports_cleanly(tool_dir: Path) -> None:
    try:
        load_tool_module(tool_id(tool_dir))
    except Exception as exc:
        pytest.fail(f"{tool_id(tool_dir)}: tool module failed to import cleanly: {exc}")


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_schemas_follow_contract(tool_dir: Path) -> None:
    name = tool_id(tool_dir)
    module = load_tool_module(name)
    tool_class = main_tool_class(module, name)
    input_schema, output_schema = tool_generic_parameters(tool_class, name)

    for label, schema in (("input", input_schema), ("output", output_schema)):
        assert inspect.isclass(schema) and issubclass(
            schema, BaseIOSchema
        ), f"{name}: {label} schema must subclass BaseIOSchema, got {schema!r}"
        assert inspect.getdoc(schema), f"{name}: {label} schema must have a non-empty docstring"


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_config_follows_contract(tool_dir: Path) -> None:
    name = tool_id(tool_dir)
    module = load_tool_module(name)
    configs = local_classes(module, BaseToolConfig)
    assert len(configs) == 1, f"{name}: expected one local BaseToolConfig subclass, found {configs}"


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_main_tool_declares_explicit_generics(tool_dir: Path) -> None:
    name = tool_id(tool_dir)
    module = load_tool_module(name)
    tool_class = main_tool_class(module, name)
    tool_generic_parameters(tool_class, name)


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_requirements_match_pyproject(tool_dir: Path) -> None:
    name = tool_id(tool_dir)
    requirements = requirements_names(tool_dir)
    dependencies = runtime_dependency_names(tool_dir)
    extra_requirements = requirements - dependencies
    missing_requirements = dependencies - requirements

    if extra_requirements or missing_requirements:
        expected = KNOWN_DEPENDENCY_MIGRATION.get(name)
        actual = (extra_requirements, missing_requirements)
        if expected == actual:
            warnings.warn(
                f"{name}: dependency declaration mismatch is a known migration warning; "
                f"requirements-only={sorted(extra_requirements)}, pyproject-only={sorted(missing_requirements)}",
                UserWarning,
                stacklevel=1,
            )
            return
        pytest.fail(
            f"{name}: requirements.txt and pyproject.toml dependencies differ by name; "
            f"requirements-only={sorted(extra_requirements)}, pyproject-only={sorted(missing_requirements)}"
        )


@pytest.mark.parametrize("tool_dir", TOOLS, ids=tool_id)
def test_index_entry_matches_project(tool_dir: Path) -> None:
    name = tool_id(tool_dir)
    metadata = project_metadata(tool_dir)
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    matches = [entry for entry in index["tools"] if entry.get("path") == f"tools/{name}"]
    assert len(matches) == 1, f"{name}: expected one index entry at tools/{name}, found {len(matches)}"

    entry = matches[0]
    assert (
        entry.get("name") == metadata["name"]
    ), f"{name}: index name {entry.get('name')!r} does not match pyproject name {metadata['name']!r}"
    assert (
        entry.get("version") == metadata["version"]
    ), f"{name}: index version {entry.get('version')!r} does not match pyproject version {metadata['version']!r}"
