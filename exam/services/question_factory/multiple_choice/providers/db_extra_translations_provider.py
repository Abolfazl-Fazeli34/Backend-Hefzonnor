from quran.models import VerseTranslation


class DatabaseExtraTranslationProvider:
    def get_extra_translations(self, verse_id, need_count=3):
        queryset = VerseTranslation.objects.filter(
            translator_id=5
        ).exclude(
            verse_id=verse_id
        ).order_by('?')[:need_count].values_list('text', flat=True)

        return queryset
