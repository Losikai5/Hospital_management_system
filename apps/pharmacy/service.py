from django.utils import timezone
from .models import Prescription, PrescriptionStatus


def dispense_prescription(prescription):
    """
    Dispenses a prescription by:
    1. Checking sufficient stock
    2. Deducting stock
    3. Updating prescription status and dispensed_at
    """

    # Get the medicine linked to this prescription
    # We need it to check stock and deduct from it
    medicine = prescription.medicine

    # Gate 1: Check if there is enough stock
    # Issue 1 fix: use prescription and medicine instances
    # not the class names Medicine and Prescription
    if medicine.stock_quantity < prescription.quantity_prescribed:
        raise ValueError(
            f"Insufficient stock. "
            f"Required: {prescription.quantity_prescribed} "
            f"{medicine.get_unit_type_display()}, "
            f"Available: {medicine.stock_quantity}"
        )

    # Gate 2: Check if prescription is already dispensed
    # Reason: A pharmacist should not be able to dispense
    # the same prescription twice — that would double-deduct stock
    if prescription.status == PrescriptionStatus.DISPENSED:
        raise ValueError("This prescription has already been dispensed.")

    # Gate 3: Check if prescription is cancelled
    # Reason: A cancelled prescription should never be dispensed
    if prescription.status == PrescriptionStatus.CANCELLED:
        raise ValueError("Cannot dispense a cancelled prescription.")

    # All gates passed — now do the heavy lifting

    # Step 1: Deduct stock
    # Issue 2 fix: actually update the field and save it
    # -= is shorthand for medicine.stock_quantity = medicine.stock_quantity - prescription.quantity_prescribed
    medicine.stock_quantity -= prescription.quantity_prescribed
    medicine.save()  # persist to database — without this only memory changes

    # Step 2: Update prescription status
    # Issue 4 fix: these lines only run when gates pass
    prescription.status = PrescriptionStatus.DISPENSED

    # Step 3: Set dispensed_at to current time
    # Issue 3 fix: timezone.now() from django.utils not datetime.timezone.utc()
    # timezone.now() is timezone-aware — it knows about UTC and local time
    # datetime.timezone.utc is just a timezone object, not a time
    prescription.dispensed_at = timezone.now()

    # Step 4: Save the prescription
    # Issue 5 fix: must save both medicine AND prescription
    # Two separate save() calls because they are two separate database rows
    prescription.save()

    return prescription