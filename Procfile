release: python manage.py migrate && python manage.py seed_permissions && python manage.py collectstatic --noinput
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --access-logfile -
worker: celery -A config worker --loglevel=info
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler