from rest_framework import generics

from apps.core.permissions import HasCustomPermission

from .models import MedicalRecord
from .serializers import MedicalRecordCreateSerializer, MedicalRecordListSerializer


class MedicalRecordCreateView(generics.CreateAPIView):
    serializer_class = MedicalRecordCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medical_records"


class MedicalRecordListView(generics.ListAPIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medical_records"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return MedicalRecord.objects.none()

        user = self.request.user
        queryset = MedicalRecord.objects.select_related(
            "appointment__doctor__user",
            "appointment__patient__user",
        )

        if user.has_permission("can_view_all_medical_records"):
            return queryset

        if user.role_code == "DOCTOR":
            return queryset.filter(appointment__doctor__user=user)

        if user.role_code == "PATIENT":
            return queryset.filter(appointment__patient__user=user)

        return MedicalRecord.objects.none()


class MedicalRecordDetailView(generics.RetrieveAPIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medical_records"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return MedicalRecord.objects.none()

        user = self.request.user
        queryset = MedicalRecord.objects.select_related(
            "appointment__doctor__user",
            "appointment__patient__user",
        )

        if user.has_permission("can_view_all_medical_records"):
            return queryset

        if user.role_code == "DOCTOR":
            return queryset.filter(appointment__doctor__user=user)

        if user.role_code == "PATIENT":
            return queryset.filter(appointment__patient__user=user)

        return MedicalRecord.objects.none()
