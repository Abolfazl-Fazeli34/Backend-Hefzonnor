from django.db import models

from account.models import Profile

from .choices import TransactionTypeChoices, TransactionReasonChoices

class TimeStampedBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DiamondTransaction(TimeStampedBaseModel):
    user = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name="diamond_transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionTypeChoices.choices,
    )
    reason = models.CharField(
        max_length=20,
        choices=TransactionReasonChoices.choices,
        default=TransactionReasonChoices.OTHER,
    )
    amount = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()

    description = models.TextField(blank=True, null=True)

    def __str__(self):
        sign = "+" if self.transaction_type == TransactionTypeChoices.Increment else "-"
        return f"{self.user} {sign}{self.amount} diamonds ({self.get_reason_display()})"

