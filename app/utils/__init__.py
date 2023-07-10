from fastapi import APIRouter, Request
from typing import Optional


class Breadcrumb:
    def __init__(self, request: Request, title: str, url: Optional[str] = None):
        self.request = request
        self.title = title
        self.url = url

    def get(self):
        return {"title": self.title, "url": self.url}


class BreadcrumbBuilder:
    def __init__(self, request: Request):
        self.request = request
        self.breadcrumbs = []

    def add(self, title: str, url: Optional[str] = None):
        breadcrumb = Breadcrumb(self.request, title, url)
        self.breadcrumbs.append(breadcrumb.get())

    def build(self):
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
