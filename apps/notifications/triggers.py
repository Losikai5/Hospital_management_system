from .dispatch import dispatch_task_after_commit
from .tasks import (
    process_low_stock_notification,
    send_appointment_cancellation,
)


def queue_appointment_cancellation(*, appointment, cancelled_by):
    dispatch_task_after_commit(
        send_appointment_cancellation,
        appointment.pk,
        cancelled_by.email,
    )


def queue_low_stock_check(*, medicine):
    dispatch_task_after_commit(
        process_low_stock_notification,
        medicine.pk,
    )

