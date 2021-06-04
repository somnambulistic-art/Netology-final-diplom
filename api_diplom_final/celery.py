import os
from api_diplom_final.settings import EMAIL_HOST_USER
from django.core.mail.message import EmailMultiAlternatives
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_django.settings')
app = Celery('api_diplom_final')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task()
def send_email(title, message: str, email: str):
    email_list = list()
    email_list.append(email)
    try:
        message = EmailMultiAlternatives(subject=title, body=message, from_email=EMAIL_HOST_USER, to=email_list)
        message.send()
        return f'Title: {message.subject}, Message:{message.body}'
    except Exception:
        raise Exception
