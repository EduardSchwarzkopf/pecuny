from fastapi import APIRouter


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
