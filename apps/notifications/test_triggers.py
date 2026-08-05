from datetime import date, time
from unittest.mock import patch

from django.test import TestCase

from apps.appointments.models import Appointment, AppointmentStatus
from apps.appointments.services import cancel_appointment
from apps.doctors.models import DoctorProfile
from apps.medical_records.models import MedicalRecord
from apps.patients.models import PatientProfile
from apps.pharmacy.models import Medicine, Prescription
from apps.pharmacy.service import dispense_prescription
from apps.users.models import CustomUser, Role


class NotificationTriggerIntegrationTests(TestCase):
    def setUp(self):
        doctor_role = Role.objects.create(code="DOCTOR", name="Doctor")
        patient_role = Role.objects.create(code="PATIENT", name="Patient")
        pharmacist_role = Role.objects.create(
            code="PHARMACIST",
            name="Pharmacist",
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doctor-trigger@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        self.patient_user = CustomUser.objects.create_user(
            email="patient-trigger@example.com",
            password="SafePassword!123",
            role=patient_role,
        )
        self.pharmacist_user = CustomUser.objects.create_user(
            email="pharmacist-trigger@example.com",
            password="SafePassword!123",
            role=pharmacist_role,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            license_number="TRIGGER-LIC-1",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date(2026, 8, 20),
            appointment_time=time(8, 0),
            status=AppointmentStatus.CONFIRMED,
        )

    @patch(
        "apps.notifications.triggers."
        "send_appointment_cancellation.apply_async"
    )
    def test_cancellation_enqueues_notice_after_commit(self, apply_async):
        with self.captureOnCommitCallbacks(execute=True):
            cancel_appointment(
                self.appointment,
                cancelled_by=self.patient_user,
            )

        apply_async.assert_called_once_with(
            args=(
                self.appointment.pk,
                self.patient_user.email,
            ),
            kwargs={},
            retry=False,
        )

    @patch(
        "apps.notifications.triggers."
        "process_low_stock_notification.apply_async"
    )
    def test_dispensing_enqueues_stock_check_after_commit(self, apply_async):
        self.appointment.status = AppointmentStatus.COMPLETED
        self.appointment.save(update_fields=["status", "updated_at"])
        medical_record = MedicalRecord.objects.create(
            appointment=self.appointment,
            diagnosis="Diagnosis",
        )
        medicine = Medicine.objects.create(
            name="Trigger medicine",
            stock_quantity=5,
            low_stock_threshold=3,
        )
        prescription = Prescription.objects.create(
            medical_record=medical_record,
            medicine=medicine,
            dosage="One tablet",
            frequency="Daily",
            duration="Two days",
            quantity_prescribed=2,
        )

        with self.captureOnCommitCallbacks(execute=True):
            dispense_prescription(prescription)

        apply_async.assert_called_once_with(
            args=(medicine.pk,),
            kwargs={},
            retry=False,
        )

