# pyright: reportInvalidTypeForm=false
"""
Universal launcher for the MCP examples.
  stdio_async  - runs the async STDIO client
  fastapi      - serves the FastAPI HTTP API
  http_stream  - HTTP-stream CLI client
  sse          - SSE CLI client
  stdio        - blocking STDIO CLI client
"""

import argparse
import asyncio
import importlib
import sys

# Optional import; only used for the FastAPI target
try:
    import uvicorn  # noqa: WPS433 – runtime import is deliberate
except ImportError:  # pragma: no cover
    uvicorn = None


def _run_target(module_name: str, func_name: str | None = "main", *, is_async: bool = False) -> None:
    """
    Import `module_name` and execute `func_name`.

    Args:
        module_name: Python module containing the entry point.
        func_name:   Callable inside that module to execute (skip for FastAPI).
        is_async:    Whether the callable is an async coroutine.
    """
    module = importlib.import_module(module_name)

    if func_name is None:  # fastapi path – start uvicorn directly
        if uvicorn is None:  # pragma: no cover
            sys.exit("uvicorn is not installed - unable to start FastAPI server.")
        # `module_name:app` tells uvicorn where the FastAPI instance lives.
        uvicorn.run(f"{module_name}:app", host="0.0.0.0", port=8000)
        return

    entry = getattr(module, func_name)
    if is_async:
        asyncio.run(entry())
    else:
        entry()


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Example Launcher")
    parser.add_argument(
        "--client",
        default="stdio",
        choices=[
            "stdio",
            "stdio_async",
            "sse",
            "http_stream",
            "fastapi",
        ],
        help="Which client implementation to start",
    )
    args = parser.parse_args()

    # Map the `--client` value to (module, callable, needs_asyncio)
    dispatch_table: dict[str, tuple[str, str | None, bool]] = {
        "stdio": ("example_client.main_stdio", "main", False),
        "stdio_async": ("example_client.main_stdio_async", "main", True),
        "sse": ("example_client.main_sse", "main", False),
        "http_stream": ("example_client.main_http", "main", False),
        # For FastAPI we hand control to uvicorn – func_name=None signals that.
        "fastapi": ("example_client.main_fastapi", None, False),
    }

    try:
        module_name, func_name, is_async = dispatch_table[args.client]
        _run_target(module_name, func_name, is_async=is_async)
    except KeyError:
        sys.exit(f"Unknown client: {args.client}")
    except (ImportError, AttributeError) as exc:
        sys.exit(f"Failed to load '{args.client}': {exc}")


if __name__ == "__main__":
    main()
