from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from quran.choices import QariType


class Surah(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام سوره')
    arabic_name = models.CharField(max_length=100, verbose_name='نام عربی سوره')
    english_name = models.CharField(max_length=100, verbose_name='نام انگلیسی سوره')
    english_meaning = models.CharField(max_length=100, verbose_name='معنای انگلیسی سوره')

    class Meta:
        verbose_name = 'سوره'
        verbose_name_plural = 'سوره‌ها'

    def __str__(self):
        return self.name


class VerseText(models.Model):
    plain = models.TextField(verbose_name='متن بدون اعراب')  # SearchA
    semi_tashkeel = models.TextField(verbose_name='متن نیم‌اعراب‌گذاری')  # SearchSA
    simple_tashkeel = models.TextField(verbose_name='متن اعراب‌گذاری ساده')  # SearchAE
    full_tashkeel = models.TextField(verbose_name='متن اعراب‌گذاری کامل')  # SearchAE2
    persian_friendly = models.TextField(verbose_name='متن برای جستجو فارسی')  # SearchP
    fuzzy = models.TextField(verbose_name='جستجوی فازی')  # SearchSP

    class Meta:
        verbose_name = 'متن آیه'
        verbose_name_plural = 'متون آیات'


class Verse(models.Model):
    text = models.OneToOneField(VerseText, on_delete=models.CASCADE, verbose_name='متن آیه')
    verse_number = models.IntegerField(verbose_name='شماره آیه')
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره', related_name='verses')
    page_number = models.IntegerField(verbose_name='شماره صفحه')
    section_number = models.IntegerField(verbose_name='شماره حزب')
    juz = models.IntegerField(verbose_name='جزء')

    class Meta:
        verbose_name = 'آیه'
        verbose_name_plural = 'آیات'

    def __str__(self):
        return f'سوره {self.surah.name} - آیه {self.verse_number}'


class Qari(models.Model):

    name = models.CharField(max_length=100, verbose_name='نام قاری')
    path = models.CharField(max_length=200, verbose_name='مسیر فایل')
    link = models.URLField(verbose_name='لینک فایل')
    type = models.CharField(choices=QariType.choices, max_length=100, verbose_name='نوع قاری')
    language = models.CharField(max_length=100, null=True, blank=True, verbose_name='زبان')
    narrator = models.CharField(max_length=100, verbose_name='راوی')

    class Meta:
        verbose_name = 'قاری'
        verbose_name_plural = 'قاری‌ها'

    def __str__(self):
        return self.name

class Word(models.Model):
    arabic_text = models.TextField(verbose_name='متن عربی')
    persian_text = models.TextField(null=True, blank=True, verbose_name='ترجمه فارسی')
    english_text = models.TextField(null=True, blank=True, verbose_name='ترجمه انگلیسی')
    word_number = models.IntegerField(null=True, blank=True, verbose_name='شماره کلمه')
    verse_number = models.IntegerField(null=True, blank=True, verbose_name='شماره آیه')
    verse = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='words', null=True, blank=True, verbose_name='آیه')
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT,related_name='words' , null=True, blank=True, verbose_name='سوره')
    type = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(7)],
        null=True, blank=True,
        verbose_name='نوع کلمه'
    )
    line = models.IntegerField(null=True, blank=True, verbose_name='شماره خط')
    page = models.IntegerField(null=True, blank=True, verbose_name='شماره صفحه')
    code_ski_word = models.IntegerField(null=True, blank=True, verbose_name='کد SKI')
    qari = models.ForeignKey(Qari, on_delete=models.PROTECT, null=True, blank=True)
    aya_index = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='wordsi', null=True, blank=True, verbose_name='ایندکس ایه')
    

    class Meta:
        verbose_name = 'کلمه'
        verbose_name_plural = 'کلمات'

    def __str__(self):
        return self.arabic_text


