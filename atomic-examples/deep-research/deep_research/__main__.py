"""Package entry point — ``python -m deep_research``.

With args: one-shot pipeline — ``python -m deep_research "your question"``.
Without args: drops into the chat loop.

The real orchestrator lives in ``main.py``; this file is just the Python
convention that makes the package directly runnable.
"""

import sys

from deep_research.main import chat_loop, run

if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        run(" ".join(args))
    else:
        chat_loop()
