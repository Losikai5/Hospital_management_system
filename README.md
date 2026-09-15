# Hospital Management System

A full-stack hospital management platform built with Django REST Framework and Next.js. It supports patient care, staff onboarding, appointment scheduling, medical records, pharmacy operations, invoicing, payments, notifications, audit trails, and database-driven role-based access control.

## Main features

- Custom `AbstractBaseUser` authentication using email addresses
- Database-driven roles and permissions, independent of Django's permission mixin
- Patient self-registration with an automatically created patient profile
- Secure staff invitations for doctors, receptionists, pharmacists, managers, and other roles
- Doctor onboarding and self-managed professional profiles
- Doctor schedules with fixed-duration appointment slots
- Appointment booking, confirmation, cancellation, completion, and slot reuse
- Medical records tied to completed appointments
- Medicine inventory, prescriptions, dispensing, restocking, and low-stock handling
- Server-calculated invoices with downloadable PDF receipts
- Partial and full invoice payments with an automatically derived payment status
- Email notifications and Celery background tasks
- Immutable audit records for mutating API operations
- Next.js dashboard with permission-aware navigation and actions
- JWT authentication stored in secure HttpOnly cookies by the Next.js proxy
- OpenAPI, Swagger UI, and ReDoc documentation

## Technology stack

### Backend

- Python 3.12+
- Django 6
- Django REST Framework
- PostgreSQL
- Simple JWT
- Celery and Celery Beat
- Redis
- drf-spectacular
- ReportLab
- WhiteNoise and Gunicorn for production

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- React Hook Form and Zod
- Motion and Huge Icons

## Project structure

```text
hospital_management_system/
├── apps/
│   ├── appointments/       Appointment booking and lifecycle
│   ├── audit/              Immutable audit trail
│   ├── billing/            Invoices, invoice items, payments and PDFs
│   ├── core/               Shared permissions, schemas and health check
│   ├── doctors/            Doctor profiles and schedules
│   ├── medical_records/    Clinical records
│   ├── notifications/      Email tasks, triggers and delivery records
│   ├── patients/           Patient profiles and staff patient management
│   ├── pharmacy/           Medicines, prescriptions and stock workflows
│   └── users/              Accounts, roles, permissions and invitations
├── config/                 Django, Celery, URL and deployment configuration
├── frontend/               Next.js web application
├── .env.example            Backend environment template
├── DEPLOYMENT.md           Production deployment instructions
├── Procfile                Web, worker, Beat and release processes
└── requirements.txt        Python dependencies
```

All active REST endpoints use explicit DRF `APIView` classes.

OpenAPI annotations are intentionally limited to information consumed by frontend developers and generated clients: endpoint tags, concise summaries, request and response serializers, query parameters, status codes, and special content types.

## Access-control design

Authorization is stored in the application database:

```text
CustomUser → Role → RolePermission → Permission
```

Roles are descriptive groupings such as `PATIENT`, `DOCTOR`, `RECEPTIONIST`, `PHARMACIST`, `MANAGER`, and `ADMIN`. Permissions are capability codes such as `can_create_appointments` and `can_dispense_prescriptions`.

The API declares the capability required for an operation. `HasCustomPermission` resolves that capability against the authenticated user's active role and permissions. This allows permission assignments to change in the database without rewriting role checks throughout the backend.

Initial roles and permissions are maintained in:

- `apps/users/fixtures/role.json`
- `apps/users/fixtures/permission.json`
- `apps/users/fixtures/role_permission.json`

They are loaded idempotently with:

```bash
python manage.py seed_permissions
```

## Local setup

### 1. Clone and create the Python environment

```bash
git clone https://github.com/Losikai5/Hospital_management_system.git
cd Hospital_management_system
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Activate it on Linux or macOS:

```bash
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure PostgreSQL and environment variables

Create a PostgreSQL database and copy the backend environment template:

```powershell
Copy-Item .env.example .env
```

On Linux or macOS:

```bash
cp .env.example .env
```

Update `.env` with local database, email, Redis, frontend, and security values. Never commit `.env` or real passwords/API keys.

For local development, use values similar to:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_PORT=5432
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
```

### 3. Prepare the database

```bash
python manage.py migrate
python manage.py seed_permissions
python manage.py createsuperuser
```

Run the API:

```bash
python manage.py runserver
```

The API is available at `http://localhost:8000`.

