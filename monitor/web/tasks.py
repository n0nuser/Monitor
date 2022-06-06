from django.core.mail import send_mail, BadHeaderError
from django_rq import job, get_scheduler
from monitor.settings import EMAIL_HOST_USER
from web.models import AgentConfig, Metric, Alert, Agent
import datetime
import logging
import requests

logger = logging.getLogger(__name__)
scheduler = get_scheduler("default")


@job
def remove_old():
    metrics = Metric.objects.all()
    threshold = 15  # days
    for each in metrics:
        if each.created < datetime.now() - datetime.timedelta(days=threshold):
            each.delete()


@job
def check_status():
    agents = Agent.objects.all()

    if agents.count() == 0:
        logger.info("No agents found")
        return None

    quotient_alert = 1 / 3

    for agent in agents:
        config = AgentConfig.objects.get(agent=agent)
        post_interval = config.metrics_post_interval

        metrics = Metric.objects.filter(agent=agent)

        normal_metric_count_in_bad_interval = (config.bad_time_interval * 60) / post_interval
        normal_metric_count_in_warning_interval = (config.warning_time_interval * 60) / post_interval

        bad_time_interval = datetime.now() - datetime.timedelta(minutes=config.bad_time_interval)
        warning_time_interval = datetime.now() - datetime.timedelta(minutes=config.warning_time_interval)

        real_metric_count_in_bad_interval = metrics(created__lte=config.bad_time_interval).count()
        real_metric_count_in_warning_interval = metrics(created__lte=config.warning_time_interval).count()

        alerts = Alert.objects.filter(agent=agent)
        real_alert_count_in_bad_interval = alerts(created__lte=bad_time_interval).count()
        real_alert_count_in_warning_interval = alerts(created__lte=warning_time_interval).count()

        if real_metric_count_in_bad_interval < normal_metric_count_in_bad_interval:
            agent.status = "BA"
            agent.status_reason = (
                "Agent received less than "
                + str(normal_metric_count_in_bad_interval)
                + " metrics in "
                + str(config.bad_time_interval)
                + " minutes."
            )
        elif real_metric_count_in_warning_interval == 0:
            agent.status = "BA"
            agent.status_reason = "Agent received no metrics in " + str(config.warning_time_interval) + " minutes."
        elif real_alert_count_in_bad_interval >= quotient_alert * normal_metric_count_in_bad_interval:
            agent.status = "BA"
            agent.status_reason = (
                "Agent received "
                + str(real_alert_count_in_bad_interval)
                + " alerts in "
                + str(config.bad_time_interval)
                + " minutes."
            )
        elif real_metric_count_in_warning_interval < normal_metric_count_in_warning_interval:
            agent.status = "WR"
            agent.status_reason = (
                "Agent received less than "
                + str(normal_metric_count_in_warning_interval)
                + " metrics in "
                + str(config.warning_time_interval)
                + " minutes."
            )
        elif real_alert_count_in_warning_interval >= quotient_alert * normal_metric_count_in_warning_interval:
            agent.status = "WR"
            agent.status_reason = (
                "Agent received "
                + str(real_alert_count_in_warning_interval)
                + " alerts in "
                + str(config.warning_time_interval)
                + " minutes."
            )
        else:
            agent.status = "OK"
            agent.status_reason = ""


@job('default', retry=5)
def send_email_task(to: list, subject: str, message: str, html_message: str):
    logger.info(f"from={EMAIL_HOST_USER}, {to=}, {subject=}, {message=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, EMAIL_HOST_USER, to, html_message=html_message)
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)


@job
def test_post():
    webhook = "https://discord.com/api/webhooks/982937826679205910/qxLyAGZ4AnZAuEbyAaYcVGWBaU8ATu0aqXgrvHN643P8VZDTQYEMANkV_czG9_zZCGJD"
    requests.post(webhook, json={"content": "Prueba ({})".format(datetime.datetime.now())})


def startup_scheduling():
    # Delete any existing jobs in the scheduler when the app starts up
    for each in scheduler.get_jobs():
        each.delete()

    scheduler.schedule(
        scheduled_time=datetime.datetime.now(datetime.timezone.utc),  # Time for first execution, in UTC timezone
        func=remove_old,  # Function to be queued
        interval=30 * 60,  # Time before the function is called again, in seconds
    )

    scheduler.schedule(
        scheduled_time=datetime.datetime.now(datetime.timezone.utc),  # Time for first execution, in UTC timezone
        func=check_status,  # Function to be queued
        interval=10 * 60,  # Time before the function is called again, in seconds
    )

    # scheduler.schedule(
    #     scheduled_time=datetime.datetime.now(datetime.timezone.utc),  # Time for first execution, in UTC timezone
    #     func=test_post,  # Function to be queued
    #     interval=60,  # Time before the function is called again, in seconds
    # )
