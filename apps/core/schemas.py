from rest_framework import serializers
from drf_spectacular.utils import inline_serializer

MessageResponse = inline_serializer(
    "MessageResponse",
    {"message": serializers.CharField()},
)

ErrorResponse = inline_serializer(
    "ErrorResponse",
    {"error": serializers.CharField()},
)
