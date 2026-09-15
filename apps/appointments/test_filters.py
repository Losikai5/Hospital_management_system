from datetime import date, time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.doctors.models import DoctorProfile, Specialization
from apps.patients.models import PatientProfile
from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import Appointment, AppointmentStatus


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class AppointmentFilterTests(APITestCase):
    def setUp(self):
        staff_role = create_role(
            "APPOINTMENT_MANAGER",
            [
                "can_view_appointments",
                "can_view_all_appointments",
            ],
        )
        patient_role = create_role(
            "PATIENT",
            ["can_view_appointments"],
        )
        doctor_role = create_role("DOCTOR", [])
        self.staff = CustomUser.objects.create_user(
            email="staff@example.com",
            password="SafePassword!123",
            role=staff_role,
        )
        first_patient_user = CustomUser.objects.create_user(
            email="alice@example.com",
            password="SafePassword!123",
            role=patient_role,
            first_name="Alice",
        )
        second_patient_user = CustomUser.objects.create_user(
            email="bob@example.com",
            password="SafePassword!123",
            role=patient_role,
            first_name="Bob",
        )
        self.first_patient = PatientProfile.objects.create(
            user=first_patient_user
        )
        second_patient = PatientProfile.objects.create(
            user=second_patient_user
        )
        first_doctor_user = CustomUser.objects.create_user(
            email="pediatrician@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        second_doctor_user = CustomUser.objects.create_user(
            email="cardiologist@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        pediatrician = DoctorProfile.objects.create(
            user=first_doctor_user,
            license_number="FILTER-LIC-1",
            specialization=Specialization.PEDIATRICS,
        )
        cardiologist = DoctorProfile.objects.create(
            user=second_doctor_user,
            license_number="FILTER-LIC-2",
            specialization=Specialization.CARDIOLOGY,
        )
        self.first_appointment = Appointment.objects.create(
            doctor=pediatrician,
            patient=self.first_patient,
            appointment_date=date(2026, 8, 20),
            appointment_time=time(8, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        Appointment.objects.create(
            doctor=cardiologist,
            patient=second_patient,
            appointment_date=date(2026, 8, 21),
            appointment_time=time(9, 0),
            status=AppointmentStatus.PENDING,
        )

    def test_staff_can_combine_filters_and_ordering(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(
            reverse("appointment-list"),
            {
                "status": "confirmed",
                "date": "2026-08-20",
                "specialization": "pediatrics",
                "search": "alice",
                "ordering": "appointment_time",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [appointment["id"] for appointment in response.data],
            [self.first_appointment.pk],
        )

    def test_filtering_does_not_expand_patient_visibility(self):
        self.client.force_authenticate(self.first_patient.user)
        response = self.client.get(
            reverse("appointment-list"),
            {"search": "bob"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        response = self.client.get(
            reverse("appointment-list"),
            {"ordering": "doctor__user__email"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

