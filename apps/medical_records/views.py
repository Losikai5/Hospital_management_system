from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasCustomPermission
from apps.utilities.mixin import PaginationMixin

from .models import MedicalRecord
from .serializers import MedicalRecordCreateSerializer, MedicalRecordListSerializer


@extend_schema(
    tags=["Medical Records"],
    summary="Create a medical record",
    request=MedicalRecordCreateSerializer,
    responses={201: MedicalRecordListSerializer},
)
class MedicalRecordCreateView(APIView):
    serializer_class = MedicalRecordCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medical_records"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            MedicalRecordListSerializer(record).data,
            status=status.HTTP_201_CREATED,
        )


class MedicalRecordVisibilityMixin:
    def get_queryset(self):
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
    summary="List medical records",
    parameters=[
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: MedicalRecordListSerializer(many=True)},
)
class MedicalRecordListView(PaginationMixin, MedicalRecordVisibilityMixin, APIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medical_records"

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            self.serializer_class,
        )


@extend_schema(
    tags=["Medical Records"],
    summary="Get a medical record",
    responses={200: MedicalRecordListSerializer},
)
class MedicalRecordDetailView(MedicalRecordVisibilityMixin, APIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medical_records"

    def get(self, request, pk):
        record = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(self.serializer_class(record).data)