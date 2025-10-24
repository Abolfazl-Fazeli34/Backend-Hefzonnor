from django.db import models


class QariType(models.TextChoices):
    TARTIL = 'tartil', 'ترتیل'
    TAJVID = 'tajvid', 'تجوید'
    TAHDIR = 'tahdir', 'تحدیر'
    TUTORIAL = 'tutorial', 'آموزشی'
    TRANSLATION = 'translation', 'ترجمه'
    WORD = 'word', 'کلمه'
    INTERSECTION = 'intersection', 'تقطیع'
    WORDAUDIO = 'wordAudio', 'صوت کلمه'
