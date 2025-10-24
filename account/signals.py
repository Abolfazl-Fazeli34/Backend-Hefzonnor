from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import Profile, User, Level


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def update_level(sender, instance, **kwargs):
    if kwargs.get("update_fields") == {"level"}:
        return

    profile = instance

    def _update():
        profile.refresh_from_db(fields=["total_score", "level"])

        new_level = (
            Level.objects
            .filter(min_score__lte=profile.total_score)
            .order_by("-order")
            .first()
        )

        if new_level and profile.level_id != new_level.id:
            profile.level = new_level
            profile.save(update_fields=["level"])

    transaction.on_commit(_update)
