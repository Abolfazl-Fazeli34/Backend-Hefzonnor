from django.utils import timezone

from competition.models import Week
from competition.choices import WeekStatusChoices
import jdatetime
from datetime import timedelta

class WeekService:
    @staticmethod
    def end_current_week(week):
        """Mark current week as finished"""
        week.status = WeekStatusChoices.PASSED
        week.save()

    @staticmethod
    def create_new_week(previous_week : Week = None):
        """Create the next week. If previous_week is given and passed, continue from it, otherwise bootstrap."""
        if previous_week:
            if previous_week.status in (WeekStatusChoices.ACTIVE, WeekStatusChoices.UPCOMING):
                raise Exception('Already an active or upcoming week exists')

            previous_week_end_date = previous_week.end_date
            today_year = jdatetime.date.today().year
            if today_year == previous_week.year:
                week_number, year = previous_week.week_number + 1, previous_week.year
            else:
                week_number, year = 1, today_year

            start_date = previous_week_end_date + timedelta(days=1)
        else:
            today = timezone.now().date()
            week_number, year = 1, jdatetime.date.today().year
            start_date = today

        return Week.objects.create(
            week_number=week_number,
            year=year,
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            status=WeekStatusChoices.UPCOMING
        )
