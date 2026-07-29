from django.contrib import admin
from .models import Medicine, Prescription


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display  = ('name', 'unit_type', 'stock_quantity', 'low_stock_threshold', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter   = ('unit_type', 'is_active')
    list_editable = ('stock_quantity', 'is_active')
    # list_editable lets you update stock directly from the list page
    # without clicking into each medicine individually


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display  = ('medicine', 'medical_record', 'quantity_prescribed', 'status', 'prescribed_at', 'dispensed_at')
    search_fields = ('medicine__name', 'medical_record__appointment__patient__user__email')
    list_filter   = ('status',)