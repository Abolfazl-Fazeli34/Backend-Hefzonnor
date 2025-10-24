from django.db import models


class WeekStatusChoices(models.TextChoices):
    PASSED = 'passed', 'گذشته'
    ACTIVE = 'active', 'فعال'
    UPCOMING = 'upcoming', 'آینده'

class PromotionStatusChoices(models.TextChoices):
    PROMOTED = 'promoted', 'ارتقا یافته'
    DEMOTED = 'demoted', 'تنزل یافته'
    STAYED = 'stayed', 'مانده'