class Translator(models.Model):
    TRANSLATION_TYPES = [
        ('verse', 'ترجمه آیه'),
        ('word', 'ترجمه کلمه‌ای'),
        ('tafseer', 'تفسیر'),
        ('audio', 'فایل صوتی'),
    ]
    name = models.CharField(max_length=100, verbose_name='نام مترجم / منبع')
    language = models.CharField(max_length=20, default='fa', verbose_name='زبان')
    translation_type = models.CharField(max_length=20, choices=TRANSLATION_TYPES, default='verse', verbose_name='نوع ترجمه')

    class Meta:
        verbose_name = 'مترجم / منبع'
        verbose_name_plural = 'مترجمان / منابع'
    
    def __str__(self):
        return f"{self.name} ({self.get_translation_type_display()})"


class VerseTranslation(models.Model):
    verse = models.ForeignKey(Verse, on_delete=models.PROTECT, verbose_name='آیه', related_name='translations')
    translator = models.ForeignKey(Translator, on_delete=models.PROTECT, verbose_name='مترجم / منبع', related_name='verse_translations')
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره', related_name='translations')
    text = models.TextField(verbose_name='متن ترجمه')

    class Meta:
        verbose_name = 'ترجمه آیه'
        verbose_name_plural = 'ترجمه‌های آیات'
        unique_together = ('surah', 'translator', 'verse')

    def __str__(self):
        return f'{self.translator.name} - سوره {self.surah.name} - آیه {self.verse.verse_number}'

class WordMeaning(models.Model):
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره')
    verse = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='word_meanings', verbose_name='آیه')
    meanings = models.JSONField(verbose_name='ترجمه مخصوص', blank=True, null=True)
    # word_number = models.IntegerField(verbose_name='شماره کلمه')
    # arabic_word = models.CharField(max_length=100, verbose_name='کلمه عربی')
    # persian_word = models.CharField(max_length=100, null=True, blank=True, verbose_name='ترجمه فارسی')
    # english_word = models.CharField(max_length=100, null=True, blank=True, verbose_name='ترجمه انگلیسی')
    translator = models.ForeignKey(Translator, on_delete=models.PROTECT, limit_choices_to={'translation_type': 'word'}, verbose_name='منبع', related_name='word_meaning')
    root_id = models.IntegerField(null=True, blank=True, verbose_name='شناسه ریشه')
    # grammar_form_id = models.IntegerField(null=True, blank=True, verbose_name='فرم گرامری')

    class Meta:
        verbose_name = 'ترجمه کلمه‌ای'
        verbose_name_plural = 'ترجمه‌های کلمه‌ای'
        # unique_together = ('verse', 'translator')

    def __str__(self):
        return f"{self.arabic_word} - {self.persian_word or '-'}"
    

class Root(models.Model):
    root_code = models.CharField(max_length=50, verbose_name='کد ریشه')
    root_arabic = models.CharField(max_length=50, verbose_name='ریشه عربی')
    root_english = models.CharField(max_length=100, verbose_name='ریشه انگلیسی')
    meanings = models.TextField(null=True, blank=True, verbose_name='معانی')
    newroot = models.CharField(max_length=50, null=True, blank=True, verbose_name='ریشه جدید')

    class Meta:
        verbose_name = 'ریشه'
        verbose_name_plural = 'ریشه‌ها'

    def __str__(self):
        return self.root_arabic
    
class VerseRootIndex(models.Model):
    verse = models.ForeignKey(Verse, on_delete=models.PROTECT, verbose_name='آیه', blank=True, null=True)
    root = models.ForeignKey(Root, on_delete=models.PROTECT, verbose_name='ریشه', blank=True, null=True)
    matched = models.IntegerField(verbose_name='تطابق')

    class Meta:
        verbose_name = 'شاخص ریشه آیه'
        verbose_name_plural = 'شاخص‌های ریشه آیه'

class Tafseer(models.Model):
    translator = models.ForeignKey(Translator, on_delete=models.PROTECT, limit_choices_to={'translation_type': 'tafseer'}, verbose_name='منبع تفسیر', related_name='tafseer')
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره', blank=True, null=True)
    from_aya = models.IntegerField(verbose_name='از آیه')
    to_aya = models.IntegerField(verbose_name='تا آیه')
    text = models.TextField(verbose_name='متن تفسیر')

    class Meta:
        verbose_name = 'تفسیر'
        verbose_name_plural = 'تفاسیر'

