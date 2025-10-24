from difflib import SequenceMatcher

from quran.models import Word, WordSearchTableMV


class DatabaseExtraWordsProvider:
    def get_extra_words(self, verse_id, correct_word, exclude_list, need_count, reverse_ordering=False):
        queryset = (
            Word.objects
            .filter(
                verse__id__gte=verse_id - 5,
                verse__id__lte=verse_id + 5,
                type=1
            )
            .exclude(verse_id=verse_id)
            .exclude(clean_arabic_text=correct_word)
            .exclude(clean_arabic_text__in=exclude_list)
        )

        ordering = '-word_number' if reverse_ordering else 'word_number'
        queryset = queryset.order_by(ordering).values_list('arabic_text', 'clean_arabic_text')

        return list(queryset[:need_count])


class HardStartWordProvider:
    def __init__(self):
        self.mv_cache = None

    def _get_mv_cache(self, exclude_verse_id=None):
        if self.mv_cache is None:
            self.mv_cache = {
                row.verse_id: row
                for row in WordSearchTableMV.objects.exclude(verse_id=exclude_verse_id)
            }
        return self.mv_cache

    def get_similar_first_words(self, verse_id, correct_word, second_word='', third_word='', need_count=3):
        wrong_words = {'arabic': [], 'clean': []}
        mv_cache = self._get_mv_cache(exclude_verse_id=verse_id)

        for row in mv_cache.values():
            if second_word and row.second_word_clean != second_word:
                continue
            if third_word and row.third_word_clean != third_word:
                continue
            if (
                    row.first_word_clean
                    and row.first_word_clean != correct_word
                    and row.first_word_clean not in wrong_words['clean']
            ):
                wrong_words['clean'].append(row.first_word_clean)
                wrong_words['arabic'].append(row.first_word)
            if len(wrong_words['arabic']) >= need_count:
                break

        if len(wrong_words['arabic']) < need_count:
            for row in mv_cache.values():
                if row.first_word_clean in wrong_words['clean'] or not row.first_word_clean:
                    continue
                similarity = SequenceMatcher(None, row.first_word_clean, correct_word).ratio()
                if similarity >= 0.7 and row.first_word_clean != correct_word:
                    wrong_words['clean'].append(row.first_word_clean)
                    wrong_words['arabic'].append(row.first_word)
                if len(wrong_words['arabic']) >= need_count:
                    break

        return wrong_words


class HardEndWordProvider:
    def __init__(self):
        self.mv_cache = None

    def _get_mv_cache(self, exclude_verse_id=None):
        if self.mv_cache is None:
            self.mv_cache = {
                row.verse_id: row
                for row in WordSearchTableMV.objects.exclude(verse_id=exclude_verse_id)
            }
        return self.mv_cache

    def get_similar_last_words(self, verse_id, correct_word, second_last_word='', third_last_word='', need_count=3):
        wrong_words = {'arabic': [], 'clean': []}
        mv_cache = self._get_mv_cache(exclude_verse_id=verse_id)

        for row in mv_cache.values():
            if second_last_word and row.second_word_clean != second_last_word:
                continue
            if third_last_word and row.third_word_clean != third_last_word:
                continue
            if (
                    row.last_word_clean
                    and row.last_word_clean != correct_word
                    and row.last_word_clean not in wrong_words['clean']
            ):
                wrong_words['clean'].append(row.last_word_clean)
                wrong_words['arabic'].append(row.last_word)
            if len(wrong_words['arabic']) >= need_count:
                break

        if len(wrong_words['arabic']) < need_count:
            for row in mv_cache.values():
                if row.last_word_clean in wrong_words['clean'] or not row.last_word_clean:
                    continue
                similarity = SequenceMatcher(None, row.last_word_clean, correct_word).ratio()
                if similarity >= 0.7 and row.last_word_clean != correct_word:
                    wrong_words['clean'].append(row.last_word_clean)
                    wrong_words['arabic'].append(row.last_word)
                if len(wrong_words['arabic']) >= need_count:
                    break

        return wrong_words
