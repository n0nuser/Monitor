# docker-compose up --build
docker-compose up -d --build
docker exec django-monitor-uvicorn python3 manage.py collectstatic --no-input
# docker exec django-monitor-uvicorn python3 manage.py compress
docker exec django-monitor-uvicorn python3 manage.py createcachetable
docker exec django-monitor-uvicorn python3 manage.py migrate --noinput
