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
    parser = argparse.ArgumentParser(description="Atomic Assembler")
    parser.add_argument("--enable-logging", action="store_true", help="Enable logging")
    args = parser.parse_args()

    setup_logging(args.enable_logging)

    app = AtomicAssembler()
    app.run()

if __name__ == "__main__":
    main()
