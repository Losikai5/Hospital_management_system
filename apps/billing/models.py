from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class InvoiceStatus(models.TextChoices):
    UNPAID = "UNPAID", _("Unpaid")
    PARTIAL = "PARTIAL", _("Partially paid")
    PAID = "PAID", _("Paid")


class PaymentMethod(models.TextChoices):
    CASH = "CASH", _("Cash")
    CARD = "CARD", _("Card")
    MOBILE_MONEY = "MOBILE_MONEY", _("Mobile money")
    INSURANCE = "INSURANCE", _("Insurance")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank transfer")


class Invoice(models.Model):
    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(
        max_length=10,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.UNPAID,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return f"Invoice #{self.pk} for appointment #{self.appointment_id}"

    @property
    def balance(self):
        return self.total_amount - self.amount_paid


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Invoice item")
        verbose_name_plural = _("Invoice items")

    def save(self, *args, **kwargs):
        self.total = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description



class InvoicePayment(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    reference = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_invoice_payments",
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["paid_at", "id"]
        verbose_name = _("Invoice payment")
        verbose_name_plural = _("Invoice payments")

    def __str__(self):
        return f"Payment #{self.pk} for invoice #{self.invoice_id}"