import ipaddress
import logging
import uuid

from django.conf import settings

from .models import AuditLog


logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    API_PREFIX = "/api/v1/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id = request_id[:100]

        try:
            response = self.get_response(request)
        except Exception:
            if self.should_log(request):
                self.write_log(request, request_id=request_id, status_code=500)
            raise

        response["X-Request-ID"] = request_id
        if self.should_log(request):
            self.write_log(
                request,
                request_id=request_id,
                status_code=response.status_code,
            )
        return response

    def should_log(self, request):
        return (
            request.method in self.MUTATING_METHODS
            and request.path.startswith(self.API_PREFIX)
        )

    def write_log(self, request, *, request_id, status_code):
        try:
            resolver_match = getattr(request, "resolver_match", None)
            url_name = getattr(resolver_match, "url_name", None)
            actor = getattr(request, "user", None)
            authenticated_actor = (
                actor
                if getattr(actor, "is_authenticated", False)
                else None
            )
            resource_type, resource_id = self.resolve_resource(request.path)

            AuditLog.objects.create(
                actor=authenticated_actor,
                actor_email=(
                    authenticated_actor.email
                    if authenticated_actor is not None
                    else ""
                ),
                action=url_name or f"{request.method} {request.path}",
                method=request.method,
                path=request.path[:500],
                status_code=status_code,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=self.get_ip_address(request),
                user_agent=request.headers.get("User-Agent", "")[:500],
                request_id=request_id,
                metadata={
                    "query_keys": sorted(request.GET.keys()),
                    "authenticated": authenticated_actor is not None,
                },
            )
        except Exception:
            logger.exception("Could not persist API audit log.")

    @classmethod
    def resolve_resource(cls, path):
        relative_path = path.removeprefix(cls.API_PREFIX).strip("/")
        segments = relative_path.split("/") if relative_path else []
        resource_type = segments[0][:100] if segments else ""
        resource_id = ""
        for segment in segments[1:]:
            if segment.isdigit():
                resource_id = segment[:100]
                break
        return resource_type, resource_id

    @staticmethod
    def get_ip_address(request):
        raw_ip = request.META.get("REMOTE_ADDR")
        if getattr(settings, "AUDIT_TRUST_X_FORWARDED_FOR", False):
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                raw_ip = forwarded.split(",", 1)[0].strip()

        if not raw_ip:
            return None
        try:
            return str(ipaddress.ip_address(raw_ip))
        except ValueError:
            return None

