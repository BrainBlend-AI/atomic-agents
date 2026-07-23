import json
import logging
import os
import shutil
import tempfile

import git
import yaml
from pathlib import Path
from atomic_assembler.constants import GITHUB_BRANCH, TOOLS_SUBFOLDER


class GithubRepoCloner:
    def __init__(self, base_url: str, branch: str = GITHUB_BRANCH):
        self.repo_url = base_url
        self.branch = branch
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, os.path.basename(base_url).replace(".git", ""))
        self.tools_path = os.path.join(self.repo_path, TOOLS_SUBFOLDER)

    def clone(self):
        try:
            _ = git.Repo.clone_from(self.repo_url, self.repo_path, branch=self.branch)
            logging.info(f"Repository cloned to {self.repo_path} on branch {self.branch}")
        except git.GitCommandError as e:
            logging.error(f"Failed to clone repository: {e}")
            raise

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class AtomicToolManager:
    @staticmethod
    def read_tool_config(tool_path):
        config_path = os.path.join(tool_path, "config.yaml")
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            return f"Error reading config file: {e}"

    @staticmethod
    def get_atomic_tools(tools_path: str) -> list[dict]:
        tools = []
        for item in sorted(os.listdir(tools_path)):
            item_path = os.path.join(tools_path, item)
            if os.path.isdir(item_path):
                tools.append(
                    {
                        "name": " ".join(word.capitalize() for word in item.split("_")),
                        "path": item_path,
                    }
                )
        return tools

    @staticmethod
    def get_forge_tools(repo_path: str, tools_path: str) -> list[dict]:
        index_path = Path(repo_path) / "atomic-forge" / "index.json"
        if index_path.is_file():
            with index_path.open(encoding="utf-8") as file:
                index = json.load(file)
            return [
                {
                    "name": tool["name"],
                    "path": str(Path(repo_path) / "atomic-forge" / tool["path"]),
                    "description": tool.get("description", "No description available."),
                }
                for tool in index["tools"]
            ]

        return [
            {
                "name": Path(tool["path"]).name.replace("_", "-"),
                "path": tool["path"],
                "description": AtomicToolManager.get_tool_description(tool["path"]),
            }
            for tool in AtomicToolManager.get_atomic_tools(tools_path)
        ]

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
        except Exception as e:
            logging.error(f"Error copying tool: {str(e)}", exc_info=True)
            raise Exception(f"Error copying tool: {e}")

    @staticmethod
    def copy_atomic_tool_to_destination(tool_path, destination):
        logging.info(f"Copying tool from {tool_path} to {destination}")
        if not os.path.exists(tool_path):
            raise FileNotFoundError(f"Source path does not exist: {tool_path}")
        if os.path.exists(destination):
            raise FileExistsError(f"Destination already exists: {destination}")

        shutil.copytree(
            tool_path,
            destination,
            ignore=shutil.ignore_patterns(".coveragerc", "uv.lock"),
        )
        logging.info(f"Tool successfully copied to {destination}")
        return str(destination)

    @staticmethod
    def load_env_file(file_path: Path) -> dict:
        """Load environment variables from a .env file."""
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
        """
        Read the README.md file from the tool directory.

        Args:
            tool_path (str): The path to the tool directory.

        Returns:
            str: The contents of the README.md file, or an error message if not found.
        """
        readme_path = os.path.join(tool_path, "README.md")
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "README.md not found for this tool."
        except Exception as e:
            return f"Error reading README.md: {str(e)}"
