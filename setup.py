from setuptools import setup, find_packages

# Read the version from pyproject.toml
with open("pyproject.toml", "r") as f:
    for line in f:
        if line.startswith("version = "):
            version = line.split("=")[1].strip().strip('"')
            break

setup(
    name="atomic-agents",
    version=version,
    packages=find_packages(where="atomic-agents") + find_packages(where="atomic-assembler"),
    package_dir={"atomic_agents": "atomic-agents/atomic_agents", "atomic_assembler": "atomic-assembler/atomic_assembler"},
    include_package_data=True,
)
