from typing import Any, Optional
import django_filters
from django.db.models import QuerySet

from quran.models import (
    Surah,
      VerseTranslation,
        Translator,
          WordMeaning,
            Tafseer, 
              TranslationAudio, 
                Qari,
                  Word,
                    TafseerAudio
    )


class SurahFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains',label="Arabic Name (Partial Match)")
    english_name = django_filters.CharFilter(lookup_expr='icontains',label="English Name (Partial Match)")
    juz = django_filters.NumberFilter(field_name='verses__juz',label="Juz Number")
    page_number = django_filters.NumberFilter(field_name='verses__page_number',label="Page Number")
    verse_number = django_filters.NumberFilter(field_name='verses__verse_number',label="Verse Number")
    class Meta:
        model = Surah
        fields = ['id', 'name', 'english_name', 'juz', 'page_number', 'verse_number']


class AudioFilter(django_filters.FilterSet):
    qari_id = django_filters.NumberFilter(label="Qari ID")
    surah_id = django_filters.NumberFilter(label="Surah ID")
    ayah_id = django_filters.NumberFilter(label="Ayah ID")
    page_number = django_filters.NumberFilter(label="Page Number")
    word_id = django_filters.NumberFilter(label="Word ID")
    class Meta:
        model = None 
        fields = ['qari_id', 'surah_id', 'ayah_id', 'page_number', 'word_id']


class CombinedListFilter(django_filters.FilterSet):
    TYPE_CHOICES = [
        ('surah', 'Surah'),
        ('juz', 'Juz'),
        ('page', 'Page'),
    ]
    type = django_filters.ChoiceFilter(choices=TYPE_CHOICES,method='filter_type',label='List Type')
    class Meta:
        model = Word
        fields: list[str] = []
    def filter_type(self, queryset: QuerySet[Any], name: str, value: Optional[str] ) -> QuerySet[Any]:
        return queryset
    

class TranslatorFilter(django_filters.FilterSet):
    LANGUAGE_CHOICES = [
        ('fa', "Fa"),
        ('en', 'En')
    ]
    TRANSLATION_TYPE = [
        ('verse', 'Verse'),
        ('word', 'Word'),
        ('tafseer', 'Tafseer'),
        ('audioTafseer', 'Audio')
    ]
    language = django_filters.ChoiceFilter(choices=LANGUAGE_CHOICES, label='language')
    translation_type = django_filters.ChoiceFilter(choices=TRANSLATION_TYPE, label='translation_type')
    class Meta:
        model = Translator
        fields = ['language', 'translation_type']

class VerseTranslationFilter(django_filters.FilterSet):
    verse = django_filters.NumberFilter(label='verse')
    translator = django_filters.ModelChoiceFilter(
        queryset=Translator.objects.filter(translation_type='verse').distinct(),
        label='translator'
    )                       #  تغییر باید بکند و بهینه تر شود فعلا تستی هست 
    surah = django_filters.NumberFilter(label='surah')

    class Meta:
        model = VerseTranslation
        fields = ['verse', 'translator', 'surah']


class WordMeaningFilter(django_filters.FilterSet):
    verse = django_filters.NumberFilter(label='verse')
    translator = django_filters.ModelChoiceFilter(
        queryset=Translator.objects.filter(translation_type='word').distinct(),
        label='translator'
    )   
    surah = django_filters.NumberFilter(label='surah')
    root_id = django_filters.NumberFilter(label='root_id')

    class Meta:
        model = WordMeaning
        fields = ['verse', 'surah', 'translator', 'root_id']

class TafseerFilter(django_filters.FilterSet):
    translator = django_filters.ModelChoiceFilter(
        queryset=Translator.objects.filter(translation_type='tafseer').distinct(),
        label='translator'
    )
    surah = django_filters.NumberFilter(label='surah')
    from_aya = django_filters.NumberFilter(label='from_aya')
    to_aya = django_filters.NumberFilter(label='to_aya')

    class Meta:
        model = Tafseer
        fields = ['translator', 'surah', 'from_aya', 'to_aya']

class TranslationAudioFilter(django_filters.FilterSet):
    translator = django_filters.ModelChoiceFilter(
        queryset=Translator.objects.filter(translation_type='audio').distinct(),
        label='translator')
    surah = django_filters.NumberFilter(label='surah')
    from_aya = django_filters.NumberFilter(label='from_aya')
    to_aya = django_filters.NumberFilter(label='to_aya')
    class Meta:
        model = TranslationAudio
        fields = ['translator', 'surah', 'from_aya', 'to_aya']


class TafseerAudioFilter(django_filters.FilterSet):
    translator = django_filters.ModelChoiceFilter(
        queryset=Translator.objects.filter(translation_type='audioTafseer').distinct(),
        label='translator'
    )
    surah = django_filters.NumberFilter(label='surah')
    from_aya = django_filters.NumberFilter(label='from_aya')
    to_aya = django_filters.NumberFilter(label='to_aya')

    class Meta:
        model = TafseerAudio
        fields = ['translator', 'surah', 'from_aya', 'to_aya']

class QariFilter(django_filters.FilterSet):

    class Meta:
        model = Qari
        fields = ['id', 'name', 'path', 'type', 'language', 'narrator']


# class TranslatorCombinedFilter(django_filters.FilterSet):
#     language = django_filters.CharFilter(field_name='language', lookup_expr='iexact')
#     translation_type = django_filters.CharFilter(field_name='translation_type', lookup_expr='iexact')
#     surah = django_filters.NumberFilter(method='filter_by_surah')
#     verse = django_filters.NumberFilter(method='filter_by_verse')

#     class Meta:
#         model = Translator
#         fields = ['language', 'translation_type', 'surah', 'verse']

#     def filter_by_surah(self, queryset, name, value):
#         return queryset.filter(
#             verse_translations__surah_id=value
#         ) | queryset.filter(
#             word_meaning__surah_id=value
#         ) | queryset.filter(
#             tafseer__surah_id=value
#         ) | queryset.filter(
#             translation_audio__surah_id=value
#         )

#     def filter_by_verse(self, queryset, name, value):
#         return queryset.filter(
#             verse_translations__verse_id=value
#         ) | queryset.filter(
#             word_meaning__verse_id=value
#         )