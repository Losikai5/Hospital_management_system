from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.pharmacy.models import Medicine
from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import NotificationEvent
from .tasks import (
    process_low_stock_notification,
    send_appointment_cancellation,
    send_appointment_reminder,
)


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    NOTIFICATIONS_ENABLED=True,
)
class NotificationTaskTests(TestCase):
    def setUp(self):
        doctor_role = create_role("DOCTOR", [])
        patient_role = create_role("PATIENT", [])
        pharmacist_role = create_role(
            "PHARMACIST",
            ["can_dispense_prescriptions"],
        )
        doctor_user = CustomUser.objects.create_user(
            email="doctor@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        patient_user = CustomUser.objects.create_user(
            email="patient@example.com",
            password="SafePassword!123",
            role=patient_role,
        )
        CustomUser.objects.create_user(
            email="pharmacist@example.com",
            password="SafePassword!123",
            role=pharmacist_role,
        )
        self.doctor = DoctorProfile.objects.create(
            user=doctor_user,
            license_number="NOTIFY-LIC-1",
        )
        self.patient = PatientProfile.objects.create(user=patient_user)

        scheduled_for = timezone.localtime() + timedelta(hours=25)
        self.appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=scheduled_for.date(),
            appointment_time=scheduled_for.time().replace(microsecond=0),
            status=AppointmentStatus.CONFIRMED,
        )

    def test_appointment_reminder_is_idempotent(self):
        self.assertTrue(send_appointment_reminder(self.appointment.pk))
        self.assertFalse(send_appointment_reminder(self.appointment.pk))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(NotificationEvent.objects.count(), 1)

    def test_cancellation_notice_is_idempotent(self):
        self.appointment.status = AppointmentStatus.CANCELLED
        self.appointment.save(update_fields=["status", "updated_at"])

        self.assertTrue(
            send_appointment_cancellation(
                self.appointment.pk,
                "patient@example.com",
            )
        )
        self.assertFalse(
            send_appointment_cancellation(
                self.appointment.pk,
                "patient@example.com",
            )
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertCountEqual(
            mail.outbox[0].to,
            ["doctor@example.com", "patient@example.com"],
        )

    def test_low_stock_alert_resets_after_restock(self):
        medicine = Medicine.objects.create(
            name="Low medicine",
            stock_quantity=5,
            low_stock_threshold=10,
        )

        self.assertTrue(process_low_stock_notification(medicine.pk))
        self.assertFalse(process_low_stock_notification(medicine.pk))
        self.assertEqual(len(mail.outbox), 1)

        medicine.stock_quantity = 20
        medicine.save(update_fields=["stock_quantity", "updated_at"])
        self.assertFalse(process_low_stock_notification(medicine.pk))
        self.assertEqual(NotificationEvent.objects.count(), 0)

        medicine.stock_quantity = 4
        medicine.save(update_fields=["stock_quantity", "updated_at"])
        self.assertTrue(process_low_stock_notification(medicine.pk))
        self.assertEqual(len(mail.outbox), 2)

