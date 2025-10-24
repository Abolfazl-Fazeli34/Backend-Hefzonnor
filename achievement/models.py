from django.db import models
from account.models import Profile

class TimeStampedBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Medal(TimeStampedBaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_image = models.ImageField(upload_to='medal_badges/', null=True, blank=True)

    def __str__(self):
        return self.name


class UserMedal(TimeStampedBaseModel):
    user = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='user_medals')
    medal = models.ForeignKey(Medal, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('user', 'medal')