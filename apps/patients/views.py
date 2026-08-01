from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import HasCustomPermission

from .models import PatientProfile
from .serializers import PatientProfileSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Patients"],
        summary="Get my patient profile",
        description=(
            "Returns the patient profile linked to the currently authenticated "
            "user. Requires the `can_view_patients` permission."
        ),
        responses={200: PatientProfileSerializer},
    ),
    patch=extend_schema(
        tags=["Patients"],
        summary="Update my patient profile",
        description=(
            "Partially updates the patient profile linked to the currently "
            "authenticated user. Requires the `can_edit_patients` permission."
        ),
        request=PatientProfileSerializer,
        responses={200: PatientProfileSerializer},
    ),
)
class PatientProfileView(APIView):
    serializer_class = PatientProfileSerializer
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_patients",),
        "PATCH": ("can_edit_patients",),
    }

    def get_object(self, user):
        return get_object_or_404(
            PatientProfile.objects.select_related(
                "user",
                "user__role",
            ),
            user=user,
        )

    def get(self, request):
        serializer = self.serializer_class(
            self.get_object(request.user),
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request):
        serializer = self.serializer_class(
            self.get_object(request.user),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
