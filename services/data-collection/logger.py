import logging
import os
from datetime import datetime


def setup_logging(level=logging.INFO) -> logging.Logger:
    """Setup logging configuration to save logs in a 'loggings' directory."""

    # Create the 'loggings' directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loggings')
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
