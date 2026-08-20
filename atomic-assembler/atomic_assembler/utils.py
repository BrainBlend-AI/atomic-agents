import json
import logging
import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path

import git
import yaml

from atomic_assembler.constants import DEFAULT_SOURCES, GITHUB_BRANCH, TOOLS_SUBFOLDER, ForgeSource, validate_source_url

SOURCES_CONFIG_PATH = Path.home() / ".atomic-assembler" / "sources.json"
_TERMINAL_ESCAPE_SEQUENCE = re.compile(r"\x1b\](?:[^\x07\x1b]|\x1b(?!\\))*(?:\x07|\x1b\\|$)|\x1b\[[0-?]*[ -/]*[@-~]")


def display_safe_text(value: str) -> str:
    without_escape_sequences = _TERMINAL_ESCAPE_SEQUENCE.sub("", value)
    return "".join(
        (
            " "
            if unicodedata.category(character).startswith("C") or unicodedata.category(character) in {"Zl", "Zp"}
            else character
        )
        for character in without_escape_sequences
    ).strip()


def _validated_index_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Forge index tool {field_name} must be a string")
    safe_value = display_safe_text(value)
    if not safe_value:
        raise ValueError(f"Forge index tool {field_name} must contain displayable text")
    return safe_value


def _validate_tool_symlink(tool_directory: Path, symlink: Path) -> None:
    link_target = Path(os.readlink(symlink))
    try:
        resolved_target = (symlink.parent / link_target).resolve()
        resolved_target.relative_to(tool_directory)
    except (OSError, RuntimeError, ValueError):
        relative_link = display_safe_text(str(symlink.relative_to(tool_directory)))
        raise ValueError(f"Tool contains an unsafe symlink: {relative_link}") from None
    if link_target.is_absolute():
        relative_link = display_safe_text(str(symlink.relative_to(tool_directory)))
        raise ValueError(f"Tool contains an unsafe symlink: {relative_link}")


def _validate_tool_symlinks(tool_path: str | Path) -> None:
    tool_directory = Path(tool_path).resolve()
    for directory, directory_names, file_names in os.walk(tool_directory, followlinks=False):
        for name in [*directory_names, *file_names]:
            candidate = Path(directory, name)
            if candidate.is_symlink():
                _validate_tool_symlink(tool_directory, candidate)


def source_config_path() -> Path:
    return SOURCES_CONFIG_PATH


def load_sources(config_path: Path | None = None) -> list[ForgeSource]:
    config_path = config_path or source_config_path()
    if not config_path.is_file():
        return list(DEFAULT_SOURCES)

    with config_path.open(encoding="utf-8") as file:
        configured_sources = json.load(file)
    if isinstance(configured_sources, dict):
        configured_sources = configured_sources.get("sources")
    if not isinstance(configured_sources, list):
        raise ValueError("sources.json must contain a list of sources")

    sources = []
    for source in configured_sources:
        if not isinstance(source, dict):
            raise ValueError("Each configured source must be an object")
        try:
            name = source["name"]
            url = source["url"]
        except KeyError as error:
            raise ValueError(f"Configured source is missing {error.args[0]}") from error
        branch = source.get("branch", GITHUB_BRANCH)
        tools_path = source.get("tools_path", TOOLS_SUBFOLDER)
        if not all(isinstance(value, str) and value for value in (name, url, branch, tools_path)):
            raise ValueError("Configured source fields must be non-empty strings")
        sources.append(ForgeSource(name, url, branch, tools_path))
    return sources


def save_sources(sources: list[ForgeSource], config_path: Path | None = None) -> None:
    config_path = config_path or source_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps([source.to_dict() for source in sources], indent=2) + "\n", encoding="utf-8")


