import logging
import os
from datetime import datetime


def setup_logging(level=logging.INFO) -> logging.Logger:
    """Setup logging configuration to save logs in a 'loggings' directory under a script-specific subfolder."""

    # Get the script filename without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # Create the 'loggings' directory and a subfolder named after the script
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loggings', script_name)
    os.makedirs(log_dir, exist_ok=True)

    # Create a log file with a timestamp
    log_filename = os.path.join(log_dir, f"log_data-collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level,
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    return logger
