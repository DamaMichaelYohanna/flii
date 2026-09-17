web: gunicorn config.wsgi:application --workers 3 --timeout 120
worker: celery -A config worker --loglevel=info
