from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from pgvector.django import VectorField
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.utilities.models import SoftDeletableTimestampModel


class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class PermissionEmbedding(models.Model):
    """Derived permission-search data; never a source of authorization grants."""

    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        related_name="embedding",
    )
    embedding = VectorField(dimensions=768)
    model_name = models.CharField(max_length=150)
    dimensions = models.PositiveIntegerField(
        default=768,
        validators=[MinValueValidator(1)],
    )
    source_text = models.TextField(
        help_text="Exact permission text used to generate this embedding.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        from ai.embeddings import EmbeddingError, validate_embedding

        if self.dimensions != 768:
            raise ValidationError({"dimensions": "The vector field requires 768 dimensions."})
        try:
            validate_embedding(self.embedding, self.dimensions)
        except EmbeddingError as error:
            raise ValidationError({"embedding": str(error)}) from None

    def __str__(self):
        return f"{self.permission.code} ({self.model_name}, {self.dimensions} dimensions)"


class Role(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        Permission,
        through="RolePermission",
        related_name="roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permission_assignments",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role.code}: {self.permission.code}"


class UserPermission(models.Model):
    pass

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))

        roles = extra_fields.pop("roles", None)
        permissions = extra_fields.pop("permissions", None)

        if not roles:
            raise ValueError(_("At least one role must be assigned to the user"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        if isinstance(roles, (list, tuple, set)):
            user.roles.set(roles)
        else:
            user.roles.set([roles])

        if permissions is not None:
            user.permissions.set(permissions)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Admin user must have is_staff=True."))

        if extra_fields.get("is_active") is not True:
            raise ValueError(_("Admin user must have is_active=True."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        try:
            admin_role = Role.objects.get(code="ADMIN", is_active=True)
        except Role.DoesNotExist as error:
            raise ValueError(_("The ADMIN role must be created first.")) from error

        extra_fields["roles"] = [admin_role]
        extra_fields["permissions"] = list(
            Permission.objects.filter(is_active=True)
        )
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    roles = models.ManyToManyField(
        Role,
        related_name="user_roles",
        blank=True,
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="user_grants",
        blank=True,
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        blank=True,
        null=True,
    )
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def role_codes(self):
        return list(self.roles.values_list("code", flat=True))

    def has_role(self, role_code):
        return self.roles.filter(code=role_code, is_active=True).exists()

    def get_permission_codes(self):
        return list(
            self.permissions.filter(is_active=True)
            .order_by("code")
            .values_list("code", flat=True)
        )

    def has_permission(self, permission_code):
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        if self.roles.filter(code="ADMIN", is_active=True).exists():
            return True

        return self.permissions.filter(
            code=permission_code,
            is_active=True,
        ).exists()

    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_superuser:
            return True

        return self.is_active and self.is_staff and "ADMIN" in self.role_codes

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

        return self.is_active and self.is_staff and "ADMIN" in self.role_codes

    def __str__(self):
        return f"{self.email} ({', '.join(self.role_codes)})"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]


class StaffInvitation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_invitation')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sent_invitations')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
     return f"Invitation for {self.user.email} by {self.invited_by.email}"
    class Meta:
        ordering = ['-created_at']
