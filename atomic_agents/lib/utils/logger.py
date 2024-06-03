import logging
from rich.logging import RichHandler

# Step 1: Define a new logging level
VERBOSE = 25
logging.addLevelName(VERBOSE, "VERBOSE")

# Step 2: Add a method to the logging module
def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE):
        kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1
        self._log(VERBOSE, message, args, **kwargs)

logging.Logger.verbose = verbose

# Configure logging
logging.basicConfig(level=VERBOSE, handlers=[RichHandler(level=VERBOSE)])
logger = logging.getLogger("rich")