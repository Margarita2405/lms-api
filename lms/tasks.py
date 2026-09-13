from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from lms.models import Course


@shared_task
def send_course_update_email(course_id, user_emails):
    course = Course.objects.get(id=course_id)
    # Проверяем, обновлялся ли курс за последние 4 часа
    if course.updated_at > timezone.now() - timedelta(hours=4):
        subject = f'Курс "{course.title}" обновлён'
        message = 'В курс добавлены новые материалы. Зайдите в приложение.'
        for email in user_emails:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
