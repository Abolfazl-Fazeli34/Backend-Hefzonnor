import random

from exam.models import MultipleChoiceQuestion, Option


class BaseQuestionGenerator:
    def generate(self, quiz, participation, template, count, verses, subtype):
        valid_verses = [
            (
                verse,
                [{'arabic': word.arabic_text, 'clean': word.clean_arabic_text} for word in verse.prefetched_words],
                verse.prefetched_translation[0].text if verse.prefetched_translation else None
            )
            for verse in verses
            if verse.prefetched_translation and len(verse.prefetched_words) >= 2
        ]

        if not valid_verses:
            return {'message': 'No valid verses found'}

        generated = 0
        used_indices = set()
        questions = []
        options_to_create = []

        while generated < count:
            available_indices = list(set(range(len(valid_verses))) - used_indices)
            if not available_indices:
                available_indices = list(range(len(valid_verses)))
                used_indices.clear()
            random.shuffle(available_indices)

            for idx in available_indices:
                if generated >= count:
                    break
                verse, words_list, translation = valid_verses[idx]
                correct_option = self.get_correct_options(verse, words_list, translation)
                wrong_options = self.get_wrong_options(verse, correct_option, valid_verses, words_list)
                if len(wrong_options) < 3:
                    continue
                correct_index = random.randint(0, 3)
                question_title = self.get_question_title(verse, words_list, translation)
                question = MultipleChoiceQuestion(
                    title=question_title,
                    participation=participation,
                    template=template
                )
                questions.append(question)
                for i in range(4):
                    is_correct = (i == correct_index)
                    text = correct_option if is_correct else wrong_options.pop()
                    options_to_create.append(
                        Option(
                            number=i + 1,
                            text=text,
                            is_correct=is_correct,
                            question=question
                        )
                    )
                used_indices.add(idx)
                generated += 1

        if not questions:
            return {
                'message': f'No questions generated for subtype: {subtype.code}, template: {template.code} due to insufficient valid options'}

        return {'questions': questions, 'options': options_to_create}

    def get_wrong_options(self, verse, correct_option, valid_verses, words_list):
        raise NotImplementedError()

    def get_correct_options(self, verse, words_list, translation):
        raise NotImplementedError()

    def get_question_title(self, verse, words_list, translation):
        raise NotImplementedError()
