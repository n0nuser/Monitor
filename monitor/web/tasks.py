from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from django_rq import job, get_scheduler
from monitor.settings import DEFAULT_FROM_EMAIL
from web.models import AgentConfig, Metric, Agent
import datetime
import logging

logger = logging.getLogger(__name__)
scheduler = get_scheduler()

@job
def remove_old():
    metrics = Metric.objects.all()
    threshold = 15 # days
    for each in metrics:
        if each.created < datetime.now() - datetime.timedelta(days=threshold):
            each.delete()

@job
def check_status():
    agents = Agent.objects.all()
    
    for agent in agents:
        config = AgentConfig.objects.get(agent=agent)
        post_interval = config.metrics_post_interval
        bad_time_interval = config.bad_time_interval
        warning_time_interval = config.warning_time_interval
        
        bad_time_interval = datetime.now() - datetime.timedelta(minutes=bad_time_interval)
        warning_time_interval = datetime.now() - datetime.timedelta(minutes=warning_time_interval)
        
        normal_metric_count_in_bad_interval = (bad_time_interval*60)/post_interval
        normal_metric_count_in_warning_interval = (warning_time_interval*60)/post_interval
        metrics = Metric.objects.filter(agent=agent)
        real_metric_count_in_bad_interval = metrics(created__lte=bad_time_interval).count()
        real_metric_count_in_warning_interval = metrics(created__lte=warning_time_interval).count()
        
        if real_metric_count_in_bad_interval < normal_metric_count_in_bad_interval:
            agent.status = 'BA'
        elif real_metric_count_in_warning_interval < normal_metric_count_in_warning_interval:
            agent.status = 'WR'
        elif real_metric_count_in_warning_interval == 0:
            agent.status = 'BA'
        else:
            agent.status = 'OK'
        


@job
def send_email_task(to, subject, message):
    logger.info(f"from={DEFAULT_FROM_EMAIL}, {to=}, {subject=}, {message=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [DEFAULT_FROM_EMAIL])
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)

# Delete any existing jobs in the scheduler when the app starts up
'''
for job in scheduler.get_jobs():
    job.delete()
'''

scheduler.cron(
    "0 1 * * *",                # A cron string (e.g. "0 0 * * 0")
    func=remove_old,                  # Function to be queued
    repeat=None,                  # Repeat this number of times (None means repeat forever)
    queue_name="default",      # In which queue the job should be put in
    use_local_timezone=False    # Interpret hours in the local timezone
)

scheduler.schedule(
    scheduled_time=datetime.utcnow(), # Time for first execution, in UTC timezone
    func=remove_old,                     # Function to be queued
    interval=30*60,                   # Time before the function is called again, in seconds
    repeat=None,                     # Repeat this number of times (None means repeat forever)
)