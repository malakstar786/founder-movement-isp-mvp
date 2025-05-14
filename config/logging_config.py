import logging
import os
from datetime import datetime

def setup_logging(log_dir="logs", level=logging.INFO):
    """
    Set up logging configuration
    
    Parameters:
    - log_dir: Directory to store log files
    - level: Logging level (default: INFO)
    
    Returns:
    - Configured logger
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"founder_tracker_{timestamp}.log")
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Get the root logger
    logger = logging.getLogger()
    
    # Create a handler for file output
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # Create a handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    
    # Clear existing handlers and add our custom handlers
    logger.handlers = []
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name):
    """
    Get a named logger
    
    Parameters:
    - name: Logger name
    
    Returns:
    - Named logger
    """
    return logging.getLogger(name)

# Example logger usage:
# from config.logging_config import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message")
# logger.error("This is an error message")
