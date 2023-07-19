import logging


def get_logger(
    name: str = "my-api",
    log_level: str = "DEBUG",
    log_format: str = "%(levelprefix)s %(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
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

    # Apply logging configuration
    logging.config.dictConfig(log_config)

    # Return configured logger
    return logging.getLogger(name)
