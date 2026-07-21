import logging
from config import LOG_DIR
from datetime import datetime

# Configure logging to write to processing.log
log_filename = LOG_DIR / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    filename=str(log_filename),
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    return logging.getLogger(name)
