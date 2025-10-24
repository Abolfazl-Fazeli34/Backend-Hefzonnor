from quran.models import Verse


class DatabaseExtraVerseDetailsProvider:
    def get_extras(self, exclude, count, verse_id, type='text'):
        if type == 'number':
            verses = (
                Verse.objects
                .select_related('surah')
                .filter(id_gte=verse_id - 10, id_lte=verse_id + 10)
                .exclude(id=verse_id)
                .order_by('?')[:count * 2]
            )
            result = []
            for v in verses:
                text = f" سوره {v.surah.name} آيه {v.verse_number}"
                if text not in exclude and text not in result:
                    print(exclude, text)
                    result.append(text)
                if len(result) >= count:
                    break
            return result

        elif type == 'text':
            verses = (
                Verse.objects
                .prefetch_related('words')
                .order_by('?')[:count * 2]
            )
            result = []
            for v in verses:
                text = ' '.join(
                    w.arabic_text for w in sorted(v.words.all(), key=lambda w: w.word_number)
                )
                if text and text != exclude and text not in result:
                    result.append(text)
                if len(result) >= count:
                    break
            return result

        else:
            raise ValueError("Unsupported type passed to get_extras(): must be 'text' or 'number'")


class DatabaseExtraVerseProvider:
    def __init__(self, exclude_ids=None, max_count=20):
        self.exclude_ids = exclude_ids or []
        self.max_count = max_count

    def get_extra_verse_texts(self):
        queryset = (
            Verse.objects
            .exclude(id__in=self.exclude_ids)
            .values_list('text', flat=True)
            .distinct()[:self.max_count]
        )
        return list(queryset)
