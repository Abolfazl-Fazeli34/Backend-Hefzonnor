from django.db import models

class TransactionTypeChoices(models.TextChoices):
    Deduction = "Deduction", "کسر"
    Increment = "Increment", "افزایش"


class TransactionReasonChoices(models.TextChoices):
    REWARD = "Reward", "چایزه"
    PURCHASE = "Purchase", "خرید"
    DEMOTION = "Demotion", "جریمه سقوط"
    PROMOTION = "Promotion", "جایزه صعود"
    ADMIN = "Admin", "ادمین"
    OTHER = "Other", "دیگر"