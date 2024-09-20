import logging
import sys
import shutil
import os
import argparse

from atomic_assembler.app import AtomicAssembler

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def reset_tools_folder():
    """
    Remove the 'tools' folder if it exists, then create an empty 'tools' folder.
    """
    tools_path = os.path.join(os.getcwd(), "tools")

    if os.path.exists(tools_path):
        try:
            shutil.rmtree(tools_path)
            logger.info("Successfully removed the existing 'tools' folder.")
        except Exception as e:
            logger.error(f"Failed to remove the 'tools' folder: {str(e)}")
            return

    try:
        os.mkdir(tools_path)
        logger.info("Successfully created an empty 'tools' folder.")
    except Exception as e:
        logger.error(f"Failed to create the 'tools' folder: {str(e)}")


def main():
    """Main function to run the CLI tool."""
    parser = argparse.ArgumentParser(description="Atomic Assembler CLI Tool")
    parser.add_argument(
        "--devmode", action="store_true", help="Enable development mode"
    )
    args = parser.parse_args()

    if args.devmode:
        reset_tools_folder()
    app = AtomicAssembler()
    app.run()


if __name__ == "__main__":
    main()
