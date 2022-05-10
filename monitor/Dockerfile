###########
# BUILDER #
###########

# pull official base image
FROM python:3.9 as builder

# install python dependencies
WORKDIR /home/monitor
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt


#########
# FINAL #
#########
FROM python:3.9-slim

# create the appropriate directories
ENV HOME=/home/monitor
ENV APP_HOME=/home/monitor/monitor
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN groupadd -r monitor && useradd -m -r -g monitor monitor

COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
WORKDIR $APP_HOME
COPY . .
RUN mkdir staticfiles && chown -R monitor:monitor .
USER monitor

# RUN python3 manage.py collectstatic --no-input

EXPOSE 8000

LABEL org.opencontainers.image.title="n0nuser/Monitor"                                 \
      org.opencontainers.image.description="\
A RESTful web application monitoring web application built with Python and Django."    \
      org.opencontainers.image.url="https://n0nuser.es/"                               \
      org.opencontainers.image.source="https://github.com/n0nuser/Monitor"             \
      org.opencontainers.image.authors="Pablo González Rubio (https://n0nuser.es)"     \
      org.opencontainers.image.licenses="GPL-3.0"                                      

CMD ["gunicorn", "monitor.asgi:application", "--bind", ":8000", "--workers", "4", "-k", "uvicorn.workers.UvicornWorker"]