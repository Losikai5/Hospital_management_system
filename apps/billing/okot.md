# Billing App Flow

Location: `apps/billing/` (Django REST app), consumed by `frontend/src/app/dashboard/billing/page.tsx`.

Mounted at: `api/v1/billing/` (`config/urls.py:38`).

## 1. Data Model (`models.py`)

- **Invoice** (extends `TimeStampModel`)
  - One-to-one with `appointments.Appointment` (`on_delete=PROTECT`).
  - `total_amount`, `amount_paid`, `status` (`UNPAID` / `PARTIAL` / `PAID`).
  - `balance` property = `total_amount - amount_paid`.
- **InvoiceItem**
  - FK to `Invoice` (`related_name="items"`).
  - `description`, `quantity`, `unit_price`, computed `total` (set in `save()`, `editable=False`).
- **InvoicePayment**
  - FK to `Invoice` (`related_name="payments"`, `on_delete=PROTECT`).
  - `amount`, `method` (`CASH`, `CARD`, `MOBILE_MONEY`, `INSURANCE`, `BANK_TRANSFER`),
    unique optional `reference`, `notes`, `recorded_by` (user), `paid_at`.

## 2. Invoice Generation Flow

Entry: `POST /api/v1/billing/` → `InvoiceListCreateView.post` (`views.py:80`).

1. `InvoiceCreateSerializer` receives an `appointment` ID (`serializers.py:110`).
2. Calls `generate_invoice(appointment=...)` (`services.py:11`) inside a transaction:
   - `select_for_update` on the appointment.
   - **Guard:** appointment must be `COMPLETED` (`AppointmentStatus.COMPLETED`); otherwise `ValueError`.
   - **Guard:** reject if an invoice already exists for the appointment.
   - Creates `Invoice`.
   - Adds one `InvoiceItem` "Doctor consultation" from `doctor.consultation_fee`.
   - Adds an `InvoiceItem` per `DISPENSED` prescription tied to the appointment's
     medical record (`PrescriptionStatus.DISPENSED`), using `medicine.unit_cost` × `quantity_prescribed`.
   - Bulk-creates items, sums their totals into `invoice.total_amount`, saves.
   - `IntegrityError` (unique 1:1 constraint) → friendly "invoice already exists" error.

Status starts as `UNPAID`.

## 3. Payment Flow

Entry: `POST /api/v1/billing/<pk>/payments/` → `InvoicePaymentListCreateView.post` (`views.py:238`).

1. `InvoicePaymentCreateSerializer` validates `amount` (≥ 0.01), `method`, optional `reference`/`notes` (`serializers.py:45`).
2. Calls `record_invoice_payment(...)` (`services.py:89`) inside a transaction:
   - `select_for_update` on the invoice.
   - **Guards:** amount > 0; balance > 0 (not already fully paid); amount ≤ outstanding balance.
   - Creates `InvoicePayment` (records `recorded_by`).
   - Increments `amount_paid`; sets status to `PAID` when fully settled, else `PARTIAL`.
   - Duplicate `reference` (`IntegrityError`) → friendly error.

## 4. Read / Access Endpoints

| Method | URL | View | Permission |
|--------|-----|------|------------|
| GET | `/billing/` | `InvoiceListCreateView` | `can_view_invoices` |
| POST | `/billing/` | `InvoiceListCreateView` | `can_create_invoices` |
| GET | `/billing/<pk>/` | `InvoiceDetailView` | `can_view_invoices` |
| GET | `/billing/<pk>/pdf/` | `InvoicePDFView` | `can_view_invoices` |
| GET | `/billing/<pk>/payments/` | `InvoicePaymentListCreateView` | `can_view_invoices` |
| POST | `/billing/<pk>/payments/` | `InvoicePaymentListCreateView` | `can_record_invoice_payments` |

- `InvoiceAccessMixin.get_queryset` (`views.py:33`): users with `can_view_all_invoices`
  see every invoice; everyone else is filtered to invoices where they are the patient.
- `HasCustomPermission` (`apps/core/permissions.py:4`) resolves permissions per HTTP method.
- PDF (`InvoicePDFView`, `views.py:120`) is rendered with ReportLab: header, patient/doctor
  emails, appointment date, status, paid/balance, and the items table.

## 5. Permissions by Role (`apps/users/fixtures/role_permission.json`)

- **ADMIN** – all permissions.
- **RECEPTIONIST** – `can_view_invoices`, `can_view_all_invoices`, `can_create_invoices`, `can_record_invoice_payments` (primary billing operator).
- **PATIENT** – `can_view_invoices` only (sees own invoices, cannot pay via app).
- **DOCTOR / PHARMACIST / MANAGER** – no billing permissions.

## 6. Frontend Flow (`frontend/src/app/dashboard/billing/page.tsx`)

1. Reads permissions via `useAuth().hasPermission` (`canView`, `canCreate`, `canRecordPayment`).
2. Loads invoices (`GET /billing/`) and, if `canCreate`, completed appointments
   (`GET /appointments/?status=COMPLETED`).
3. Filters out appointments that already have an invoice (`invoicedAppointmentIds`) to
   build the candidate dropdown.
4. **Generate invoice**: POSTs `{ appointment: id }`, toasts success, reloads invoices/appointments.
5. Shows stat cards (Invoiced / Paid / Outstanding) and per-invoice status, totals, balance.
6. **Download PDF**: `apiDownload('/billing/<id>/pdf/')`.
7. **Record payment** (only when `canRecordPayment` and status ≠ `PAID`): modal prefilled with
   balance, posts to `/billing/<id>/payments/`, then reloads.
8. Nav link (`frontend/src/lib/nav.ts:27`) is shown if the user has `can_view_invoices` or `can_create_invoices`.

## 7. End-to-End Sequence

```
Appointment COMPLETED
        │
        ▼
[Receptionist] POST /billing/ (appointment id)
        │  generate_invoice()
        │  → Invoice + consultation item + dispensed prescription items
        ▼
Invoice UNPAID  ──GET /billing/──▶ dashboard
        │
        ▼
[Receptionist] POST /billing/<id>/payments/  (amount, method, reference)
        │  record_invoice_payment()
        │  → InvoicePayment, amount_paid += , status = PARTIAL / PAID
        ▼
PARTIAL ──(more payments)──▶ PAID
        │
        ▼
GET /billing/<id>/pdf/  → downloadable invoice
```

## 8. Tests

- `apps/billing/test_payments.py` – partial→full payment status updates, overpayment /
  payment-on-paid rejection, patient view-only access.
- `apps/billing/tests.py` – invoice generation/listing permission coverage.
