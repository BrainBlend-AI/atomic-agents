from setuptools import setup, find_packages

setup(
    name="atomic-agents",
    version="1.0.0",
    packages=find_packages(where="atomic-agents") + find_packages(where="atomic-assembler"),
    package_dir={"": "atomic-agents", "": "atomic-assembler"},
    include_package_data=True,
)
