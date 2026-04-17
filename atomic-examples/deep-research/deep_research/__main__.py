"""Package entry point — so ``python -m deep_research "question"`` works.

The real orchestrator lives in ``main.py``; this file is just the Python
convention that makes the package directly runnable.
"""

import sys

from deep_research.main import run

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print('Usage: python -m deep_research "your question"', file=sys.stderr)
        sys.exit(1)
    run(" ".join(args))
