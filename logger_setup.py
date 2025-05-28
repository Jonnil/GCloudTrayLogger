import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_file: str, max_log_size: int, backup_count: int):
    """
    Configure the 'GCloudTrayLogger' logger with a rotating file handler.
    Returns (logger, handler) so the caller can reconfigure later if needed.
    """
    logger = logging.getLogger("GCloudTrayLogger")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        log_file, maxBytes=max_log_size, backupCount=backup_count
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    )
    logger.addHandler(handler)
    return logger, handler
