import logging

from django.db import transaction


logger = logging.getLogger(__name__)


def dispatch_task_after_commit(task, *args, **kwargs):
    def enqueue():
        try:
            task.apply_async(
                args=args,
                kwargs=kwargs,
                retry=False,
            )
        except Exception:
            logger.exception(
                "Could not enqueue notification task %s.",
                task.name,
            )

    transaction.on_commit(enqueue)

