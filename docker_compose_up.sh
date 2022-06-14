echo "Docker-Compose Build"
docker-compose build
echo "Docker-Compose Deploy"
docker-compose up -d

USER=admin
PASS=admin
EMAIL=admin@monitor.tfg
echo "from web.models import CustomUser; User.objects.create_superuser('$USER', '$EMAIL', '$PASS')" | docker exec django-monitor-uvicorn python3 manage.py shell
