import logging

from celery import shared_task, chain
from django.db import transaction
from django.utils import timezone

from competition.choices import WeekStatusChoices
from competition.models import Week
from competition.services.division_service import DivisionManagerService
from competition.services.week_service import WeekService

logger = logging.getLogger(__name__)

@shared_task
def closing_the_current_week_and_its_divisions():
    week = Week.objects.filter(status=WeekStatusChoices.ACTIVE, end_date__lte=timezone.now().date()).order_by('-end_date').first()
    if not week:
        logger.warning("No active week found to close.")
        return
    try:
        with transaction.atomic():
            WeekService.end_current_week(week)
            DivisionManagerService.finalize_all_divisions_for_this_week(week)
        logger.info(f"Successfully closed week {week.id} and finalized all divisions.")
    except Exception as e:
        logger.exception(f"Failed closing week {week.id}: {e}")
        raise

@shared_task
def start_new_week_and_create_divisions():
    try:
        with transaction.atomic():
            last_week = Week.objects.all().order_by('-end_date').first()
            new_week = WeekService.create_new_week(last_week)
            DivisionManagerService.create_new_divisions_for_week(new_week)
            new_week.status = WeekStatusChoices.ACTIVE
            new_week.save()
        logger.info(f"Successfully created new week {new_week.id} and divisions.")
    except Exception as e:
        logger.exception(f"Failed starting new week {last_week.id if last_week else ''}: ")