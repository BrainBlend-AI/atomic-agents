# Only expose the subpackages; no direct re‑exports.
from . import mcp  # ensure pkg_resources-style discovery

__all__ = ["mcp"]
