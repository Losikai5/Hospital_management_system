from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class UnitType(models.TextChoices):
    # Edit 1: Changed unit_type from plain CharField to TextChoices
    # Reason: Consistent with the rest of the project.
    # AppointmentStatus all use TextChoices. This prevents invalid
    # unit types from being saved and gives you readable labels
    # in the admin panel.
    TABLET  = 'tablet',  _('Tablet(s)')
    CAPSULE = 'capsule', _('Capsule(s)')
    ML      = 'ml',      _('Milliliters (ml)')
    MG      = 'mg',      _('Milligrams (mg)')
    G       = 'g',       _('Grams (g)')
    VIAL    = 'vial',    _('Vial(s)')
    BOTTLE  = 'bottle',  _('Bottle(s)')


class Medicine(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,          # Edit 2: Added unique=True
                              # Reason: Two medicines with the same name
                              # would cause confusion when dispensing.
                              # unique=True prevents duplicate entries.
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,            # Edit 3: Changed IntegerField to PositiveIntegerField
                              # Reason: Stock can never be negative.
                              # PositiveIntegerField enforces this at
                              # the database level — you cannot accidentally
                              # save -10 tablets.
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,     # Edit 4: Added required DecimalField arguments
                              # Reason: DecimalField requires both max_digits
                              # and decimal_places. Without them Django raises
                              # a TypeError during makemigrations.
                              # Also DecimalField not FloatField — money
                              # must always be stored exactly.
        validators=[MinValueValidator(Decimal("0.00"))],
                              # Edit 5: Added MinValueValidator
                              # Reason: A medicine cannot have a negative price.
                              # This validator enforces that at the
                              # serializer level before saving.
        default=Decimal("0.00")
    )
    unit_type = models.CharField(
        max_length=10,
        choices=UnitType.choices,  # Edit 6: Connected to TextChoices
        default=UnitType.TABLET
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,           # Edit 7: Added default=10
                              # Reason: Every medicine needs a threshold
                              # to trigger low stock alerts. Without a
                              # default, every new medicine entry would
                              # require manually setting this field.
        validators=[MinValueValidator(1)]
    )
    description = models.TextField(
        blank=True, null=True # Edit 8: Added description field
                              # Reason: Pharmacists need to record
                              # usage instructions, side effects, and
                              # contraindications for each medicine.
    )
    is_active = models.BooleanField(
        default=True          # Edit 9: Added is_active field
                              # Reason: When a medicine is discontinued
                              # you should never delete it — old
                              # prescriptions still reference it.
                              # Deactivating is safer than deleting.
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = _('Medicine')
        verbose_name_plural = _('Medicines')
        ordering            = ['name']  # Edit 10: Added ordering
                                        # Reason: Medicines should appear
                                        # alphabetically in the admin
                                        # and API responses for easy lookup.

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.get_unit_type_display()} remaining)"

    @property
    def is_low_stock(self):
        # Edit 11: Added is_low_stock property
        # Reason: A clean reusable way to check stock level
        # anywhere in the codebase — views, serializers,
        # Celery tasks — without repeating the comparison logic.
        return self.stock_quantity <= self.low_stock_threshold


class PrescriptionStatus(models.TextChoices):
    # Edit 12: Moved status choices to TextChoices class
    # Reason: Consistent with the rest of the project.
    # Lets you reference statuses by name anywhere:
    # PrescriptionStatus.PENDING instead of raw string 'pending'
    PENDING   = 'PENDING',   _('Pending Fulfillment')
    DISPENSED = 'DISPENSED', _('Dispensed')
    CANCELLED = 'CANCELLED', _('Cancelled')


class Prescription(models.Model):
    medical_record = models.ForeignKey(
        'medical_records.MedicalRecord',
        # Edit 13: Added correct app label
        # Reason: Prescription is in the pharmacy app but
        # MedicalRecord is in medical_records app. Without
        # the app label Django looks in the wrong app and crashes.
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        # Edit 14: PROTECT not CASCADE
        # Reason: If a medicine is deleted, its prescription
        # history should not be wiped. PROTECT blocks deletion
        # of a medicine that has prescriptions referencing it.
        related_name='prescriptions'
    )
    dosage              = models.CharField(max_length=255)
    frequency           = models.CharField(max_length=255)
    duration            = models.CharField(max_length=100)
    quantity_prescribed = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=15,
        choices=PrescriptionStatus.choices,
        default=PrescriptionStatus.PENDING
    )
    prescribed_at = models.DateTimeField(auto_now_add=True)
    dispensed_at  = models.DateTimeField(
        null=True,
        blank=True,
        # Edit 15: No auto_now=True — intentional
        # Reason: auto_now=True updates every time the record
        # is saved. dispensed_at should only be set ONCE —
        # at the exact moment of dispensing. We set it manually
        # in the service layer: prescription.dispensed_at = timezone.now()
    )

    class Meta:
        verbose_name        = _('Prescription')
        verbose_name_plural = _('Prescriptions')
        ordering            = ['-prescribed_at']

    def __str__(self):
        return f"Prescription #{self.id} — {self.medicine.name} for Record #{self.medical_record.id}"