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
        """
        Returns the database connection.
        """

        return db

    def patch_task(self):
        """
        Patches the task to run asynchronously.

        Returns:
            None
        """
        TaskBase = self.Task

        class ContextTask(TaskBase):
            abstract = True

            async def _run(self, *args, **kwargs):
                result = TaskBase.__call__(  # pylint: disable=assignment-from-no-return
                    self, *args, **kwargs
                )
                if isawaitable(result):
                    await result

            def __call__(self, *args, **kwargs):
                asyncio.get_event_loop().run_until_complete(self._run(*args, **kwargs))

        self.Task = (  # pylint: disable=invalid-name,assignment-from-no-return
            ContextTask
        )

    def init_app(self, app):
        """
        Initializes the app configuration.

        Args:
            app: The application object.

        Returns:
            None
        """

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
