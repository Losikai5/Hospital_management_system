from io import BytesIO

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasCustomPermission
from apps.utilities.mixin import PaginationMixin

from .models import Invoice
from .serializers import (
    InvoiceCreateSerializer,
    InvoicePaymentCreateSerializer,
    InvoicePaymentSerializer,
    InvoiceSerializer,
)


class InvoiceAccessMixin:
    def get_queryset(self):
        queryset = Invoice.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        ).prefetch_related("items", "payments__recorded_by")

        if self.request.user.has_permission("can_view_all_invoices"):
            return queryset

        return queryset.filter(
            appointment__patient__user=self.request.user,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Billing"],
        summary="List accessible invoices",
        parameters=[
            OpenApiParameter(name="page", type=int),
            OpenApiParameter(name="page_size", type=int),
        ],
        responses={200: InvoiceSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Billing"],
        summary="Generate an invoice",
        request=InvoiceCreateSerializer,
        responses={201: InvoiceSerializer},
    ),
)
class InvoiceListCreateView(PaginationMixin, InvoiceAccessMixin, APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_invoices",),
        "POST": ("can_create_invoices",),
    }

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            InvoiceSerializer,
            context={"request": request},
        )

    def post(self, request):
        serializer = InvoiceCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(
            InvoiceSerializer(
                invoice,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Billing"],
    summary="Get an invoice",
    responses={200: InvoiceSerializer},
)
class InvoiceDetailView(InvoiceAccessMixin, APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_invoices"

    def get(self, request, pk):
        invoice = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(
            InvoiceSerializer(
                invoice,
                context={"request": request},
            ).data
        )


@extend_schema(
    tags=["Billing"],
    summary="Download an invoice PDF",
    responses={(200, "application/pdf"): bytes},
)
class InvoicePDFView(InvoiceAccessMixin, APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_invoices"

    def get(self, request, pk):
        invoice = get_object_or_404(self.get_queryset(), pk=pk)
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"Hospital Invoice #{invoice.pk}", styles["Title"]),
            Spacer(1, 8 * mm),
            Paragraph(
                f"Patient: {invoice.appointment.patient.user.email}",
                styles["Normal"],
            ),
            Paragraph(
                f"Doctor: {invoice.appointment.doctor.user.email}",
                styles["Normal"],
            ),
            Paragraph(
                f"Appointment: {invoice.appointment.appointment_date}",
                styles["Normal"],
            ),
            Paragraph(f"Status: {invoice.get_status_display()}", styles["Normal"]),
            Paragraph(f"Amount paid: {invoice.amount_paid:.2f}", styles["Normal"]),
            Paragraph(f"Balance: {invoice.balance:.2f}", styles["Normal"]),
            Spacer(1, 6 * mm),
        ]
        table_data = [
            ["Description", "Quantity", "Unit price", "Total"],
            *[
                [
                    item.description,
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.total:.2f}",
                ]
                for item in invoice.items.all()
            ],
            ["", "", "Grand total", f"{invoice.total_amount:.2f}"],
        ]
        table = Table(
            table_data,
            colWidths=[85 * mm, 25 * mm, 30 * mm, 30 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                    ("TOPPADDING", (0, 0), (-1, 0), 7),
                ]
            )
        )
        story.append(table)
        document.build(story)
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"invoice-{invoice.pk}.pdf",
            content_type="application/pdf",
        )



@extend_schema_view(
    get=extend_schema(
        tags=["Billing"],
        summary="List invoice payments",
        responses={200: InvoicePaymentSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Billing"],
        summary="Record an invoice payment",
        request=InvoicePaymentCreateSerializer,
        responses={201: InvoicePaymentSerializer},
    ),
)
class InvoicePaymentListCreateView(InvoiceAccessMixin, APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_invoices",),
        "POST": ("can_record_invoice_payments",),
    }

    def get_invoice(self, pk):
        if self.request.method == "POST":
            queryset = Invoice.objects.select_related(
                "appointment__patient__user",
                "appointment__doctor__user",
            ).prefetch_related("items", "payments__recorded_by")
        else:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk):
        invoice = self.get_invoice(pk)
        return Response(
            InvoicePaymentSerializer(
                invoice.payments.select_related("recorded_by"),
                many=True,
            ).data
        )

    def post(self, request, pk):
        invoice = self.get_invoice(pk)
        serializer = InvoicePaymentCreateSerializer(
            data=request.data,
            context={"request": request, "invoice": invoice},
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(
            InvoicePaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )