#!/usr/bin/env python3
"""
Sync version from pyproject.toml to docs/conf.py
"""

import re
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
DOCS_CONF_FILE = PROJECT_ROOT / "docs" / "conf.py"

def get_version_from_pyproject():
    """Extract version from pyproject.toml using regex"""
    with open(PYPROJECT_FILE, 'r') as f:
        content = f.read()

    # Look for version line in [project] section
    match = re.search(r'^version = ["\'](.*?)["\']', content, re.MULTILINE)
    if match:
        return match.group(1)
    else:
        raise ValueError("Could not find version in pyproject.toml")

def update_docs_conf(version):
    """Update version in docs/conf.py"""
    with open(DOCS_CONF_FILE, 'r') as f:
        content = f.read()
    
    # Replace version line
    content = re.sub(
        r'^version = "[^"]*"$',
        f'version = "{version}"',
        content,
        flags=re.MULTILINE
    )
    
    # Replace release line
    content = re.sub(
        r'^release = "[^"]*"$',
        f'release = "{version}"',
        content,
        flags=re.MULTILINE
    )
    
    with open(DOCS_CONF_FILE, 'w') as f:
        f.write(content)
    
    print(f"Updated docs/conf.py to version {version}")

def main():
    """Main function"""
    try:
        version = get_version_from_pyproject()
        print(f"Found version {version} in pyproject.toml")
        update_docs_conf(version)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()