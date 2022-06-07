from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.template import loader
from django.utils import timezone as datetime
from django_rq import job, get_scheduler
from monitor.settings import EMAIL_HOST_USER
from web.models import AgentConfig, AlertEmail, AlertWebhook, Metric, Alert, Agent
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


def verify_status(
    agent, real_metric_count, real_alert_count, normal_metric_count, interval, post_interval, quotient, status
):
    if real_metric_count < normal_metric_count:
        agent.status = status
        agent.status_reason = (
            "Agent received "
            + str(real_metric_count)
            + " of "
            + str(int(normal_metric_count))
            + " metrics in "
            + str(interval)
            + " minutes. Post Interval is "
            + str(post_interval)
            + " seconds."
        )
        return True
    elif real_metric_count == 0:
        agent.status = status
        agent.status_reason = (
            "Agent received no metrics in "
            + str(interval)
            + " minutes. Should have received at least "
            + str(normal_metric_count)
            + " metrics due to the post interval being "
            + str(post_interval)
            + " seconds."
        )
        return True
    elif real_alert_count and (real_alert_count >= quotient * normal_metric_count):
        agent.status = status
        agent.status_reason = (
            "Agent received "
            + str(real_alert_count)
            + " alerts in "
            + str(interval)
            + " minutes. It should be less than "
            + str(quotient * normal_metric_count)
            + " alerts."
        )
        return True
    else:
        print("VERIFY STATUS - OK!!!!!!")
        agent.status = "OK"
        agent.status_reason = ""
        return False


@job
def check_status():
    agents = Agent.objects.all()

    if agents.count() == 0:
        logger.info("No agents found")
        return None

    quotient_alert = 1 / 3

    for agent in agents:
        config = AgentConfig.objects.get(agent=agent)
        metrics = Metric.objects.filter(agent=agent)
        if metrics.count() == 0:
            agent.status = "BA"
            agent.status_reason = "Host hasn't sent any metrics yet."
            continue

        post_interval = config.metrics_post_interval
        bad_time_interval = config.bad_time_interval
        normal_metric_count_in_bad_interval = (bad_time_interval * 60) / post_interval
        bad_time_interval_datetime = datetime.datetime.now() - datetime.timedelta(minutes=bad_time_interval)
        real_metric_count_in_bad_interval = metrics.filter(created__lte=bad_time_interval_datetime).count()

        warning_time_interval = config.warning_time_interval
        normal_metric_count_in_warning_interval = (warning_time_interval * 60) / post_interval
        warning_time_interval_datetime = datetime.datetime.now() - datetime.timedelta(minutes=warning_time_interval)
        real_metric_count_in_warning_interval = metrics.filter(created__lte=warning_time_interval_datetime).count()

        alerts = Alert.objects.filter(agent=agent)
        if alerts:
            real_alert_count_in_bad_interval = alerts.filter(created__lte=bad_time_interval_datetime).count()
            real_alert_count_in_warning_interval = alerts.filter(created__lte=warning_time_interval_datetime).count()
        else:
            real_alert_count_in_bad_interval = None
            real_alert_count_in_warning_interval = None

        start_status = agent.status
        warning_status = verify_status(
            agent,
            real_metric_count_in_warning_interval,
            real_alert_count_in_warning_interval,
            normal_metric_count_in_warning_interval,
            warning_time_interval,
            post_interval,
            quotient_alert,
            "WR",
        )
        if warning_status:
            verify_status(
                agent,
                real_metric_count_in_bad_interval,
                real_alert_count_in_bad_interval,
                normal_metric_count_in_bad_interval,
                bad_time_interval,
                post_interval,
                quotient_alert,
                "BA",
            )
        end_status = agent.status

        if start_status != end_status != "OK":
            end_status = "Warning" if end_status == "WR" else "Bad"
            html_content = loader.render_to_string(
                "email/default.html",
                {
                    "year": datetime.datetime.now().year,
                    "company": "Monitor",
                    "address": "Salamanca, Spain",
                    "url": "https://nonuser.es",
                    "header": f"{end_status} status on {agent.name}",
                    "message": agent.status_reason,
                },
            )
            emails = list(AlertEmail.objects.filter(user=agent.user).values_list("email", flat=True))
            print(emails)
            send_email_task(
                to=emails,
                subject="Alert on " + agent.name + " (" + end_status + ")",
                html_message=html_content,
            )
            for each in AlertWebhook.objects.filter(user=agent.user):
                requests.post(
                    each.webhook,
                    json={
                        "content": f"{datetime.datetime.now()} | {agent.name} - **{end_status.upper()}**: {agent.status_reason}"
                    },
                )
        else:
            print("OK!!!!!!")
            agent.status = "OK"
            agent.status_reason = ""

        agent.save()
        print(Agent.objects.get(token=agent.token).__dict__)


@job("default", retry=5)
def send_email_task(to: list, subject: str, message: str = "", html_message: str = ""):
    logger.info(f"from={EMAIL_HOST_USER}, {to=}, {subject=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, EMAIL_HOST_USER, to, html_message=html_message)
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)


@job
def test_post():
    webhook = (
        "https://discord.com/api/webhooks/982937826679205910/"
        + "qxLyAGZ4AnZAuEbyAaYcVGWBaU8ATu0aqXgrvHN643P8VZDTQYEMANkV_czG9_zZCGJD"
    )

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
