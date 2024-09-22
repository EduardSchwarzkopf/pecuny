from abc import ABC
from logging import Logger
from typing import Optional

from app.exceptions.base_service_exception import BaseServiceException
from app.repository import Repository


class BaseService(ABC):
    def __init__(self, logger: Logger, repository: Optional[Repository] = None):
        if repository is None:
            repository = Repository()

        self.repository = repository
        self.logger = logger

    def log_and_raise_exception(self, exception: BaseServiceException):
        """
        Logs the given exception using the logger and then raises the exception.

        Args:
            exception (BaseServiceException): The exception to be logged and raised.

        Raises:
            BaseServiceException: The exception passed as an argument.

        Returns:
            None
        """

        self.logger.info(exception)
        raise exception

    @classmethod
    def get_instance(cls):
        """
        Returns an instance of the service class, suitable for use as a dependency in FastAPI.

        This method is designed to be used with FastAPI's dependency injection system. By declaring
        a dependency on this method in your route handlers, FastAPI will automatically create and
        inject an instance of the service class when the route is called. This allows for easy
        integration of service classes into your API endpoints, promoting a clean separation of
        concerns and facilitating testing by enabling the injection of mock objects.

        Usage:
            @app.get("/some-endpoint")
            async def some_endpoint(service: MyService = Depends(MyService.get_instance)):
                # Use the service instance here
                pass
        """
        return cls()