class GithubRepoCloner:
    def __init__(self, base_url: str, branch: str = GITHUB_BRANCH, tools_path: str = TOOLS_SUBFOLDER):
        validate_source_url(base_url)
        self.repo_url = base_url
        self.branch = branch
        self.temp_dir = tempfile.mkdtemp()
        repo_name = Path(base_url.rstrip("/")).name.removesuffix(".git")
        self.repo_path = os.path.join(self.temp_dir, repo_name)
        self.tools_path = os.path.join(self.repo_path, tools_path)

    def clone(self):
        validate_source_url(self.repo_url)
        try:
            _ = git.Repo.clone_from(self.repo_url, self.repo_path, branch=self.branch)
            logging.info(f"Repository cloned to {self.repo_path} on branch {self.branch}")
        except git.GitCommandError as error:
            logging.error(f"Failed to clone repository: {error}")
            raise

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class AtomicToolManager:
    @staticmethod
    def read_tool_config(tool_path):
        config_path = os.path.join(tool_path, "config.yaml")
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return None
        except Exception as error:
            return f"Error reading config file: {error}"

    @staticmethod
    def get_atomic_tools(tools_path: str) -> list[dict]:
        tools = []
        for item in sorted(os.listdir(tools_path)):
            item_path = os.path.join(tools_path, item)
            if os.path.isdir(item_path):
                tools.append({"name": " ".join(word.capitalize() for word in item.split("_")), "path": item_path})
        return tools

    @staticmethod
    def get_forge_tools(repo_path: str, tools_path: str) -> list[dict]:
        index_path = Path(tools_path).parent / "index.json"
        if index_path.is_file():
            return AtomicToolManager.get_indexed_forge_tools(repo_path, tools_path)

        return [
            {
                "name": Path(tool["path"]).name.replace("_", "-"),
                "path": tool["path"],
                "description": AtomicToolManager.get_tool_description(tool["path"]),
            }
            for tool in AtomicToolManager.get_atomic_tools(tools_path)
        ]

    @staticmethod
    def get_indexed_forge_tools(repo_path: str, tools_path: str) -> list[dict]:
        index_path = Path(tools_path).parent / "index.json"
        if not index_path.is_file():
            raise FileNotFoundError(f"Missing forge index: {index_path}")
        with index_path.open(encoding="utf-8") as file:
            index = json.load(file)
        if not isinstance(index.get("tools"), list):
            raise ValueError(f"Forge index has no tools list: {index_path}")

        tools_directory = Path(tools_path).resolve()
        if not tools_directory.is_dir():
            raise NotADirectoryError(f"Configured tools directory is not a directory: {tools_path}")

        indexed_tools = []
        for tool in index["tools"]:
            tool_path = tool.get("path") if isinstance(tool, dict) else None
            if not isinstance(tool_path, str) or not tool_path:
                raise ValueError(f"Forge index tool path must be a non-empty string: {index_path}")

            safe_tool_path = display_safe_text(tool_path)
            relative_tool_path = Path(tool_path)
            if relative_tool_path.is_absolute() or ".." in relative_tool_path.parts:
                raise ValueError(f"Forge index tool path must stay within configured tools directory: {safe_tool_path}")

            resolved_tool_path = (index_path.parent / relative_tool_path).resolve()
            try:
                resolved_tool_path.relative_to(tools_directory)
            except ValueError as error:
                raise ValueError(
                    f"Forge index tool path must stay within configured tools directory: {safe_tool_path}"
                ) from error
            if not resolved_tool_path.is_dir():
                raise NotADirectoryError(f"Forge index tool path is not a directory: {safe_tool_path}")

            indexed_tools.append(
                {
                    "name": _validated_index_text(tool.get("name"), "name"),
                    "path": str(resolved_tool_path),
                    "description": _validated_index_text(tool.get("description", "No description available."), "description"),
                }
            )
        return indexed_tools

    @staticmethod
    def get_tool_description(tool_path: str) -> str:
        try:
            readme = Path(tool_path, "README.md").read_text(encoding="utf-8")
        except FileNotFoundError:
            return "No description available."

        for line in readme.splitlines():
            description = line.strip()
            if description and not description.startswith("#"):
                return description
        return "No description available."

    @staticmethod
    def copy_atomic_tool(tool_path, destination):
        logging.info(f"copy_atomic_tool called with tool_path: {tool_path}, destination: {destination}")
        try:
            local_tool_path = os.path.join(destination, os.path.basename(tool_path))
            return AtomicToolManager.copy_atomic_tool_to_destination(tool_path, local_tool_path)
        except Exception as error:
            logging.error(f"Error copying tool: {error}", exc_info=True)
            raise Exception(f"Error copying tool: {error}") from error

    @staticmethod
    def copy_atomic_tool_to_destination(tool_path, destination):
        logging.info(f"Copying tool from {tool_path} to {destination}")
        if not os.path.exists(tool_path):
            raise FileNotFoundError(f"Source path does not exist: {tool_path}")
        if os.path.exists(destination):
            raise FileExistsError(f"Destination already exists: {destination}")

        _validate_tool_symlinks(tool_path)
        shutil.copytree(tool_path, destination, symlinks=True, ignore=shutil.ignore_patterns(".coveragerc", "uv.lock"))
        logging.info(f"Tool successfully copied to {destination}")
        return str(destination)

    @staticmethod
    def load_env_file(file_path: Path) -> dict:
        env_vars = {}
        if file_path.exists():
            with open(file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars

    @staticmethod
    def read_readme(tool_path: str) -> str:
        readme_path = os.path.join(tool_path, "README.md")
        try:
            with open(readme_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return "README.md not found for this tool."
        except Exception as error:
            return f"Error reading README.md: {error}"
