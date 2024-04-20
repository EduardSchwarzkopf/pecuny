from typing import Optional

from app.repository import Repository


class BaseService:

    def __init__(self, repository: Optional[Repository] = None):
        if repository is None:
            repository = Repository()

        self.repository = repository

    # classmethod to return a new instance of the self
    @classmethod
    def new(cls, repository: Optional[Repository] = None):
        return cls(repository)
