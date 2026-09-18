from django.shortcuts import get_object_or_404
from django.db.models import F, Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.core.permissions import HasCustomPermission
from apps.core.schemas import ErrorResponse, MessageResponse
from apps.utilities.mixin import PaginationMixin

from .models import (
    Medicine,
    Prescription,
    PrescriptionStatus,
    UnitType,
)
from .serializers import (
    MedicineCreateSerializer,
    MedicineListSerializer,
    PrescriptionCreateSerializer,
    PrescriptionDispenseSerializer,
    PrescriptionListSerializer,
)
from .service import cancel_prescription, dispense_prescription


@extend_schema(
    tags=["Pharmacy"],
    summary="List medicines",
    parameters=[
        OpenApiParameter(name="unit_type", type=str),
        OpenApiParameter(name="is_active", type=bool),
        OpenApiParameter(name="low_stock", type=bool),
        OpenApiParameter(name="search", type=str),
        OpenApiParameter(
            name="ordering",
            type=str,
            description=(
                "name, stock_quantity, unit_cost or created_at; "
                "prefix with - for descending order."
            ),
        ),
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: MedicineListSerializer(many=True)},
)
class MedicineListView(PaginationMixin, APIView):
    serializer_class = MedicineListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_medicines"

    def get_queryset(self):
        queryset = Medicine.objects.all()

        if not self.request.user.has_permission("can_view_all_medicines"):
            queryset = queryset.filter(is_active=True)

        unit_type = self.request.query_params.get("unit_type")
        if unit_type:
            unit_type = unit_type.lower()
            if unit_type not in UnitType.values:
                raise ValidationError({"unit_type": "Invalid medicine unit type."})
            queryset = queryset.filter(unit_type=unit_type)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            normalized = is_active.lower()
            if normalized not in {"true", "false"}:
                raise ValidationError({"is_active": "Use true or false."})
            queryset = queryset.filter(is_active=normalized == "true")

        low_stock = self.request.query_params.get("low_stock")
        if low_stock is not None:
            normalized = low_stock.lower()
            if normalized not in {"true", "false"}:
                raise ValidationError({"low_stock": "Use true or false."})
            if normalized == "true":
                queryset = queryset.filter(
                    stock_quantity__lte=F("low_stock_threshold")
                )
            else:
                queryset = queryset.filter(
                    stock_quantity__gt=F("low_stock_threshold")
                )

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        ordering = self.request.query_params.get("ordering", "name")
        allowed_ordering = {
            "name", "-name", "stock_quantity", "-stock_quantity",
            "unit_cost", "-unit_cost", "created_at", "-created_at",
        }
        if ordering not in allowed_ordering:
            raise ValidationError({"ordering": "Invalid ordering field."})

        return queryset.order_by(ordering)

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            self.serializer_class,
            context={"request": request},
        )


