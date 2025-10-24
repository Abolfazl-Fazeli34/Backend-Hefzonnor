import random

from quran.models import Verse
from .base import BaseQuestionGenerator


class VerseToTranslationGenerator(BaseQuestionGenerator):
    def __init__(self, extra_translations_provider, ask_from_number):
        self.extra_translations_provider = extra_translations_provider()
        self.ask_from_number = ask_from_number

    def get_question_title(self, verse, words_list, translation):
        question_title = 'ترجمه ی آیه ی زیر کدام گزینه است؟ '
        if self.ask_from_number:
            question_title = question_title + f' سوره {verse.surah.name} آيه {verse.verse_number} '
        else:
            question_title = question_title + ' '.join(word['arabic'] for word in words_list)
        return question_title

    def get_correct_options(self, verse, words_list, translation):
        return translation

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        wrong_options = []
        attempts = 0
        max_attempts = len(valid_verses) + 10

        while len(wrong_options) < 3 and attempts < max_attempts:
            idx = random.randint(0, len(valid_verses) - 1)
            other_verse, _, other_translation = valid_verses[idx]
            if (
                    other_verse.id != verse.id
                    and other_translation
                    and other_translation != correct_option
                    and other_translation not in wrong_options
            ):
                wrong_options.append(other_translation)
            attempts += 1

        if len(wrong_options) < 3:
            need_count = 3 - len(wrong_options)
            extra_translations = self.extra_translations_provider.get_extra_translations(verse.id, need_count)
            wrong_options.extend([t for t in extra_translations if t != correct_option and t not in wrong_options])

        return wrong_options[:3]


class TranslationToVerseGenerator(BaseQuestionGenerator):
    def __init__(self, options_from_number):
        self.options_from_number = options_from_number

    def get_question_title(self, verse, words_list, translation):
        return f'متن زیر ترجمه کدام آیه است؟ {translation}'

    def get_correct_options(self, verse, words_list, translation):
        return f' آیه{verse.verse_number} سوره {verse.surah.name}' if self.options_from_number else ' '.join(
            word['arabic'] for word in words_list)

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        wrong_options = []
        attempts = 0
        max_attempts = len(valid_verses) + 10

        while len(wrong_options) < 3 and attempts < max_attempts:
            idx = random.randint(0, len(valid_verses) - 1)
            other_verse, other_words, _ = valid_verses[idx]
            if other_verse.id != verse.id:
                temp_wrong = f'آیه {other_verse.verse_number} سوره {other_verse.surah.name}' if self.options_from_number else ' '.join(
                    word['arabic'] for word in other_words)
                if temp_wrong != correct_option and temp_wrong not in wrong_options:
                    wrong_options.append(temp_wrong)
            attempts += 1

        if len(wrong_options) < 3:
            need_count = 3 - len(wrong_options)
            if self.options_from_number:
                max_verse_number = max(v[0].verse_number for v in valid_verses)
                extra_options = [
                    f'آیه {max_verse_number + i + 1} سوره {verse.surah.name}'
                    for i in range(need_count)
                ]
            else:
                extra_verses = Verse.objects.exclude(id=verse.id).order_by('?')[:need_count]
                extra_options = [' '.join(w.arabic_text for w in v.words.order_by('word_number')) for v in extra_verses]
            wrong_options.extend([opt for opt in extra_options if opt != correct_option and opt not in wrong_options])

        return wrong_options[:3]
