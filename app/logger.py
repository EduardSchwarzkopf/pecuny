import logging
from fastapi.logger import logger as fastapi_logger


def get_logger():
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

    fastapi_logger.handlers = gunicorn_error_logger.handlers

    if __name__ != "__main__":
        fastapi_logger.setLevel(gunicorn_logger.level)
    else:
        fastapi_logger.setLevel(logging.DEBUG)

    return fastapi_logger
