# subtype_handler.py
from collections import defaultdict

from django.db.models import Count, Prefetch, Q

from exam.models import QuestionTemplate, MultipleChoiceQuestion, Option
from quran.models import Verse, Word, VerseTranslation
from .dispatchers.dispatchers import (
    VerseBeginningSubtypeDispatcher,
    VerseEndingSubtypeDispatcher, VerseTranslationSubtypeDispatcher,
    VerseDetailSubtypeDispatcher, VerseBeforeAfterSubtypeDispatcher, VerseHardBeginningSubtypeDispatcher,
    VerseHardEndingSubtypeDispatcher
)
from .utils import divide_and_spread_remainder

subtype_dispatch = {
    1: lambda: VerseBeginningSubtypeDispatcher(),
    2: lambda: VerseEndingSubtypeDispatcher(),
    3: lambda: VerseTranslationSubtypeDispatcher(),
    4: lambda: VerseDetailSubtypeDispatcher(),
    5: lambda: VerseBeforeAfterSubtypeDispatcher(),
    16: lambda: VerseHardBeginningSubtypeDispatcher(),
    17: lambda: VerseHardEndingSubtypeDispatcher(),
}


def generate_questions(quiz, participation):
    subtypes = list(quiz.subtypes.all())
    question_counts = divide_and_spread_remainder(quiz.question_count, len(subtypes))

    all_questions = []
    all_options = []
    all_messages = []

    words_queryset = Word.objects.filter(type=1).order_by('word_number')
    translation_queryset = VerseTranslation.objects.filter(translator_id=5)
    verses = (
        Verse.objects
        .filter(id__gte=quiz.start_verse_id, id__lte=quiz.end_verse_id)
        .prefetch_related(
            Prefetch('words', queryset=words_queryset, to_attr='prefetched_words'),
            Prefetch('versetranslation_set', queryset=translation_queryset, to_attr='prefetched_translation')
        )
        .select_related('surah', 'text')
        .annotate(word_count=Count("words", filter=Q(words__type=1)))
        .filter(word_count__gt=1)
    )

    templates = QuestionTemplate.objects.filter(subtype__in=subtypes).order_by('code')

    templates_by_subtype = defaultdict(list)
    for template in templates:
        templates_by_subtype[template.subtype_id].append(template)

    for subtype, count in zip(subtypes, question_counts):
        templates = templates_by_subtype.get(subtype.id, [])
        handler_factory = subtype_dispatch.get(subtype.code)
        if not handler_factory:
            raise NotImplementedError(f"No handler defined for subtype code {subtype.code}")

        handler = handler_factory()

        if not handler:
            raise NotImplementedError(f"No handler defined for subtype code {subtype.code}")
        result = handler.dispatch(
            templates=templates,
            subtype=subtype,
            quiz=quiz,
            participation=participation,
            count=count,
            verses=verses,
        )
        all_questions.extend(result.get('questions', []))
        all_options.extend(result.get('options', []))
        message = result.get('message')
        if isinstance(message, list):
            all_messages.extend(message)
        elif isinstance(message, str):
            all_messages.append(message)

    if all_questions:
        MultipleChoiceQuestion.objects.bulk_create(all_questions)
        for i, question in enumerate(all_questions):
            for j in range(4):
                all_options[i * 4 + j].question = question
        Option.objects.bulk_create(all_options)

    return {
        'message': '\n'.join(m for m in all_messages if m),
        'questions': all_questions,
    }
