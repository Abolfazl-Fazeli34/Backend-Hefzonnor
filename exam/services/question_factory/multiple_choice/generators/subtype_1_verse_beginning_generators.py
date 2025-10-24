from .base import BaseQuestionGenerator


class VerseFirstWordGenerator(BaseQuestionGenerator):
    def __init__(self, extra_words_provider, ask_from_number):
        self.extra_words_provider = extra_words_provider()
        self.ask_from_number = ask_from_number

    def get_question_title(self, verse, words_list, translation):
        question_title = f' متن سوال : ابتدای این آیه با چه کلمه ای شروع می‌شود؟ سوره: {verse.surah.name} آیه {verse.verse_number} '
        if not self.ask_from_number:
            return question_title + ' '.join(word['arabic'] for word in words_list[1:])
        return question_title

    def get_correct_options(self, verse, words_list, translation):
        return words_list[0]['arabic']

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        wrong_options = {'arabic': [], 'clean': []}

        nearby_verses = [
            (v, words, _) for v, words, _ in valid_verses
            if v.id != verse.id and verse.id - 5 <= v.id <= verse.id + 5
        ]

        for v, words, _ in nearby_verses:
            word = words[0]
            if word['clean'] != words_list[0]['clean'] and word['clean'] not in wrong_options['clean']:
                wrong_options['arabic'].append(word['arabic'])
                wrong_options['clean'].append(word['clean'])
            if len(wrong_options['arabic']) >= 3:
                break

        if len(wrong_options['arabic']) < 3:
            need_count = 3 - len(wrong_options['arabic'])
            extra_words = self.extra_words_provider.get_extra_words(
                verse_id=verse.id, correct_word=words_list[0]['clean'], exclude_list=wrong_options['clean'],
                need_count=need_count, reverse_ordering=False
            )
            for arabic, clean in extra_words:
                if clean not in wrong_options['clean'] and clean != words_list[0]['clean']:
                    wrong_options['arabic'].append(arabic)
                    wrong_options['clean'].append(clean)
                if len(wrong_options['clean']) >= 3:
                    break

        return wrong_options['arabic'][:3]
