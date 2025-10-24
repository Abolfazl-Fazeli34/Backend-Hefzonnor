from account.managers import UserManager
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from exam.choices import ProvinceChoices
from django.utils import timezone
from django.conf import settings
import os
from PIL import Image
import re


def avatar_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"avatar.{ext}"
    return os.path.join('avatars', str(instance.user.id), filename)

PHONE_REGEX = re.compile(r'^\+?\d{10,15}$')  


class TimeStampedBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractBaseUser, TimeStampedBaseModel, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True) 
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        if hasattr(self, 'profile') and self.profile.first_name:
            return f"{self.profile.first_name} {self.profile.last_name or ''}"
        return self.phone_number


class Profile(TimeStampedBaseModel):
    FEMALE = 'F'
    MALE = 'M'
    GENDER_CHOICES = [
        (FEMALE, 'Female'),
        (MALE, 'Male'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    province = models.CharField(choices=ProvinceChoices, max_length=100, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1, null=True, blank=True)
    total_score = models.PositiveIntegerField(default=0)
    diamonds_count = models.PositiveIntegerField(default=0)
    level = models.ForeignKey('Level', on_delete=models.PROTECT, null=True)
    current_league = models.ForeignKey('competition.League', on_delete=models.PROTECT, null=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True, default='avatars/default.png')
    avatar_thumbnail = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)

    @property
    def is_complete(self):
        return bool(self.age and self.province and self.gender)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            if self.avatar and os.path.isfile(self.avatar.path):
                img = Image.open(self.avatar.path)
                max_size = (800, 800)
                img.thumbnail(max_size)
                img.save(self.avatar.path, quality=85)

                thumb_size = (150, 150)
                img_thumb = Image.open(self.avatar.path)
                img_thumb.thumbnail(thumb_size)
                thumb_filename = os.path.join(os.path.dirname(self.avatar.path),
                                              'thumb_' + os.path.basename(self.avatar.path))
                img_thumb.save(thumb_filename, quality=85)
                rel_path = os.path.relpath(thumb_filename, settings.MEDIA_ROOT)
                self.avatar_thumbnail.name = rel_path.replace('\\', '/')
                super().save(update_fields=['avatar_thumbnail'])
        except Exception:
            pass


class PhoneVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='phone_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"PhoneVerification({self.user.phone_number}) - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class Level(TimeStampedBaseModel):
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(unique=True)
    min_score = models.PositiveIntegerField()
