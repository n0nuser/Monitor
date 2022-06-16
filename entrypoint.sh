echo "Collect static files"
python manage.py collectstatic --no-input

echo "Create database tables"
python manage.py makemigrations web

echo "Apply database migrations"
python manage.py migrate

echo "Create superuser with .env parameters"
python manage.py createsuperuser --no-input

echo "Run Redis Queue Workers"
python manage.py rqworker high default low &

echo "Run Redis Queue Scheduler"
python manage.py rqscheduler &

echo "Launch Gunicorn (Uvicorn)"
gunicorn monitor.asgi:application --bind :8000 --workers 4 -k uvicorn.workers.UvicornWorker --log-level debug
