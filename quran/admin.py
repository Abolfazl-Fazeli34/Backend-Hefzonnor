from django.contrib import admin
from .models import (
    Surah, VerseText, Verse, Qari, Word, Translator, VerseTranslation,
    WordMeaning, Root, VerseRootIndex, Tafseer, TranslationAudio,
    WordSearchTableMV
)

@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ('name', 'arabic_name', 'english_name', 'english_meaning')
    search_fields = ('name', 'arabic_name', 'english_name', 'english_meaning')


@admin.register(VerseText)
class VerseTextAdmin(admin.ModelAdmin):
    list_display = ('plain', 'semi_tashkeel', 'simple_tashkeel', 'full_tashkeel', 'persian_friendly')
    search_fields = ('plain', 'semi_tashkeel', 'simple_tashkeel', 'full_tashkeel', 'persian_friendly')


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):
    list_display = ('verse_number', 'surah', 'page_number', 'section_number', 'juz')
    list_filter = ('surah', 'juz', 'page_number')
    search_fields = ('verse_number', 'text__plain', 'text__semi_tashkeel')


@admin.register(Qari)
class QariAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'language', 'narrator', 'link', 'path')
    list_filter = ('type', 'language')
    search_fields = ('name', 'narrator')


# @admin.register(Word)
# class WordAdmin(admin.ModelAdmin):
#     list_display = ('arabic_text', 'persian_text', 'english_text', 'word_number', 'verse_number', 'surah', 'qari')
#     list_filter = ('surah', 'verse', 'type')
#     search_fields = ('arabic_text', 'persian_text', 'english_text')


@admin.register(Translator)
class TranslatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'translation_type')
    list_filter = ('translation_type', 'language')
    search_fields = ('name',)


# @admin.register(VerseTranslation)
# class VerseTranslationAdmin(admin.ModelAdmin):
#     list_display = ('verse', 'surah', 'translator', 'text')
#     list_filter = ('surah', 'translator')
#     search_fields = ('text',)


# @admin.register(WordMeaning)
# class WordMeaningAdmin(admin.ModelAdmin):
#     list_display = ('verse', 'surah', 'translator', 'meanings', 'root_id')
#     list_filter = ('surah', 'translator')
#     search_fields = ('meanings',)


@admin.register(Root)
class RootAdmin(admin.ModelAdmin):
    list_display = ('root_code', 'root_arabic', 'root_english', 'newroot')
    search_fields = ('root_code', 'root_arabic', 'root_english')


@admin.register(VerseRootIndex)
class VerseRootIndexAdmin(admin.ModelAdmin):
    list_display = ('verse', 'root', 'matched')
    list_filter = ('root',)
    search_fields = ('verse__verse_number',)


# @admin.register(Tafseer)
# class TafseerAdmin(admin.ModelAdmin):
#     list_display = ('translator', 'surah', 'from_aya', 'to_aya', 'text')
#     list_filter = ('translator', 'surah')
#     search_fields = ('text',)


@admin.register(TranslationAudio)
class TranslationAudioAdmin(admin.ModelAdmin):
    list_display = ('custom_id', 'translator', 'surah', 'from_aya', 'to_aya', 'first_type')
    list_filter = ('translator', 'surah')
    search_fields = ('first_type',)


@admin.register(WordSearchTableMV)
class WordSearchTableMVAdmin(admin.ModelAdmin):
    list_display = ('verse', 'surah', 'verse_number', 'first_word', 'last_word')
    search_fields = ('first_word', 'last_word')
    readonly_fields = ('verse', 'surah', 'verse_number', 'first_word', 'last_word')
