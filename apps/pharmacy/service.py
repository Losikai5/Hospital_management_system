from django.db import transaction
from django.utils import timezone

from .models import Medicine, Prescription, PrescriptionStatus


@transaction.atomic
def dispense_prescription(prescription):
    prescription = (
        Prescription.objects
        .select_for_update()
        .select_related("medicine")
        .get(pk=prescription.pk)
    )
    medicine = Medicine.objects.select_for_update().get(
        pk=prescription.medicine_id
    )

    if prescription.status == PrescriptionStatus.DISPENSED:
        raise ValueError("This prescription has already been dispensed.")

    if prescription.status == PrescriptionStatus.CANCELLED:
        raise ValueError("Cannot dispense a cancelled prescription.")

    if medicine.stock_quantity < prescription.quantity_prescribed:
        raise ValueError(
            f"Insufficient stock. "
            f"Required: {prescription.quantity_prescribed} "
            f"{medicine.get_unit_type_display()}, "
            f"Available: {medicine.stock_quantity}"
        )

    medicine.stock_quantity -= prescription.quantity_prescribed
    medicine.save(update_fields=["stock_quantity", "updated_at"])

    prescription.status = PrescriptionStatus.DISPENSED
    prescription.dispensed_at = timezone.now()
    prescription.save(update_fields=["status", "dispensed_at"])

    from apps.notifications.triggers import queue_low_stock_check

    queue_low_stock_check(medicine=medicine)
    return prescription


@transaction.atomic
def cancel_prescription(*, prescription, cancelled_by):
    prescription = (
        Prescription.objects
        .select_for_update()
        .select_related(
            "medical_record__appointment__doctor__user",
        )
        .get(pk=prescription.pk)
    )

    prescribing_user_id = (
        prescription
        .medical_record
        .appointment
        .doctor
        .user_id
    )

    if (
        prescribing_user_id != cancelled_by.id
        and not cancelled_by.has_permission("can_view_all_prescriptions")
    ):
        raise ValueError(
            "You can only cancel prescriptions that you prescribed."
        )

    if prescription.status == PrescriptionStatus.DISPENSED:
        raise ValueError("A dispensed prescription cannot be cancelled.")

    if prescription.status == PrescriptionStatus.CANCELLED:
        raise ValueError("This prescription is already cancelled.")

    prescription.status = PrescriptionStatus.CANCELLED
    prescription.save(update_fields=["status"])
    return prescription
