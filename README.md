<div id="top"></div>

# Monitor

Computer Science Final Degree Project @ USAL - Web App to manage monitorized hosts

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GPL License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



## Built With

[![Python][Python]][Python-url] [![Poetry][Poetry]][Poetry-url]

[![Django][Django]][Django-url] [![Django REST Framework][DRF]][DRF-url]

[![Docker][Docker]][Docker-url]

[![Redis][Redis]][Redis-url] [![Django RQ][djangorq]][djangorq-url] [![RQ Scheduler][rqscheduler]][rqscheduler-url]

[![Uvicorn][Uvicorn]][Uvicorn-url] [![Nginx][Nginx]][Nginx-url]


<p align="right">(<a href="#top">back to top</a>)</p>


## Architecture

![Architecture][architecture-image]

## Getting Started

A web app that allows to manage agents and get results from them. Django is used for the webpage, while Django REST Framework is used for the REST API.

The webpage will be used by the user to manage its server/computers remotely and get their metrics, as well as send them commands in POST requests to the agents.

> :warning: For agents to receive commands port forwarding to the agents must be done in the router to the port specified in the settings file of the agent.

The REST API will receive the metrics and the alerts from the agents.

### Installation and use

Modify the `.env` file to suit your needs.

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

### Endpoints

* `users`: http://FQDN/api/users/
* `agents`: http://FQDN/api/agents/
* `agent_configs`: http://FQDN/api/agent_configs/
* `metrics`: http://FQDN/api/metrics/
* `alerts`: http://FQDN/api/alerts/
* `alert_emails`: http://FQDN/api/alert_emails/
* `alert_webhooks`: http://FQDN/api/alert_webhooks/

### Authentication

In the web app, the user can log in with the username and password, or with the token (only to the REST API).

This token is assigned automatically to the user when it's registered and can be seen in the user's profile.

### Get the user token

In case you prefer the REST API method, you can get the token with the following command:

```sh
# curl -X POST -d "username=YOUR_USERNAME&password=YOUR_PASSWORD"  http://SERVER:PORT/api-token-auth/
curl -X POST -d "username=admin&password=admin"  http://localhost:8000/api-token-auth/
```

### Authenticate with Token

```sh
# curl http://localhost:8000/api/users/ -H 'Authorization: Token YOUR_TOKEN'
curl http://localhost:8000/api/users/ -H 'Authorization: Token abe47ef7170a53a0f9670c8b2b1081d8ace7d3e5'
```

<!-- ROADMAP -->
## Roadmap

Check the [Roadmap here](https://github.com/n0nuser/Monitor/issues/11).

See the [open issues](https://github.com/n0nuser/Monitor/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the GPL-3.0 License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Pablo González Rubio - [@n0nuser_](https://twitter.com/n0nuser_) - gonzrubio.pablo@gmail.com

Project Link: [https://github.com/n0nuser/Monitor-Agent](https://github.com/n0nuser/Monitor-Agent)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->

[architecture-image]: https://i.imgur.com/c1royxO.png

[contributors-shield]: https://img.shields.io/github/contributors/n0nuser/monitor?style=for-the-badge
[contributors-url]: https://github.com/n0nuser/Monitor/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/n0nuser/monitor?style=for-the-badge
[forks-url]: https://github.com/n0nuser/Monitor/network/members
[stars-shield]: https://img.shields.io/github/stars/n0nuser/monitor?style=for-the-badge
[stars-url]: https://github.com/n0nuser/Monitor/stargazers
[issues-shield]: https://img.shields.io/github/issues/n0nuser/monitor?style=for-the-badge
[issues-url]: https://github.com/n0nuser/Monitor/issues
[license-shield]: https://img.shields.io/github/license/n0nuser/monitor?style=for-the-badge
[license-url]: https://github.com/n0nuser/Monitor-Agent/blob/main/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/nonuser

[Python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org/
[Poetry]: https://img.shields.io/badge/Poetry-3670A0?style=for-the-badge&logo=poetry&logoColor=ffdd54
[Poetry-url]: https://python-poetry.org/
[Django]: https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white
[Django-url]: https://www.djangoproject.com/
[DRF]: https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray
[DRF-url]: https://www.django-rest-framework.org/
[Docker]: https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
[Redis]: https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white
[Redis-url]: https://redis.io/
[djangorq]: https://img.shields.io/badge/django%20rq-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white
[djangorq-url]: https://github.com/rq/django-rq
[rqscheduler]: https://img.shields.io/badge/rq%20scheduler-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white
[rqscheduler-url]: https://github.com/rq/rq-scheduler
[Uvicorn]: https://img.shields.io/badge/uvicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white
[Uvicorn-url]: https://www.uvicorn.org/
[Nginx]: https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white
[Nginx-url]: https://www.nginx.com/
