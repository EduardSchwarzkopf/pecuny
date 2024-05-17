import asyncio
from inspect import isawaitable

from celery import Celery

from app.config import settings
from app.database import db


class AsyncCelery(Celery):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.patch_task()

        if "app" in kwargs:
            self.init_app(kwargs["app"])

    def get_db(self):
        return db

    def patch_task(self):
        TaskBase = self.Task

        class ContextTask(TaskBase):
            abstract = True

            async def _run(self, *args, **kwargs):
                result = TaskBase.__call__(self, *args, **kwargs)
                if isawaitable(result):
                    await result

            def __call__(self, *args, **kwargs):
                asyncio.get_event_loop().run_until_complete(self._run(*args, **kwargs))

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app

        conf = {
            key[7:].lower(): app.config[key]
            for key in app.config.keys()
            if key[:7] == self.namespace
        }
        if (
            "broker_transport_options" not in conf
            and conf.get("broker_url", "")[:4] == "sqs:"
        ):
            conf["broker_transport_options"] = {"region": "eu-west-1"}

        self.config_from_object(conf)


celery = AsyncCelery(
    __name__,
    include=["app.tasks"],
)

celery.config_from_object(settings, namespace="celery")
