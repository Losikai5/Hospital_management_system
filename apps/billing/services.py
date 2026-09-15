from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.appointments.models import Appointment, AppointmentStatus
from apps.pharmacy.models import Prescription, PrescriptionStatus

from .models import Invoice, InvoiceItem, InvoicePayment, InvoiceStatus


def generate_invoice(*, appointment):
    try:
        with transaction.atomic():
            locked_appointment = (
                Appointment.objects
                .select_for_update()
                .select_related(
                    "doctor__user",
                    "patient__user",
                )
                .get(pk=appointment.pk)
            )

            if locked_appointment.status != AppointmentStatus.COMPLETED:
                raise ValueError(
                    "An invoice can only be generated for a completed appointment."
                )

            if Invoice.objects.filter(
                appointment=locked_appointment
            ).exists():
                raise ValueError(
                    "An invoice already exists for this appointment."
                )

            invoice = Invoice.objects.create(
                appointment=locked_appointment,
            )

            consultation_fee = Decimal(
                locked_appointment.doctor.consultation_fee
            )
            items = [
                InvoiceItem(
                    invoice=invoice,
                    description="Doctor consultation",
                    quantity=1,
                    unit_price=consultation_fee,
                    total=consultation_fee,
                )
            ]

            prescriptions = (
                Prescription.objects
                .filter(
                    medical_record__appointment=locked_appointment,
                    status=PrescriptionStatus.DISPENSED,
                )
                .select_related("medicine")
            )

            for prescription in prescriptions:
                quantity = prescription.quantity_prescribed
                unit_price = Decimal(prescription.medicine.unit_cost)
                items.append(
                    InvoiceItem(
                        invoice=invoice,
                        description=prescription.medicine.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=Decimal(quantity) * unit_price,
                    )
                )

            InvoiceItem.objects.bulk_create(items)
            invoice.total_amount = sum(
                (item.total for item in items),
                Decimal("0.00"),
            )
            invoice.save(update_fields=["total_amount", "updated_at"])
            return invoice
    except IntegrityError as error:
        raise ValueError(
            "An invoice already exists for this appointment."
        ) from error



def record_invoice_payment(
    *,
    invoice,
    amount,
    method,
    recorded_by,
    reference=None,
    notes="",
):
    try:
        with transaction.atomic():
            locked_invoice = (
                Invoice.objects
                .select_for_update()
                .get(pk=invoice.pk)
            )

            amount = Decimal(amount)
            if amount <= Decimal("0.00"):
                raise ValueError("Payment amount must be greater than zero.")

            balance = locked_invoice.balance
            if balance <= Decimal("0.00"):
                raise ValueError("This invoice has already been paid in full.")
            if amount > balance:
                raise ValueError(
                    f"Payment exceeds the outstanding balance of {balance:.2f}."
                )

            payment = InvoicePayment.objects.create(
                invoice=locked_invoice,
                amount=amount,
                method=method,
                reference=reference or None,
                notes=notes,
                recorded_by=recorded_by,
            )

            locked_invoice.amount_paid += amount
            locked_invoice.status = (
                InvoiceStatus.PAID
                if locked_invoice.amount_paid == locked_invoice.total_amount
                else InvoiceStatus.PARTIAL
            )
            locked_invoice.save(
                update_fields=["amount_paid", "status", "updated_at"]
            )
            return payment
    except IntegrityError as error:
        raise ValueError(
            "A payment with this reference already exists."
        ) from error