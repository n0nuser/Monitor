python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate
python manage.py rqworker high default low &
python manage.py rqscheduler &
gunicorn monitor.asgi:application --bind :8000 --workers 4 -k uvicorn.workers.UvicornWorker --log-level debug