# Monitor

A web app that allows to manage agents and get results from them. Django is used for the webpage, while Django REST Framework is used for the REST API.

The webpage will be used by the user to manage its server/computers remotely and get their metrics, as well as send them commands in POST requests to the agents.

> :warning: For agents to receive commands port forwarding to the agents must be done in the router to the port specified in the settings file of the agent.

The REST API will receive the metrics and the alerts from the agents.

## Roadmap

For Roadmap the [this issue](https://github.com/n0nuser/Monitor/issues/2).

## Installation and use

Install dependencies and enter the Poetry virtual environment:

```shell
poetry install
poetry shell
```

> If you don't have Poetry: `pip3 install poetry`

Inside `monitor/` run the Django web:

```python
python3 manage.py makemigrations web
python3 manage.py migrate
python3 manage.py createsuperuser --email admin@example.com --username admin
python3 manage.py runserver
```

## Get user token

```
# curl -X POST -d "username=YOUR_EMAIL&password=YOUR_PASSWORD"  http://localhost:8000/api-token-auth/
curl -X POST -d "username=admin@monitor.tfg&password=admin"  http://localhost:8000/api-token-auth/
```

## Auth with Token

```
# curl http://localhost:8000/api/users/ -H 'Authorization: Token YOUR_TOKEN'
curl http://localhost:8000/api/users/ -H 'Authorization: Token abe47ef7170a53a0f9670c8b2b1081d8ace7d3e5'
```
