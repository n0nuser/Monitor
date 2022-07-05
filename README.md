# Monitor

A web app that allows to manage agents and get results from them. Django is used for the webpage, while Django REST Framework is used for the REST API.

The webpage will be used by the user to manage its server/computers remotely and get their metrics, as well as send them commands in POST requests to the agents.

> :warning: For agents to receive commands port forwarding to the agents must be done in the router to the port specified in the settings file of the agent.

The REST API will receive the metrics and the alerts from the agents.

## Installation and use

Modify the `.env` file to your needs.

```env
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.0.28
DEBUG=False
DJANGO_SUPERUSER_EMAIL=admin@monitor.tfg
DJANGO_SUPERUSER_PASSWORD=admin
DJANGO_SUPERUSER_USERNAME=admin
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_PASSWORD=password
EMAIL_HOST_USER=account@gmail.com
EMAIL_PORT=587
PORT=8000
POSTGRES_NAME=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_USER=postgres
SECRET_KEY=myDummySecretKey
SERVER=YOUR FQDN
```

Execute the `docker_compose_up.sh` file to deploy the containers.

```sh
chmod +x docker_compose_up.sh
./docker_compose_up.sh
```

## Authentication

In the web app, the user can log in with the username and password, or with the token (only to the REST API).

This token is assigned automatically to the user when it's registered and can be seen in the user's profile.

### Get user token

In case you prefer the REST API method, you can get the token with the following command:

```sh
# curl -X POST -d "username=YOUR_USERNAME&password=YOUR_PASSWORD"  http://SERVER:PORT/api-token-auth/
curl -X POST -d "username=admin&password=admin"  http://localhost:8000/api-token-auth/
```

### Auth with Token

```sh
# curl http://localhost:8000/api/users/ -H 'Authorization: Token YOUR_TOKEN'
curl http://localhost:8000/api/users/ -H 'Authorization: Token abe47ef7170a53a0f9670c8b2b1081d8ace7d3e5'
```
