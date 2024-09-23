import logging
import sys
import argparse
from atomic_assembler.constants import GITHUB_BASE_URL
from atomic_assembler.app import AtomicAssembler

def setup_logging(enable_logging: bool):
    if enable_logging:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            handlers=[
                logging.FileHandler("atomic_assembler.log"),
            ],
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)

logger = logging.getLogger(__name__)

def main():
    global GITHUB_BASE_URL

    parser = argparse.ArgumentParser(description="Atomic Assembler")
    parser.add_argument("--github-url", type=str, default=GITHUB_BASE_URL, help="GitHub repository URL")
    parser.add_argument("--branch", type=str, default="feature/monorepo", help="Branch to checkout")
    parser.add_argument("--enable-logging", action="store_true", help="Enable logging")
    args = parser.parse_args()

    setup_logging(args.enable_logging)

    GITHUB_BASE_URL = args.github_url
    branch = args.branch

    app = AtomicAssembler(branch=branch)
    app.run()

if __name__ == "__main__":
    main()
