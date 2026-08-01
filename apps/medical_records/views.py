from rest_framework import generics
from drf_spectacular.utils import extend_schema

from apps.core.permissions import HasCustomPermission

from .models import MedicalRecord
from .serializers import MedicalRecordCreateSerializer, MedicalRecordListSerializer


@extend_schema(
    tags=["Medical Records"],
    summary="Create a medical record",
    description=(
        "Creates a medical record for a completed appointment. The record can "
        "only be created by the doctor assigned to the appointment, and only "
        "once per appointment."
    ),
    request=MedicalRecordCreateSerializer,
    responses={201: MedicalRecordListSerializer},
)
class MedicalRecordCreateView(generics.CreateAPIView):
    serializer_class = MedicalRecordCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medical_records"


@extend_schema(
    tags=["Medical Records"],
    summary="List medical records",
    description=(
        "Role-aware list of medical records: patients see their own, doctors "
        "see the records they authored, and users with "
        "`can_view_all_medical_records` see everything."
    ),
    responses={200: MedicalRecordListSerializer(many=True)},
)
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


@extend_schema(
    tags=["Medical Records"],
    summary="Get a medical record",
    description=(
        "Returns a single medical record, restricted by the same role-aware "
        "rules as the list endpoint."
    ),
    responses={200: MedicalRecordListSerializer},
)
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
