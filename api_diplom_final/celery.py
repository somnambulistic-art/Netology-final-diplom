import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_django.settings')
app = Celery('api_diplom_final')
app.config_from_object('django.conf:settings', namespace='CELERY')

# загрузка tasks.py в приложение django
app.autodiscover_tasks()



@app.task
def send_email(some_data):
    return
# TODO:добавить задачу с отправкой почты
