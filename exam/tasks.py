from celery import shared_task
from django.db.models import Q
from django.utils.timezone import now

from .models import Quiz


@shared_task
def activate_due_quizzes():
    count = Quiz.objects.filter(
        is_active=False,
        quiz_start_datetime__lte=now()
    ).update(is_active=True)
    return f"{count} quizzes activated."


@shared_task
def deactivate_due_quizzes():
    count = (Quiz.objects
             .filter(is_active=True, )
             .filter(Q(quiz_start_datetime__gte=now()) | Q(quiz_end_datetime__lte=now()))
             .update(is_active=False))
    return f"{count} quizzes deactivated."
