from rest_framework import serializers
from .models import Prescription, Medicine


class MedicineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Medicine
        fields = [
            'name', 'stock_quantity', 'unit_cost',
            'unit_type', 'low_stock_threshold',
            'description', 'is_active'
        ]


class MedicineListSerializer(serializers.ModelSerializer):
    # Edit 1: Declared is_low_stock as a serializer field
    # Reason: is_low_stock is a @property on the Medicine model,
    # not a database column. DRF cannot auto-detect properties
    # so you must declare it explicitly. read_only=True because
    # it is computed — the client never sends this value.
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Medicine
        fields = [
            'id', 'name', 'stock_quantity', 'unit_cost',
            'unit_type', 'low_stock_threshold', 'description',
            'is_active', 'is_low_stock',  # Edit 2: Added is_low_stock to fields list
                                           # Reason: Declaring it above is not enough —
                                           # you must also include it in fields
                                           # otherwise DRF ignores it completely.
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Prescription
        fields = [
            'medical_record', 'medicine', 'dosage',
            'frequency', 'duration', 'quantity_prescribed',
            'status', 'prescribed_at', 'dispensed_at'
        ]
        read_only_fields = ['status', 'prescribed_at', 'dispensed_at']
        # Edit 3: status, prescribed_at, dispensed_at are read_only
        # Reason:
        # status — system sets this to PENDING automatically on creation
        # prescribed_at — auto_now_add sets this when record is created
        # dispensed_at — only set by the pharmacist at dispensing time
        # The doctor should not be able to manipulate any of these


class PrescriptionListSerializer(serializers.ModelSerializer):
    # Edit 4: Replaced raw ForeignKey fields with readable source fields
    # Reason: Without source, medicine and medical_record would just
    # show ID numbers like 1, 2, 3 — useless to anyone reading the API.
    # source traverses the relationship to get meaningful data.
    medicine_name   = serializers.CharField(
        source='medicine.name',
        read_only=True
    )
    medicine_unit   = serializers.CharField(
        source='medicine.get_unit_type_display',
        read_only=True
        # get_unit_type_display is Django's auto-generated method
        # that returns the human readable label from TextChoices
        # e.g. 'tablet' → 'Tablet(s)'
    )
    patient_email   = serializers.EmailField(
        source='medical_record.appointment.patient.user.email',
        read_only=True
        # Edit 5: Deep relationship traversal
        # Reason: Prescription → MedicalRecord → Appointment
        # → PatientProfile → CustomUser → email
        # Each dot is one bridge crossing — same concept as
        # double underscore in ORM queries but in Python object form
    )
    doctor_email    = serializers.EmailField(
        source='medical_record.appointment.doctor.user.email',
        read_only=True
    )

    class Meta:
        model  = Prescription
        fields = [
            'id',
            'medicine_name',
            'medicine_unit',
            'patient_email',
            'doctor_email',
            'dosage',
            'frequency',
            'duration',
            'quantity_prescribed',
            'status',
            'prescribed_at',
            'dispensed_at'
        ]
        read_only_fields = ['id', 'prescribed_at', 'dispensed_at']


class PrescriptionDispenseSerializer(serializers.Serializer):
    # Edit 6: Changed from ModelSerializer to plain Serializer
    # Reason: Dispensing is not standard CRUD — it is a process.
    # The pharmacist does not send any fields at all.
    # They just hit the endpoint and the service layer handles
    # everything — updating status, setting dispensed_at,
    # deducting stock. No input fields needed from the client.
    # Plain Serializer with no fields is the cleanest way to
    # represent "this endpoint triggers an action, not a data save."
    pass