from typing import List, Optional

from fastapi import APIRouter, Request


class Breadcrumb:
    def __init__(self, request: Request, title: str, url: Optional[str] = None):
        self.request = request
        self.title = title
        self.url = url

    def get(self):
        """Get the title and URL of the object.

        Args:
            self

        Returns:
            dict: A dictionary containing the title and URL.

        Raises:
            None
        """
        return {"title": self.title, "url": self.url}


class BreadcrumbBuilder:
    def __init__(self, request: Request):
        self.request = request
        self.breadcrumbs: list[Breadcrumb] = []

    def add(self, title: str, url: Optional[str] = None):
        """Add a breadcrumb to the list of breadcrumbs.

        Args:
            title: The title of the breadcrumb.
            url: Optional URL for the breadcrumb.

        Returns:
            None

        Raises:
            None
        """
        breadcrumb = Breadcrumb(self.request, title, url)
        self.breadcrumbs.append(breadcrumb.get())

    def build(self):
        """Build and return the list of breadcrumbs.

        Args:
            self

        Returns:
            list: The list of breadcrumbs.

        Raises:
            None
        """
        return self.breadcrumbs


class APIRouterExtended(APIRouter):
    def __init__(self, *args, **kwargs):
        # Ensure that a prefix always starts with "/api"
        if "prefix" in kwargs:
            kwargs["prefix"] = "/api" + kwargs["prefix"]

        # Ensure that "Api" is always included in tags
        if "tags" in kwargs and "Api" not in kwargs["tags"]:
            kwargs["tags"].append("Api")

        super().__init__(*args, **kwargs)


class PageRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        # Ensure that "Page" is always included in tags
        if "tags" in kwargs and "Page" not in kwargs["tags"]:
            kwargs["tags"].append("Page")

        super().__init__(*args, **kwargs)
