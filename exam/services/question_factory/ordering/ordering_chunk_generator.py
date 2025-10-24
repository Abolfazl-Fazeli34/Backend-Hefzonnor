from django.db.models import OuterRef, Subquery

from exam.models import OrderingChunk
from quran.models import Word, Verse


def ordering_subtype_dispatcher(quiz, force_regenerate=False):
    subtype = quiz.subtypes.all()[0]
    generator_map = {
        6: generate_ordering_chunk_from_verse,
        7: generate_ordering_chunk_from_verse_starts,
        8: generate_ordering_chunk_from_verse_ends,
    }
    if subtype.code not in generator_map:
        raise NotImplementedError('Generator with code {} not implemented'.format(subtype.code))
    generator = generator_map[subtype.code]
    generator(quiz, force_regenerate)


def generate_ordering_chunk_from_verse(quiz, force_regenerate):
    if OrderingChunk.objects.filter(quiz=quiz).exists() and not force_regenerate:
        return

    chunk_size = quiz.chunk_size

    words_qs = (
        Word.objects
        .filter(verse__gte=quiz.start_verse, verse__lte=quiz.end_verse, type=1)
        .order_by('verse__id', 'word_number')
        .values('verse_id', 'arabic_text')
    )

    step_index = 1
    current_chunk = []
    last_verse_id = None
    chunks = []

    for word in words_qs:
        verse_id = word['verse_id']
        arabic_text = word['arabic_text']

        if last_verse_id is not None and verse_id != last_verse_id and current_chunk:
            chunks.append(OrderingChunk(
                quiz=quiz,
                correct_order=current_chunk.copy(),
                step_index=step_index
            ))
            step_index += 1
            current_chunk = []

        current_chunk.append(arabic_text)

        if len(current_chunk) == chunk_size:
            chunks.append(OrderingChunk(
                quiz=quiz,
                correct_order=current_chunk.copy(),
                step_index=step_index
            ))
            step_index += 1
            current_chunk = []

        last_verse_id = verse_id

    if current_chunk:
        chunks.append(OrderingChunk(
            quiz=quiz,
            correct_order=current_chunk.copy(),
            step_index=step_index
        ))

    OrderingChunk.objects.bulk_create(chunks)


def generate_ordering_chunk_from_verse_starts(quiz, force_regenerate):
    if OrderingChunk.objects.filter(quiz=quiz).exists() and not force_regenerate:
        return

    chunk_size = quiz.chunk_size

    start_words_qs = (
        Word.objects
        .filter(
            verse__gte=quiz.start_verse,
            verse__lte=quiz.end_verse,
            word_number=1,
            type=1
        )
        .order_by('verse__id')
        .values_list('arabic_text', flat=True)
    )

    chunks = []
    step_index = 1

    for i in range(0, len(start_words_qs), chunk_size):
        chunk = start_words_qs[i:i + chunk_size]
        chunks.append(OrderingChunk(
            quiz=quiz,
            correct_order=list(chunk),
            step_index=step_index
        ))
        step_index += 1

    OrderingChunk.objects.bulk_create(chunks)


def generate_ordering_chunk_from_verse_ends(quiz, force_regenerate):
    if OrderingChunk.objects.filter(quiz=quiz).exists() and not force_regenerate:
        return

    chunk_size = quiz.chunk_size

    last_word_subquery = Word.objects.filter(
        verse_id=OuterRef('pk'),
        type=1
    ).order_by('-word_number').values('arabic_text')[:1]

    last_words = (
        Verse.objects
        .filter(id__gte=quiz.start_verse_id, id__lte=quiz.end_verse_id)
        .annotate(last_word=Subquery(last_word_subquery))
        .values_list('last_word', flat=True)
    )

    chunks = []
    step_index = 1

    for i in range(0, len(last_words), chunk_size):
        chunk = last_words[i:i + chunk_size]
        chunks.append(OrderingChunk(
            quiz=quiz,
            correct_order=list(chunk),
            step_index=step_index
        ))
        step_index += 1

    OrderingChunk.objects.bulk_create(chunks)
