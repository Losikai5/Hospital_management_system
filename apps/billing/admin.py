from django.contrib import admin

from .models import Invoice, InvoiceItem, InvoicePayment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    can_delete = False
    readonly_fields = ("description", "quantity", "unit_price", "total")

    def has_add_permission(self, request, obj=None):
        return False


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    can_delete = False
    readonly_fields = (
        "amount",
        "method",
        "reference",
        "notes",
        "recorded_by",
        "paid_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "total_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "appointment__patient__user__email",
        "appointment__doctor__user__email",
    )
    readonly_fields = ("appointment", "total_amount", "created_at", "updated_at")
    inlines = (InvoiceItemInline, InvoicePaymentInline)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "description", "quantity", "unit_price", "total")
    readonly_fields = (
        "invoice",
        "description",
        "quantity",
        "unit_price",
        "total",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice",
        "amount",
        "method",
        "reference",
        "recorded_by",
        "paid_at",
    )
    list_filter = ("method", "paid_at")
    search_fields = (
        "reference",
        "invoice__appointment__patient__user__email",
        "recorded_by__email",
    )
    readonly_fields = (
        "invoice",
        "amount",
        "method",
        "reference",
        "notes",
        "recorded_by",
        "paid_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False