@extend_schema(
    tags=["Pharmacy"],
    summary="Add a medicine",
    request=MedicineCreateSerializer,
    responses={201: MedicineListSerializer},
)
class MedicineCreateView(APIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_medicines"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        medicine = serializer.save()

        from apps.notifications.triggers import queue_low_stock_check

        queue_low_stock_check(medicine=medicine)
        return Response(
            MedicineListSerializer(
                medicine,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Pharmacy"],
        summary="Get a medicine",
        responses={200: MedicineListSerializer},
    ),
    put=extend_schema(
        tags=["Pharmacy"],
        summary="Replace a medicine",
        request=MedicineCreateSerializer,
        responses={200: MedicineListSerializer},
    ),
    patch=extend_schema(
        tags=["Pharmacy"],
        summary="Update a medicine",
        request=MedicineCreateSerializer,
        responses={200: MedicineListSerializer},
    ),
)
class MedicineDetailView(APIView):
    serializer_class = MedicineCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_medicines",),
        "PUT": ("can_edit_medicines",),
        "PATCH": ("can_edit_medicines",),
    }

    def get_object(self):
        queryset = Medicine.objects.all()

        if (
            self.request.method == "GET"
            and not self.request.user.has_permission("can_view_all_medicines")
        ):
            queryset = queryset.filter(is_active=True)

        return get_object_or_404(queryset, pk=self.kwargs["pk"])

    def get(self, request, pk):
        serializer = MedicineListSerializer(
            self.get_object(),
            context={"request": request},
        )
        return Response(serializer.data)

    def update(self, request, pk, *, partial):
        serializer = self.serializer_class(
            self.get_object(),
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        medicine = serializer.save()

        from apps.notifications.triggers import queue_low_stock_check

        queue_low_stock_check(medicine=medicine)
        return Response(
            MedicineListSerializer(
                medicine,
                context={"request": request},
            ).data
        )

    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update(request, pk, partial=True)


@extend_schema(
    tags=["Pharmacy"],
    summary="Create a prescription",
    request=PrescriptionCreateSerializer,
    responses={201: PrescriptionListSerializer},
)
class PrescriptionCreateView(APIView):
    serializer_class = PrescriptionCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_prescriptions"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save()
        return Response(
            PrescriptionListSerializer(
                prescription,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PrescriptionListBaseView(APIView):
    serializer_class = PrescriptionListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_prescriptions"

    def base_queryset(self):
        return Prescription.objects.select_related(
            "medicine",
            "medical_record__appointment__doctor__user",
            "medical_record__appointment__patient__user",
        )
    def apply_filters(self, queryset):
        status_code = self.request.query_params.get("status")
        if status_code:
            status_code = status_code.upper()
            if status_code not in PrescriptionStatus.values:
                raise ValidationError({"status": "Invalid prescription status."})
            queryset = queryset.filter(status=status_code)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(medicine__name__icontains=search)
                | Q(medical_record__appointment__patient__user__email__icontains=search)
                | Q(medical_record__appointment__patient__user__first_name__icontains=search)
                | Q(medical_record__appointment__patient__user__last_name__icontains=search)
            )

        ordering = self.request.query_params.get("ordering", "-prescribed_at")
        allowed_ordering = {
            "prescribed_at", "-prescribed_at",
            "dispensed_at", "-dispensed_at",
            "quantity_prescribed", "-quantity_prescribed",
        }
        if ordering not in allowed_ordering:
            raise ValidationError({"ordering": "Invalid ordering field."})

        return queryset.order_by(ordering)


@extend_schema(
    tags=["Pharmacy"],
    summary="List prescriptions",
    parameters=[
        OpenApiParameter(name="status", type=str),
        OpenApiParameter(
            name="search",
            type=str,
            description="Search by medicine or patient name/email.",
        ),
        OpenApiParameter(
            name="ordering",
            type=str,
            description=(
                "prescribed_at, dispensed_at or quantity_prescribed; "
                "prefix with - for descending order."
            ),
        ),
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: PrescriptionListSerializer(many=True)},
)
class PrescriptionListView(PaginationMixin, PrescriptionListBaseView):
    def get_queryset(self):
        user = self.request.user
        queryset = self.base_queryset()

        if user.has_permission("can_view_all_prescriptions"):
            visible_queryset = queryset
        elif user.role_code == "DOCTOR":
            visible_queryset = queryset.filter(
                medical_record__appointment__doctor__user=user
            )
        elif user.role_code == "PATIENT":
            visible_queryset = queryset.filter(
                medical_record__appointment__patient__user=user
            )
        else:
            return Prescription.objects.none()

        return self.apply_filters(visible_queryset)

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            self.serializer_class,
            context={"request": request},
        )


@extend_schema(
    tags=["Pharmacy"],
    summary="List my prescriptions",
    parameters=[
        OpenApiParameter(name="status", type=str),
        OpenApiParameter(name="search", type=str),
        OpenApiParameter(name="ordering", type=str),
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: PrescriptionListSerializer(many=True)},
)
class PatientPrescriptionListView(PaginationMixin, PrescriptionListBaseView):
    def get_queryset(self):
        return self.apply_filters(
            self.base_queryset().filter(
                medical_record__appointment__patient__user=self.request.user
            )
        )

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            self.serializer_class,
            context={"request": request},
        )


@extend_schema(
    tags=["Pharmacy"],
    summary="Dispense a prescription",
    request=None,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
class PrescriptionDispenseView(APIView):
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_dispense_prescriptions"

    def post(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)

        try:
            dispense_prescription(prescription)
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": f"Prescription #{pk} dispensed successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Pharmacy"],
    summary="Cancel a prescription",
    request=None,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
class PrescriptionCancelView(APIView):
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_cancel_prescriptions"

    def get_queryset(self):
        queryset = Prescription.objects.select_related(
            "medical_record__appointment__doctor__user",
        )

        if self.request.user.has_permission("can_view_all_prescriptions"):
            return queryset

        return queryset.filter(
            medical_record__appointment__doctor__user=self.request.user
        )

    def post(self, request, pk):
        prescription = get_object_or_404(self.get_queryset(), pk=pk)

        try:
            cancel_prescription(
                prescription=prescription,
                cancelled_by=request.user,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": f"Prescription #{pk} cancelled successfully."},
            status=status.HTTP_200_OK,
        )
