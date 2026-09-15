from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import (
    CustomUser,
    Permission,
    Role,
    RolePermission,
)

from .models import DoctorProfile, DoctorSchedule, Specialization


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(
            role=role,
            permission=permission,
        )
    return role


class DoctorApiTests(APITestCase):
    def setUp(self):
        self.doctor_role = create_role(
            "DOCTOR",
            [
                "can_view_doctors",
                "can_manage_doctor_schedules",
            ],
        )
        self.manager_role = create_role(
            "DOCTOR_MANAGER",
            [
                "can_view_doctors",
                "can_view_all_doctors",
                "can_manage_doctor_schedules",
            ],
        )
        self.viewer_role = create_role(
            "PATIENT",
            ["can_view_doctors"],
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doctor@example.com",
            password="SafePassword!123",
            role=self.doctor_role,
            first_name="Grace",
            last_name="Nambi",
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization=Specialization.PEDIATRICS,
            license_number="LIC-001",
        )
        self.other_doctor_user = CustomUser.objects.create_user(
            email="other-doctor@example.com",
            password="SafePassword!123",
            role=self.doctor_role,
        )
        self.other_doctor = DoctorProfile.objects.create(
            user=self.other_doctor_user,
            specialization=Specialization.CARDIOLOGY,
            license_number="LIC-002",
        )
        self.manager_user = CustomUser.objects.create_user(
            email="manager@example.com",
            password="SafePassword!123",
            role=self.manager_role,
        )
        self.viewer_user = CustomUser.objects.create_user(
            email="viewer@example.com",
            password="SafePassword!123",
            role=self.viewer_role,
        )

    def schedule_payload(self, **overrides):
        payload = {
            "day_of_week": 0,
            "start_time": "08:00",
            "end_time": "17:00",
            "session_duration": 30,
            "is_available": True,
        }
        payload.update(overrides)
        return payload

    def test_doctor_manages_only_own_schedule(self):
        self.client.force_authenticate(self.doctor_user)
        response = self.client.post(
            reverse("doctor-schedule-list-create"),
            self.schedule_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule = DoctorSchedule.objects.get(pk=response.data["id"])
        self.assertEqual(schedule.doctor, self.doctor)

        response = self.client.post(
            reverse("doctor-schedule-list-create"),
            self.schedule_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.other_doctor_user)
        response = self.client.get(
            reverse("doctor-schedule-detail", args=[schedule.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_create_schedule_for_any_doctor(self):
        self.client.force_authenticate(self.manager_user)
        response = self.client.post(
            reverse("doctor-schedule-list-create"),
            self.schedule_payload(doctor=self.other_doctor.pk),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule = DoctorSchedule.objects.get(pk=response.data["id"])
        self.assertEqual(schedule.doctor, self.other_doctor)

    def test_doctor_directory_filters_and_searches(self):
        self.client.force_authenticate(self.viewer_user)
        response = self.client.get(
            reverse("doctor-list"),
            {
                "specialization": "pediatrics",
                "search": "grace",
                "is_available": "true",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.doctor.pk)

        response = self.client.get(
            reverse("doctor-list"),
            {"is_available": "sometimes"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)