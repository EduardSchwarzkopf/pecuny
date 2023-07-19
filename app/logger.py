import logging
from logging.config import dictConfig


def get_logger(
    name: str = "pecuny",
    log_level: str = "DEBUG",
    log_format: str = "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
) -> logging.Logger:
    # Set up logging configuration
    log_config = {
        "version": 1,
        "formatters": {
            "basic": {
                "()": "uvicorn.logging.DefaultFormatter",
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "formatter": "basic",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "level": log_level,
            }
        },
        "loggers": {
            name: {
                "handlers": ["console"],
                "level": log_level,
            }
        },
    }

    dictConfig(log_config)

    return logging.getLogger(name)
