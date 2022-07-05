import logging

import requests
from django.core.mail import BadHeaderError, send_mail
from django.template import loader
from django.utils import timezone as datetime
from django_rq import get_scheduler, job
from monitor.settings import EMAIL_HOST_USER
from django.db.models.query import QuerySet

import web.models as models

logger = logging.getLogger(__name__)
scheduler = get_scheduler("default")


@job
def remove_old(threshold: int = 15):
    """Removes metrics with a timestamp older than 15 days

    Args:
        threshold (int, optional): Maximum number of days. Defaults to 15.
    """
    metrics = models.Metric.objects.all()
    for each in metrics:
        if each.created < datetime.now() - datetime.timedelta(days=threshold):
            each.delete()


def verify_status(
    agent, real_metric_count, real_alert_count, normal_metric_count, interval, post_interval, quotient, status
) -> bool:
    """Checks status of agent and alerts if necessary

    Args:
        agent (Agent): Agent to check
        real_metric_count (int): Number of metrics in the database
        real_alert_count (int): Number of alerts in the database
        normal_metric_count (int): Number of metrics that should be in the database
        interval (int): Interval of time when an status is tested
        post_interval (int): Interval between metric POSTs
        quotient (float): Maximum percentage of alerts per number of metrics
        status (str): Status to set to agent

    Returns:
        bool: True if agent has problems, False otherwise
    """
    if real_metric_count < normal_metric_count:
        agent.status = status
        agent.status_reason = (
            f"Agent received {real_metric_count} of {normal_metric_count} metrics in the last {interval} minutes."
            + f" Post interval is {post_interval} seconds."
        )
        return True
    elif real_metric_count == 0:
        agent.status = status
        agent.status_reason = (
            f"Agent received no metrics in {interval} minutes."
            + f" Should have received at least {normal_metric_count} metrics"
            + f" due to the post interval being {post_interval} seconds."
        )
        return True
    elif real_alert_count and (real_alert_count >= quotient * normal_metric_count):
        agent.status = status
        agent.status_reason = (
            f"Agent received {real_alert_count} alerts in {interval} minutes."
            + f" It should be less than {quotient * normal_metric_count} alerts."
        )
        return True
    else:
        agent.status = "OK"
        agent.status_reason = ""
        return False


def evaluate_status(quotient_alert: float, agent: models.Agent, config: models.AgentConfig, metrics: QuerySet) -> str:
    """Evaluates the status of an agent

    Args:
        quotient_alert (float): Maximum percentage of alerts per number of metrics
        agent (models.Agent): Agent to evaluate
        config (models.AgentConfig): Configuration of the agent
        metrics (QuerySet): All the metrics of the agent

    Returns:
        str: Status of the agent
    """
    post_interval = config.metrics_post_interval
    bad_time_interval = config.bad_time_interval
    normal_metric_count_in_bad_interval = (bad_time_interval * 60) / post_interval
    bad_time_interval_datetime = datetime.datetime.now() - datetime.timedelta(minutes=bad_time_interval)
    real_metric_count_in_bad_interval = metrics.filter(created__lte=bad_time_interval_datetime).count()

    warning_time_interval = config.warning_time_interval
    normal_metric_count_in_warning_interval = (warning_time_interval * 60) / post_interval
    warning_time_interval_datetime = datetime.datetime.now() - datetime.timedelta(minutes=warning_time_interval)
    real_metric_count_in_warning_interval = metrics.filter(created__lte=warning_time_interval_datetime).count()

    alerts = models.Alert.objects.filter(agent=agent)
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
        status="WR",
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
            status="BA",
        )
    end_status = agent.status
    return start_status, end_status


@job
def check_status():
    """Checks the status of all agents, modifies the status of the agent and sends an email/webhook if necessary."""
    agents = models.Agent.objects.all()

    if not agents:
        logger.info("No agents found")
        return None

    quotient_alert = 1 / 3

    for agent in agents:
        config = models.AgentConfig.objects.get(agent=agent)
        metrics = models.Metric.objects.filter(agent=agent)
        if metrics.count() == 0:
            agent.status = "BA"
            agent.status_reason = "Host hasn't sent any metrics yet."
            continue

        start_status, end_status = evaluate_status(quotient_alert, agent, config, metrics)

        if start_status == end_status == "OK":
            agent.status = "OK"
            agent.status_reason = ""
        else:
            end_status = "Warning" if end_status == "WR" else "Bad"
            html_context = {
                "year": datetime.datetime.now().year,
                "company": "Monitor",
                "address": "Salamanca, Spain",
                "url": "https://nonuser.es",
                "header": f"{end_status} status on {agent.name}",
                "message": agent.status_reason,
            }
            html_content = loader.render_to_string("email/default.html", html_context)

            emails = list(models.AlertEmail.objects.filter(user=agent.user).values_list("email", flat=True))

            send_email_task(
                to=emails,
                subject="Alert on " + agent.name + " (" + end_status + ")",
                html_message=html_content,
            )

            for each in models.AlertWebhook.objects.filter(user=agent.user):
                message = f"{datetime.datetime.now()} | {agent.name} - **{end_status.upper()}**: {agent.status_reason}"
                requests.post(each.webhook, json={"content": message})

        agent.save()


@job("default", retry=5)
def send_email_task(to: list, subject: str, message: str = "", html_message: str = "") -> None:
    """Sends an email with the given parameters.

    Args:
        to (list): List of email directions to send the email to
        subject (str): Subject of the email
        message (str, optional): TXT message to send. Defaults to "".
        html_message (str, optional): HTML message to send. Defaults to "".
    """
    logger.info(f"from={EMAIL_HOST_USER}, {to=}, {subject=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, EMAIL_HOST_USER, to, html_message=html_message)
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)


def startup_scheduling():
    """Function for the RQ scheduler to call at startup. Should be called only once."""
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