### 4. Start Redis and background jobs

Start a local Redis service, then open separate terminals:

```bash
celery -A config worker --loglevel=info
```

```bash
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Run only one Celery Beat process.

### 5. Configure and run the frontend

```bash
cd frontend
npm install
```

Copy the frontend environment template:

```powershell
Copy-Item .env.example .env.local
```

Set the server-only backend URL:

```env
BACKEND_API_BASE_URL=http://localhost:8000/api/v1
```

Do not rename it to `NEXT_PUBLIC_BACKEND_API_BASE_URL`. The value must remain server-only so browser requests pass through the secure Next.js proxy.

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Authentication and onboarding flows

### Patient

1. The patient registers publicly.
2. The system assigns the `PATIENT` role.
3. A `PatientProfile` is created automatically.
4. The patient can complete personal and medical information, browse doctors, book appointments, view medical records, prescriptions, and invoices.

### Staff member

1. An authorized staff member enters the invitee's email and role.
2. The system creates an inactive user with no usable password.
3. A signed, expiring invitation link is emailed.
4. The invitee accepts the invitation and chooses their password.
5. The account becomes active and inherits permissions from the invited role.

### Doctor

After accepting an invitation, a doctor completes their professional profile and manages their own schedules. Appointment endpoints use the authenticated doctor's profile rather than accepting a doctor ID for ownership-sensitive operations.

## Important API routes

| Area | Base route |
| --- | --- |
| Health check | `/api/v1/health/` |
| Authentication | `/api/v1/auth/` |
| Staff invitations and roles | `/api/v1/staff/` |
| Patients | `/api/v1/patients/` |
| Doctors and schedules | `/api/v1/doctors/` |
| Appointments and slots | `/api/v1/appointments/` |
| Medical records | `/api/v1/medical-records/` |
| Medicines and prescriptions | `/api/v1/pharmacy/` |
| Invoices and payments | `/api/v1/billing/` |
| Audit logs | `/api/v1/audit/` |
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI schema | `/api/schema/` |

## Billing workflow

Invoices can only be generated for completed appointments. Totals are calculated on the server from the doctor's consultation fee and dispensed prescription items.

Payments support:

- Cash
- Card
- Mobile money
- Insurance
- Bank transfer

The invoice status is derived from its totals:

- `UNPAID`: no payment recorded
- `PARTIAL`: some payment recorded and a balance remains
- `PAID`: the full invoice total has been paid

Overpayments, duplicate payment references, and payments on fully paid invoices are rejected. This records payments processed by the hospital; connecting a live payment gateway is a separate provider-specific integration.

## Audit logging

Every `POST`, `PUT`, `PATCH`, and `DELETE` request under `/api/v1/` creates an audit record containing the actor, action, route, response status, request ID, IP address, user agent, resource hints, and timestamp.

Request bodies are deliberately not copied into audit metadata because hospital payloads can contain medical and personal information. Audit logs cannot be changed or deleted through the model or admin interface.

## Testing and validation

Run the backend suite:

```bash
python manage.py test
```

Validate migrations and the API schema:

```bash
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file schema.yml --validate
```

Run Django's production security review:

```bash
python manage.py check --deploy
```

Validate the frontend:

```bash
cd frontend
npm run lint
npm run build
```

The acceptance suite includes the full flow from appointment booking through medical records, prescription dispensing, invoice payment, and audit-log verification.

## Production deployment

This repository intentionally does not use Docker. See [DEPLOYMENT.md](DEPLOYMENT.md) for the web, worker, scheduler, PostgreSQL, Redis, TLS, environment, migration, static-file, health-check, and release-verification setup.

Before deploying:

- Replace every development secret.
- Keep secrets in the hosting provider's secret manager.
- Use managed PostgreSQL and Redis with backups.
- Set `DEBUG=False`.
- Configure HTTPS hostnames and trusted origins.
- Set `BACKEND_API_BASE_URL` on the Next.js server.
- Use durable object storage for uploaded media when running multiple API instances.

## Development history

- [Development progress — 5 August 2026](PROGRESS_2026-08-05.md)

## Security notice

If any SMTP password, database password, signing secret, or API key has appeared in chat, logs, screenshots, or committed history, revoke it and generate a replacement before deployment.