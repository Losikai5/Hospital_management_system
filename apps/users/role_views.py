from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import HasCustomPermission
from apps.core.schemas import ErrorResponse

from .models import Permission, Role
from .role_serializers import (
    PermissionSerializer,
    RoleCreateSerializer,
    RoleDetailSerializer,
    RolePermissionUpdateSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Role Management"],
        summary="List roles",
        description="Returns all roles. Requires the `can_view_roles` permission.",
        responses={200: RoleDetailSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Role Management"],
        summary="Create a custom role",
        description=(
            "Creates a new custom role (is_system=False) and optionally assigns "
            "permissions to it. Requires the `can_create_roles` permission."
        ),
        request=RoleCreateSerializer,
        responses={201: RoleDetailSerializer},
    ),
)
class RoleListCreateView(generics.ListCreateAPIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "POST": ("can_create_roles",),
    }
    serializer_class = RoleDetailSerializer
    queryset = Role.objects.prefetch_related("permissions").order_by("code")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RoleCreateSerializer
        return self.serializer_class


@extend_schema_view(
    get=extend_schema(
        tags=["Role Management"],
        summary="Get a role",
        description="Returns a single role by code. Requires the `can_view_roles` permission.",
        responses={200: RoleDetailSerializer},
    ),
    patch=extend_schema(
        tags=["Role Management"],
        summary="Update a role",
        description=(
            "Updates role information and/or replaces its permissions. "
            "Requires the `can_edit_roles` permission."
        ),
        request=RoleDetailSerializer,
        responses={200: RoleDetailSerializer},
    ),
    put=extend_schema(
        tags=["Role Management"],
        summary="Update a role",
        description=(
            "Updates role information and/or replaces its permissions. "
            "Requires the `can_edit_roles` permission."
        ),
        request=RoleDetailSerializer,
        responses={200: RoleDetailSerializer},
    ),
    delete=extend_schema(
        tags=["Role Management"],
        summary="Delete a custom role",
        description=(
            "Deletes a custom role. Requires the `can_edit_roles` permission. "
            "System roles and roles assigned to users cannot be deleted."
        ),
        responses={204: None, 400: ErrorResponse},
    ),
)
class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "PATCH": ("can_edit_roles",),
        "PUT": ("can_edit_roles",),
        "DELETE": ("can_edit_roles",),
    }
    serializer_class = RoleDetailSerializer
    queryset = Role.objects.prefetch_related("permissions")
    lookup_field = "code"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), code=self.kwargs["code"].upper())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if instance.users.exists():
            return Response(
                {"detail": "Cannot delete a role that is currently assigned to users."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Role Management"],
    summary="Assign permissions to a role",
    description=(
        "Replaces the permission set of a role with the given permission codes. "
        "Requires the `can_assign_permissions` permission."
    ),
    request=RolePermissionUpdateSerializer,
    responses={
        200: RoleDetailSerializer,
        400: ErrorResponse,
    },
)
class RolePermissionUpdateView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_assign_permissions"
    serializer_class = RolePermissionUpdateSerializer

    def put(self, request, code):
        role = get_object_or_404(Role, code=code.upper())
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        codes = serializer.validated_data["permissions"]
        permissions = Permission.objects.filter(code__in=codes, is_active=True)
        role.permissions.set(permissions)

        out_serializer = RoleDetailSerializer(role)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Role Management"],
    summary="List permissions",
    description="Returns all active permissions. Requires the `can_view_permissions` permission.",
    responses={200: PermissionSerializer(many=True)},
)
class PermissionListView(generics.ListAPIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_permissions"
    serializer_class = PermissionSerializer
    queryset = Permission.objects.filter(is_active=True).order_by("code")
