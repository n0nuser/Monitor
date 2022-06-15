echo "Updating requirements.txt with pyproject.toml"
poetry export -f requirements.txt --output requirements.txt --without-hashes

echo "Docker-Compose Build"
docker-compose build
echo "Docker-Compose Deploy"
docker-compose up -d