from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasCustomPermission

from .models import Medicine, Prescription
from .serializers import (
    MedicineCreateSerializer,
    MedicineListSerializer,
    PrescriptionCreateSerializer,
    PrescriptionDispenseSerializer,
    PrescriptionListSerializer,
)
from .service import dispense_prescription


class MedicineListView(generics.ListAPIView):
    serializer_class = MedicineListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medicines"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Medicine.objects.none()

        if self.request.user.has_permission("can_view_all_medicines"):
            return Medicine.objects.all()

        return Medicine.objects.filter(is_active=True)


class MedicineCreateView(generics.CreateAPIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medicines"


class MedicineUpdateView(generics.UpdateAPIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_edit_medicines"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Medicine.objects.none()
        return Medicine.objects.all()


class PrescriptionCreateView(generics.CreateAPIView):
    serializer_class = PrescriptionCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_prescriptions"


class PrescriptionListView(generics.ListAPIView):
    serializer_class = PrescriptionListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_prescriptions"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Prescription.objects.none()

        user = self.request.user
        queryset = Prescription.objects.select_related(
            "medicine",
            "medical_record__appointment__doctor__user",
            "medical_record__appointment__patient__user",
        )

        if user.has_permission("can_view_all_prescriptions"):
            return queryset

        if user.role_code == "DOCTOR":
            return queryset.filter(
                medical_record__appointment__doctor__user=user
            )

        if user.role_code == "PATIENT":
            return queryset.filter(
                medical_record__appointment__patient__user=user
            )

        return Prescription.objects.none()


class PatientPrescriptionListView(generics.ListAPIView):
    serializer_class = PrescriptionListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_prescriptions"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Prescription.objects.none()

        return Prescription.objects.filter(
            medical_record__appointment__patient__user=self.request.user
        ).select_related(
            "medicine",
            "medical_record__appointment__doctor__user",
            "medical_record__appointment__patient__user",
        )


class PrescriptionDispenseView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_dispense_prescriptions"
    serializer_class = PrescriptionDispenseSerializer

    def post(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)

        try:
            dispense_prescription(prescription)
            return Response(
                {"message": f"Prescription #{pk} dispensed successfully."},
                status=status.HTTP_200_OK,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
