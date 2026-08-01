from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.core.permissions import HasCustomPermission
from apps.core.schemas import ErrorResponse, MessageResponse

from .models import Medicine, Prescription
from .serializers import (
    MedicineCreateSerializer,
    MedicineListSerializer,
    PrescriptionCreateSerializer,
    PrescriptionDispenseSerializer,
    PrescriptionListSerializer,
)
from .service import dispense_prescription


@extend_schema(
    tags=["Pharmacy"],
    summary="List medicines",
    description=(
        "Lists medicines in the pharmacy inventory. Users without "
        "`can_view_all_medicines` only see active medicines."
    ),
    responses={200: MedicineListSerializer(many=True)},
)
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


@extend_schema(
    tags=["Pharmacy"],
    summary="Add a medicine",
    description="Adds a new medicine to the pharmacy inventory.",
    request=MedicineCreateSerializer,
    responses={201: MedicineListSerializer},
)
class MedicineCreateView(generics.CreateAPIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medicines"


@extend_schema(
    tags=["Pharmacy"],
    summary="Update a medicine",
    description=(
        "Partially updates a medicine's details and stock levels. PUT and PATCH "
        "are both supported."
    ),
    request=MedicineCreateSerializer,
    responses={200: MedicineListSerializer},
)
class MedicineUpdateView(generics.UpdateAPIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_edit_medicines"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Medicine.objects.none()
        return Medicine.objects.all()


@extend_schema(
    tags=["Pharmacy"],
    summary="Create a prescription",
    description=(
        "Creates a prescription for one of the prescribing doctor's own medical "
        "records. Status is set to PENDING automatically."
    ),
    request=PrescriptionCreateSerializer,
    responses={201: PrescriptionListSerializer},
)
class PrescriptionCreateView(generics.CreateAPIView):
    serializer_class = PrescriptionCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_prescriptions"


@extend_schema(
    tags=["Pharmacy"],
    summary="List prescriptions",
    description=(
        "Role-aware list of prescriptions: patients see their own, doctors see "
        "the ones they prescribed, and users with `can_view_all_prescriptions` "
        "see everything."
    ),
    responses={200: PrescriptionListSerializer(many=True)},
)
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


@extend_schema(
    tags=["Pharmacy"],
    summary="List my prescriptions",
    description="Returns the prescriptions belonging to the currently authenticated patient.",
    responses={200: PrescriptionListSerializer(many=True)},
)
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


@extend_schema(
    tags=["Pharmacy"],
    summary="Dispense a prescription",
    description=(
        "Dispenses a pending prescription: marks it as dispensed, records the "
        "dispensed time, and deducts the prescribed quantity from medicine stock."
    ),
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
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
