# Production deployment (without Docker)

The system is deployed as four cooperating processes and two managed data services:

- Next.js web process (`frontend`: `npm ci`, `npm run build`, `npm start`)
- Django API process (`web` in `Procfile`)
- Celery worker (`worker` in `Procfile`)
- Celery Beat scheduler (`beat` in `Procfile`)
- Managed PostgreSQL database
- Managed Redis instance

## 1. Rotate credentials

Before deployment, revoke and replace every SMTP app password and AI API key that has ever been pasted into chat, logs, or source. Store replacements only in the hosting provider secret manager.

## 2. Backend environment

Copy the variable names from `.env.example` into the backend service secret manager. Use real HTTPS origins and hostnames. `DEBUG=False`, a new random `SECRET_KEY`, `DB_SSLMODE=require`, and the secure proxy/HTTPS settings are required in production.

Install and build:

```text
pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate
python manage.py seed_permissions
python manage.py collectstatic --noinput
```

Start the web, worker, and beat commands shown in `Procfile`. Configure the platform health check as `/api/v1/health/`.

Run only one Beat process. Multiple workers are safe; multiple Beat schedulers can enqueue duplicate reminders.

## 3. Frontend environment

Set the server-only `BACKEND_API_BASE_URL` to the public backend URL ending in `/api/v1`. Do not create a `NEXT_PUBLIC_` version: the browser must call the same-origin `/api/backend/*` proxy so JWTs remain in secure HttpOnly cookies.

Build and run:

```text
cd frontend
npm ci
npm run lint
npm run build
npm start
```

Set `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` on Django to the final frontend HTTPS origin.

## 4. TLS, DNS, and data

Terminate TLS at the hosting load balancer, force HTTP to HTTPS, point frontend and API DNS records at their services, enable automated PostgreSQL backups, and configure Redis persistence according to the hosting plan. Uploaded media needs durable object storage before horizontally scaling the API; the current filesystem media storage is suitable for a single instance only.

## 5. Release verification

After every release:

1. Check `/api/v1/health/` returns `{"status":"ok"}`.
2. Sign in through the frontend and verify HttpOnly `serenity_access` and `serenity_refresh` cookies are set.
3. Complete one appointment lifecycle, invoice it, record a partial then final payment, and verify audit entries.
4. Confirm a staff invitation and notification email arrives.
5. Check Celery worker and Beat logs, then verify database backups and rollback instructions.