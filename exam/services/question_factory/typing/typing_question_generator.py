import random

from exam.models import TypingQuestion, Quiz, TypingParticipation, QuizSubtype
from quran.models import Verse

FIRST_WORD_CODE = 12
LAST_WORD_CODE = 15
WHOLE_VERSE_CODE = 14


class CommonTypingQuestionGenerator:
    def __init__(self, quiz: Quiz):
        self.quiz = quiz
        self.start_verse = quiz.start_verse
        self.end_verse = quiz.end_verse
        self.verses = Verse.objects.filter(
            id__gte=self.start_verse.id,
            id__lte=self.end_verse.id,
        ).select_related('text').order_by('id')

    def generate(self):
        for subtype in self.quiz.subtypes.filter(code__in=[FIRST_WORD_CODE, LAST_WORD_CODE, WHOLE_VERSE_CODE]):
            self._generate_for_subtype(subtype)

    def _generate_for_subtype(self, subtype: QuizSubtype):
        questions = []
        for i, verse in enumerate(self.verses, start=1):
            answer = self._prepare_question_answer(verse, subtype.code)
            display_text = self._prepare_question_text(verse, subtype.code, answer[0])
            if not display_text or not answer:
                continue
            question = TypingQuestion(
                quiz=self.quiz,
                title=display_text,
                answer=answer,
                step_index=i,
                template=subtype.templates.first()
            )
            questions.append(question)
        TypingQuestion.objects.bulk_create(questions)

    def _prepare_question_answer(self, verse: Verse, subtype_code: int):
        texts = [
            verse.text.plain,
            verse.text.semi_tashkeel,
            verse.text.simple_tashkeel,
            verse.text.full_tashkeel,
            verse.text.persian_friendly,
            verse.text.fuzzy,
        ]

        def split_words(text):
            return text.strip().split()

        answers = []

        for text in texts:
            words = split_words(text)
            if subtype_code == FIRST_WORD_CODE:
                answer = words[0]
            elif subtype_code == LAST_WORD_CODE:
                answer = words[-1]
            elif subtype_code == WHOLE_VERSE_CODE:
                answer = words
            else:
                return None

            answers.append(answer)

        return answers

    def _prepare_question_text(self, verse: Verse, subtype_code: int, answer: str):
        text = verse.text.full_tashkeel
        words = text.strip().split()
        display = f'آیه زیر را کامل کنید سوره {verse.surah.name} آیه {verse.verse_number}: '
        if subtype_code == FIRST_WORD_CODE:
            placeholder = '_' * len(answer)
            display_words = [placeholder] + words[1:]
            display += ' '.join(display_words)
        elif subtype_code == LAST_WORD_CODE:
            placeholder = '_' * len(answer)
            display_words = words[:-1] + [placeholder]
            display += ' '.join(display_words)
        elif subtype_code == WHOLE_VERSE_CODE:
            display += ' '.join(['_' * len(word) for word in answer])
        else:
            return None
        return display


class MiddleWordTypingQuestionGenerator:
    def __init__(self, participation: TypingParticipation):
        self.participation = participation
        self.quiz = participation.participation.quiz
        self.subtype = self.quiz.subtypes.first()
        self.verses = Verse.objects.filter(
            id__gte=self.quiz.start_verse.id,
            id__lte=self.quiz.end_verse.id,
        ).select_related('text', 'surah').order_by('?')[:self.quiz.question_count]
        self.template = self.subtype.templates.first()

    def generate(self):
        verses = self.verses
        created_questions = []

        for i, verse in enumerate(verses, start=1):
            question = self._build_question_for_verse(verse, index=i)
            if question:
                created_questions.append(question)

        TypingQuestion.objects.bulk_create(created_questions)

    def _build_question_for_verse(self, verse, index: int):
        text = verse.text.plain
        words = text.split()

        word_index = random.randint(0, len(words) - 1)
        missing_word = words[word_index]

        placeholder = '_' * len(missing_word)
        words_with_blank = words.copy()
        words_with_blank[word_index] = placeholder
        question_text = f'آیه زیر را کامل کنید سوره {verse.surah.name} آیه {verse.verse_number}: '
        question_text += ' '.join(words_with_blank)

        alternatives = self._get_variants(verse.text, word_index)

        return TypingQuestion(
            participation=self.participation,
            title=question_text,
            answer=alternatives,
            step_index=index,
            template=self.template
        )

    def _get_variants(self, verse_text, index):
        raw_variants = [
            verse_text.plain.split(),
            verse_text.semi_tashkeel.split(),
            verse_text.simple_tashkeel.split(),
            verse_text.full_tashkeel.split(),
            verse_text.persian_friendly.split(),
            verse_text.fuzzy.split(),
        ]
        variants = [variant[index] for variant in raw_variants if len(variant) > index]
        return variants
