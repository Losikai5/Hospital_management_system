from decimal import Decimal

from rest_framework import serializers

from apps.appointments.models import Appointment
from apps.utilities.models import BaseModelSerializer

from .models import Invoice, InvoiceItem, InvoicePayment, PaymentMethod
from .services import generate_invoice, record_invoice_payment


class InvoiceItemSerializer(BaseModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "total",
        ]
        read_only_fields = fields


class InvoicePaymentSerializer(BaseModelSerializer):
    recorded_by_email = serializers.EmailField(
        source="recorded_by.email",
        read_only=True,
    )

    class Meta:
        model = InvoicePayment
        fields = [
            "id",
            "amount",
            "method",
            "reference",
            "notes",
            "recorded_by_email",
            "paid_at",
        ]
        read_only_fields = fields


class InvoicePaymentCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    method = serializers.ChoiceField(choices=PaymentMethod.choices)
    reference = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_reference(self, value):
        return value.strip() or None

    def create(self, validated_data):
        try:
            return record_invoice_payment(
                invoice=self.context["invoice"],
                recorded_by=self.context["request"].user,
                **validated_data,
            )
        except ValueError as error:
            raise serializers.ValidationError(
                {"payment": str(error)}
            ) from error

class InvoiceSerializer(BaseModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = InvoicePaymentSerializer(many=True, read_only=True)
    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    patient_email = serializers.EmailField(
        source="appointment.patient.user.email",
        read_only=True,
    )
    doctor_email = serializers.EmailField(
        source="appointment.doctor.user.email",
        read_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "appointment",
            "patient_email",
            "doctor_email",
            "total_amount",
            "amount_paid",
            "balance",
            "status",
            "items",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvoiceCreateSerializer(serializers.Serializer):
    appointment = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
    )

    def create(self, validated_data):
        try:
            return generate_invoice(
                appointment=validated_data["appointment"],
            )
        except ValueError as error:
            raise serializers.ValidationError(
                {"appointment": str(error)}
            ) from error

