from exam.services.question_factory.multiple_choice.generators.base import BaseQuestionGenerator


class VerseFirstWordHardGenerator(BaseQuestionGenerator):
    def __init__(self, hard_start_provider):
        self.hard_start_provider = hard_start_provider()

    def get_question_title(self, verse, words_list, translation):
        return f' متن سوال : ابتدای این آیه با چه کلمه ای شروع می‌شود؟ سوره: {verse.surah.name} آیه {verse.verse_number} ' + ' '.join(
            word['arabic'] for word in words_list[1:])

    def get_correct_options(self, verse, words_list, translation):
        return words_list[0]['arabic']

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        wrong_options = {'arabic': [], 'clean': []}
        second_word = words_list[1]['clean'] if len(words_list) > 1 else ''
        third_word = words_list[2]['clean'] if len(words_list) > 2 else ''

        hard_options = self.hard_start_provider.get_similar_first_words(
            verse_id=verse.id,
            correct_word=words_list[0]['clean'],
            second_word=second_word,
            third_word=third_word,
            need_count=3
        )
        wrong_options['arabic'].extend(hard_options['arabic'])
        wrong_options['clean'].extend(hard_options['clean'])

        if len(wrong_options['arabic']) < 3:
            fallback_options = self.get_wrong_options_with_nearby_fallback(verse, words_list[0]['clean'], valid_verses,
                                                                           need_count=3 - len(wrong_options['arabic']))
            wrong_options['arabic'].extend(fallback_options['arabic'])
            wrong_options['clean'].extend(fallback_options['clean'])

        return wrong_options['arabic'][:3]

    def get_wrong_options_with_nearby_fallback(
            self,
            verse,
            correct_clean_word,
            valid_verses,
            need_count=3,
            nearby_range=5,
    ):
        wrong_options = {'arabic': [], 'clean': []}
        nearby_verses = [
            (v, words, _) for v, words, _ in valid_verses
            if v.id != verse.id and verse.id - nearby_range <= v.id <= verse.id + nearby_range
        ]
        for v, words, _ in nearby_verses:
            if not words:
                continue
            word = words[0]
            if word['clean'] != correct_clean_word and word['clean'] not in wrong_options['clean']:
                wrong_options['arabic'].append(word['arabic'])
                wrong_options['clean'].append(word['clean'])
            if len(wrong_options['arabic']) >= need_count:
                break

        return wrong_options
