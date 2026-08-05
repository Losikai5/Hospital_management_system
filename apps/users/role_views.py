from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
        responses={200: RoleDetailSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Role Management"],
        summary="Create a custom role",
        request=RoleCreateSerializer,
        responses={201: RoleDetailSerializer},
    ),
)
class RoleListCreateView(APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "POST": ("can_create_roles", "can_assign_permissions"),
    }

    def get(self, request):
        roles = Role.objects.prefetch_related("permissions").order_by("code")
        return Response(RoleDetailSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(
            RoleDetailSerializer(role).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Role Management"],
        summary="Get a role",
        responses={200: RoleDetailSerializer},
    ),
    patch=extend_schema(
        tags=["Role Management"],
        summary="Update a role",
        request=RoleDetailSerializer,
        responses={200: RoleDetailSerializer},
    ),
    put=extend_schema(
        tags=["Role Management"],
        summary="Replace a role",
        request=RoleDetailSerializer,
        responses={200: RoleDetailSerializer},
    ),
    delete=extend_schema(
        tags=["Role Management"],
        summary="Delete a custom role",
        responses={204: None, 400: ErrorResponse},
    ),
)
class RoleDetailView(APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "PATCH": ("can_edit_roles",),
        "PUT": ("can_edit_roles",),
        "DELETE": ("can_edit_roles",),
    }

    @staticmethod
    def get_role(code):
        return get_object_or_404(
            Role.objects.prefetch_related("permissions"),
            code=code.upper(),
        )

    def get(self, request, code):
        return Response(RoleDetailSerializer(self.get_role(code)).data)

    def patch(self, request, code):
        role = self.get_role(code)
        serializer = RoleDetailSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, code):
        role = self.get_role(code)
        serializer = RoleDetailSerializer(role, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, code):
        role = self.get_role(code)
        if role.is_system:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if role.users.exists():
            return Response(
                {"detail": "Cannot delete a role that is currently assigned to users."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Role Management"],
    summary="Assign permissions to a role",
    request=RolePermissionUpdateSerializer,
    responses={200: RoleDetailSerializer, 400: ErrorResponse},
)
class RolePermissionUpdateView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_assign_permissions"
    serializer_class = RolePermissionUpdateSerializer

    def put(self, request, code):
        role = get_object_or_404(Role, code=code.upper())
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = Permission.objects.filter(
            code__in=serializer.validated_data["permissions"],
            is_active=True,
        )
        role.permissions.set(permissions)
        return Response(RoleDetailSerializer(role).data)


@extend_schema(
    tags=["Role Management"],
    summary="List permissions",
    responses={200: PermissionSerializer(many=True)},
)
class PermissionListView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_permissions"

    def get(self, request):
        permissions = Permission.objects.filter(is_active=True).order_by("code")
        return Response(PermissionSerializer(permissions, many=True).data)