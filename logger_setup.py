import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logger(
    log_file: str,
    max_log_size: int,
    backup_count: int,
    log_per_date: bool = False
):
    """
    Configure the 'GCloudTrayLogger' logger.

    If log_per_date is False, uses a size-based RotatingFileHandler:
      - Rolls over when the file reaches max_log_size, keeping backup_count files.

    If log_per_date is True, uses a TimedRotatingFileHandler:
      - Rolls over at midnight each day, keeping backup_count days of logs.

    Returns (logger, handler) so the caller can reconfigure later if needed.
    """
    logger = logging.getLogger("GCloudTrayLogger")
    logger.setLevel(logging.INFO)
    # Remove existing handlers
    for h in list(logger.handlers):
        logger.removeHandler(h)

    if log_per_date:
        handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            backupCount=backup_count,
            encoding="utf-8"
        )
    else:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding="utf-8"
        )

    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    )
    logger.addHandler(handler)
    return logger, handler