class TranslationAudio(models.Model):
    custom_id = models.IntegerField(verbose_name='شناسه صوت')
    translator = models.ForeignKey(Translator, on_delete=models.PROTECT, limit_choices_to={'translation_type': 'audio'}, verbose_name='منبع صوتی', related_name='translation_audio')
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره', blank=True, null=True)
    from_aya = models.IntegerField(verbose_name='از آیه')
    to_aya = models.IntegerField(verbose_name='تا آیه')
    first_type = models.CharField(max_length=125, verbose_name='اطلاعات صوت')
    class Meta:
        verbose_name = 'فایل صوتی ترجمه'
        verbose_name_plural = 'فایل‌های صوتی ترجمه'

class UnwantedWord(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name='کلمه بی‌اهمیت')

    class Meta:
        verbose_name = 'کلمه بی‌اهمیت'
        verbose_name_plural = 'کلمات بی‌اهمیت'

    def __str__(self):
        return self.word
    


class SearchTable(models.Model):
    id = models.AutoField(primary_key=True)
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, related_name='search_surah', verbose_name='سوره')
    verse = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='search_verse', verbose_name='آیه')
    
    verse_number = models.IntegerField()

    PageNum = models.PositiveIntegerField(verbose_name="شماره صفحه", db_index=True)
    JozNum = models.PositiveIntegerField(verbose_name="شماره جزء", db_index=True)
    HezbNum = models.PositiveIntegerField(verbose_name="شماره حزب", db_index=True)
    positioninpage = models.PositiveIntegerField(verbose_name="مکان در صفحه", db_index=True)

    SearchSP = models.TextField(verbose_name="SearchSP", blank=True, null=True)
    SearchP = models.TextField(verbose_name="SearchP", blank=True, null=True)
    SearchAE = models.TextField(verbose_name="SearchAE", blank=True, null=True)
    SearchSA = models.TextField(verbose_name="SearchSA", blank=True, null=True)
    SearchA = models.TextField(verbose_name="SearchA", blank=True, null=True)
    SearchAE2 = models.TextField(verbose_name="SearchAE2", blank=True, null=True)

    class Meta:
        # db_table = "searchTable"
        verbose_name = "Search Table"
        verbose_name_plural = "Search Tables"
        ordering = ["surah", "verse", "PageNum", "positioninpage"]
        indexes = [
            models.Index(fields=['surah', 'verse']),
            models.Index(fields=['PageNum']),
            models.Index(fields=['JozNum']),
            models.Index(fields=['HezbNum']),
        ]

    def __str__(self):
        return f"سوره {self.surah.name}، آیه {self.verse.verse_number}, صفحه {self.PageNum}"




class WordSearchTableMV(models.Model):
    verse = models.OneToOneField(Verse, on_delete=models.DO_NOTHING, primary_key=True)
    surah = models.ForeignKey(Surah, on_delete=models.DO_NOTHING)
    verse_number = models.SmallIntegerField()
    first_word = models.TextField(null=True)
    first_word_clean = models.TextField(null=True)
    second_word_clean = models.TextField(null=True)
    third_word_clean = models.TextField(null=True)
    last_word = models.TextField(null=True)
    last_word_clean = models.TextField(null=True)
    second_last_word_clean = models.TextField(null=True)
    third_last_word_clean = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'search_table'
        

class TafseerAudio(models.Model):
    custom_id = models.IntegerField(verbose_name='شناسه صوت')
    translator = models.ForeignKey(
        Translator,
        on_delete=models.PROTECT,
        limit_choices_to={'translation_type': 'audioTafseer'},
        verbose_name='منبع تفسیر صوتی',
        related_name='tafseer_audio',
    )
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name='سوره', blank=True, null=True)
    from_aya = models.IntegerField(verbose_name='از آیه')
    to_aya = models.IntegerField(verbose_name='تا آیه')
    audio_link = models.CharField(max_length=50, verbose_name='لینک صوتی تفسیر')

    class Meta:
        verbose_name = 'فایل صوتی تفسیر'
        verbose_name_plural = 'فایل‌های صوتی تفسیر'

    def __str__(self):
        return f'{self.translator.name} - سوره {self.surah.name} ({self.from_aya} تا {self.to_aya})'
