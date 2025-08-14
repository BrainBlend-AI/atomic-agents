import logging
import argparse
from importlib.metadata import version, PackageNotFoundError
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
    try:
        pkg_version = version("atomic-agents")
    except PackageNotFoundError:
        pkg_version = "unknown"

    parser = argparse.ArgumentParser(
        description="Atomic Assembler", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=f"Version: {pkg_version}"
    )
    parser.add_argument("--enable-logging", action="store_true", help="Enable logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {pkg_version}")
    args = parser.parse_args()

    setup_logging(args.enable_logging)

    app = AtomicAssembler()
    app.run()


if __name__ == "__main__":
    main()
