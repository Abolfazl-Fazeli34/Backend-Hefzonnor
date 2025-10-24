from django.db import models


class QuizCategory(models.TextChoices):
    MULTIPLE_CHOICE = 'multiple_choice', 'چهار گزینه‌ای'
    ORDERING = 'ordering', 'چینشی'
    MATCHING = 'matching', 'وصل کردنی'
    TYPING = 'typing', 'تایپی'


class ProvinceChoices(models.TextChoices):
    EAST_AZERBAIJAN = 'east_azerbaijan', 'آذربایجان شرقی'
    WEST_AZERBAIJAN = 'west_azerbaijan', 'آذربایجان غربی'
    ARDABIL = 'ardabil', 'اردبیل'
    ISFAHAN = 'isfahan', 'اصفهان'
    ALBORZ = 'alborz', 'البرز'
    ILAAM = 'ilaam', 'ایلام'
    BUSHEHR = 'bushehr', 'بوشهر'
    TEHRAN = 'tehran', 'تهران'
    CHAHAR_MAHAAL = 'chahar_mahaal', 'چهارمحال و بختیاری'
    SOUTH_KHORASAN = 'south_khorasan', 'خراسان جنوبی'
    RAZAVI_KHORASAN = 'razavi_khorasan', 'خراسان رضوی'
    NORTH_KHORASAN = 'north_khorasan', 'خراسان شمالی'
    KHUZESTAN = 'khuzestan', 'خوزستان'
    ZANJAN = 'zanjan', 'زنجان'
    SEMNAN = 'semnan', 'سمنان'
    SISTAN_BALUCHESTAN = 'sistan_baluchestan', 'سیستان و بلوچستان'
    FARS = 'fars', 'فارس'
    QAZVIN = 'qazvin', 'قزوین'
    QOM = 'qom', 'قم'
    KURDISTAN = 'kurdistan', 'کردستان'
    KERMAN = 'kerman', 'کرمان'
    KERMANSHAH = 'kermanshah', 'کرمانشاه'
    KOHGILUYEH = 'kohgiluyeh', 'کهگیلویه و بویراحمد'
    GOLESTAN = 'golestan', 'گلستان'
    GILAN = 'gilan', 'گیلان'
    LORESTAN = 'lorestan', 'لرستان'
    MAZANDARAN = 'mazandaran', 'مازندران'
    MARKAZI = 'markazi', 'مرکزی'
    HORMOZGAN = 'hormozgan', 'هرمزگان'
    HAMEDAN = 'hamedan', 'همدان'
    YAZD = 'yazd', 'یزد'


class ParticipationStatus(models.TextChoices):
    INCOMPLETE = 'incomplete', 'ناتمام'
    COMPLETED = 'completed', 'کامل شده'
