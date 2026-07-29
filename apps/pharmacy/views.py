from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Medicine, Prescription
from .serializers import (
    MedicineCreateSerializer,
    MedicineListSerializer,
    PrescriptionCreateSerializer,
    PrescriptionListSerializer,
    PrescriptionDispenseSerializer
)
from .service import dispense_prescription
from apps.core.permissions import (
    IsDoctor,
    IsPatient,
    IsAdminOrPharmacist
)


class MedicineListView(generics.ListAPIView):
    """List all medicines — Admin and Pharmacist only."""
    serializer_class   = MedicineListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPharmacist]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Medicine.objects.none()
        return Medicine.objects.filter(is_active=True)


class MedicineCreateView(generics.CreateAPIView):
    """Add a new medicine — Admin and Pharmacist only."""
    serializer_class   = MedicineCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPharmacist]


class MedicineUpdateView(generics.UpdateAPIView):
    """Update medicine stock — Admin and Pharmacist only."""
    serializer_class   = MedicineCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrPharmacist]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Medicine.objects.none()
        return Medicine.objects.all()


class PrescriptionCreateView(generics.CreateAPIView):
    """Doctor creates a prescription after a consultation."""
    serializer_class   = PrescriptionCreateSerializer
    permission_classes = [IsAuthenticated, IsDoctor]


class PrescriptionListView(generics.ListAPIView):
    """
    List prescriptions — role aware.
    Admin and Pharmacist see all prescriptions.
    Doctor sees only prescriptions they created.
    """
    serializer_class   = PrescriptionListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()

        user = self.request.user

        if user.role in ['ADMIN', 'PHARMACIST']:
            return Prescription.objects.all().select_related(
                'medicine',
                'medical_record__appointment__doctor__user',
                'medical_record__appointment__patient__user'
            )

        if user.role == 'DOCTOR':
            return Prescription.objects.filter(
                medical_record__appointment__doctor__user=user
            ).select_related(
                'medicine',
                'medical_record__appointment__patient__user'
            )

        return Prescription.objects.none()


class PatientPrescriptionListView(generics.ListAPIView):
    """Patient views their own prescriptions."""
    serializer_class   = PrescriptionListSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()

        return Prescription.objects.filter(
            medical_record__appointment__patient__user=self.request.user
        ).select_related(
            'medicine',
            'medical_record__appointment__doctor__user',
            'medical_record__appointment__patient__user'
        )


class PrescriptionDispenseView(APIView):
    """
    Pharmacist or Admin dispenses a prescription.
    Calls the service layer which handles all business logic.
    """
    permission_classes = [IsAuthenticated, IsAdminOrPharmacist]
    serializer_class   = PrescriptionDispenseSerializer

    def post(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)

        try:
            dispense_prescription(prescription)
            return Response(
                {'message': f'Prescription #{pk} dispensed successfully.'},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            # Service layer raises ValueError for business rule violations
            # View catches it and converts to proper HTTP 400 response
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )