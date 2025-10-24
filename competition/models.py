from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from account.models import Profile
from competition.choices import PromotionStatusChoices, WeekStatusChoices


class TimeStampedBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class League(TimeStampedBaseModel):
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField()
    promote_rate = models.DecimalField(decimal_places=2, max_digits=3, validators=[MaxValueValidator(0.99), MinValueValidator(0.01)])
    demote_rate = models.DecimalField(decimal_places=2, max_digits=3, validators=[MaxValueValidator(0.99), MinValueValidator(0.01)])
    promotion_minimum_score = models.PositiveIntegerField()
    demotion_penalty = models.PositiveIntegerField()
    target_division_size = models.PositiveIntegerField()
    max_division_size = models.PositiveIntegerField()
    min_division_size = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Week(TimeStampedBaseModel):
    year = models.IntegerField()
    week_number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=WeekStatusChoices.choices, default=WeekStatusChoices.UPCOMING)

    class Meta:
        unique_together = ('year', 'week_number')


class Division(TimeStampedBaseModel):
    league = models.ForeignKey(League, on_delete=models.PROTECT)
    week = models.ForeignKey(Week, on_delete=models.PROTECT)
    size = models.PositiveIntegerField()


class DivisionMembership(TimeStampedBaseModel):
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='memberships')
    user = models.ForeignKey('account.Profile', on_delete=models.PROTECT, related_name='user_division_memberships')
    weekly_score = models.PositiveIntegerField(default=0)
    rank_in_division = models.PositiveIntegerField(null=True)
    promotion_status = models.CharField(max_length=20, choices=PromotionStatusChoices.choices, null=True)

    class Meta:
        unique_together = ('user', 'division')