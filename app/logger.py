import logging

import uvicorn


def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Get a logger with the specified name and log level.

    Args:
        name: The name of the logger.
        log_level: The log level for the logger.

    Returns:
        logging.Logger: The logger object.

    Raises:
        None
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = uvicorn.logging.DefaultFormatter(
        "%(levelprefix)s %(asctime)s - %(name)s - %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger
