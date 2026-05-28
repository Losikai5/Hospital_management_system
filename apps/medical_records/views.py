from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import MedicalRecord
from .serializers import MedicalRecordCreateSerializer, MedicalRecordListSerializer
from apps.core.permissions import IsDoctor, IsAdminOrReceptionist


class MedicalRecordCreateView(generics.CreateAPIView):
    serializer_class = MedicalRecordCreateSerializer
    permission_classes = [IsAuthenticated, IsDoctor]


class MedicalRecordListView(generics.ListAPIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Guard for drf-spectacular schema generation
        if getattr(self, 'swagger_fake_view', False):
            return MedicalRecord.objects.none()

        user = self.request.user

        if user.role in ['ADMIN', 'RECEPTIONIST']:
            return MedicalRecord.objects.all().select_related(
                'appointment__doctor__user',
                'appointment__patient__user'
            )
        if user.role == 'DOCTOR':
            return MedicalRecord.objects.filter(
                appointment__doctor__user=user
            ).select_related(
                'appointment__doctor__user',
                'appointment__patient__user'
            )
        if user.role == 'PATIENT':
            return MedicalRecord.objects.filter(
                appointment__patient__user=user
            ).select_related(
                'appointment__doctor__user',
                'appointment__patient__user'
            )

        return MedicalRecord.objects.none()


class MedicalRecordDetailView(generics.RetrieveAPIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MedicalRecord.objects.none()

        user = self.request.user

        if user.role in ['ADMIN', 'RECEPTIONIST']:
            return MedicalRecord.objects.all()
        if user.role == 'DOCTOR':
            return MedicalRecord.objects.filter(
                appointment__doctor__user=user
            )
        if user.role == 'PATIENT':
            return MedicalRecord.objects.filter(
                appointment__patient__user=user
            )

        return MedicalRecord.objects.none()