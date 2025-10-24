import random

from .base import BaseQuestionGenerator


class VerseDetailsGenerator(BaseQuestionGenerator):
    def __init__(self, extra_verse_provider, ask_from_number):
        self.extra_verse_provider = extra_verse_provider()
        self.ask_from_number = ask_from_number

    def get_question_title(self, verse, words_list, translation):
        if self.ask_from_number:
            return f' سوره آیه مرتبط با شماره زیر را انتخاب کنید{verse.surah.name} آيه {verse.verse_number}'
        else:
            return f'شماره آیه زیر چند است؟{" ".join(word['arabic'] for word in words_list)}'

    def get_correct_options(self, verse, words_list, translation):
        return (
            ' '.join(word['arabic'] for word in words_list)
            if self.ask_from_number
            else str(f" سوره {verse.surah.name} آيه {verse.verse_number}")
        )

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        wrong_options = []
        attempts = 0
        max_attempts = len(valid_verses) + 10

        while len(wrong_options) < 3 and attempts < max_attempts:
            idx = random.randint(0, len(valid_verses) - 1)
            other_verse, other_words, _ = valid_verses[idx]
            if other_verse.id == verse.id:
                continue

            temp = (
                ' '.join(word['arabic'] for word in other_words)
                if self.ask_from_number
                else str(f" سوره {other_verse.surah.name} آيه {other_verse.verse_number}")
            )
            if temp != correct_option and temp not in wrong_options:
                wrong_options.append(temp)

            attempts += 1

        if len(wrong_options) < 3:
            need_count = 3 - len(wrong_options)
            excludes = wrong_options.copy()
            excludes.append(correct_option)
            extras = self.extra_verse_provider.get_extras(
                exclude=excludes,
                count=need_count,
                type='text' if self.ask_from_number else 'number',
                verse_id=verse.id
            )
            wrong_options.extend([e for e in extras if e not in wrong_options])

        return wrong_options[:3]
