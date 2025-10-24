import shortuuid

from exam.models import Quiz, MatchingChunk
from quran.models import Verse


class MatchingChunkGenerator:
    def __init__(self, quiz: Quiz, chunk_size: int = 5):
        subtype = quiz.subtypes.first()
        if subtype.code not in [9, 10, 11]:
            raise ValueError(f"Unsupported matching subtype: {subtype.code}")
        self.quiz = quiz
        self.subtype_code = subtype.code
        self.chunk_size = chunk_size

        self.verses = (
            Verse.objects
            .filter(id__gte=quiz.start_verse.id, id__lte=quiz.end_verse.id)
            .select_related('surah')
            .prefetch_related('words')
            .order_by('surah_id', 'verse_number')
        )
        self.words = {v.id: list(v.words.all()) for v in self.verses}

    def _get_left_right_pair(self, verse):
        words = self.words[verse.id]
        if not words:
            return None, None

        start_word = words[0].arabic_text
        end_word = words[-1].arabic_text
        verse_info = f"{verse.verse_number} آیه {verse.surah.name}سوره "

        if self.subtype_code == 9:
            return start_word, verse_info
        elif self.subtype_code == 10:
            return end_word, verse_info
        elif self.subtype_code == 11:
            return start_word, end_word
        return None, None

    def generate(self):
        verses = list(self.verses)
        total_chunks = (len(verses) + self.chunk_size - 1) // self.chunk_size

        chunks_to_create = []

        for i in range(total_chunks):
            chunk_verses = verses[i * self.chunk_size: (i + 1) * self.chunk_size]

            left_items = []
            right_items = []
            left_text_to_id = {}
            right_text_to_id = {}

            correct_matches = []

            for verse in chunk_verses:
                left_text, right_text = self._get_left_right_pair(verse)
                if not left_text or not right_text:
                    continue

                if left_text not in left_text_to_id:
                    left_id = str(shortuuid.uuid()[:8])
                    left_text_to_id[left_text] = left_id
                    left_items.append({"id": left_id, "text": left_text})
                else:
                    left_id = left_text_to_id[left_text]
                    left_text_to_id[left_text] = left_id
                    left_items.append({"id": left_id, "text": left_text})

                if right_text not in right_text_to_id:
                    right_id = str(shortuuid.uuid()[:8])
                    right_text_to_id[right_text] = right_id
                    right_items.append({"id": right_id, "text": right_text})
                else:
                    right_id = right_text_to_id[right_text]
                    right_text_to_id[right_text] = right_id
                    right_items.append({"id": right_id, "text": right_text})

                correct_matches.append([left_id, right_id])

            if left_items and right_items:
                chunks_to_create.append(MatchingChunk(
                    quiz=self.quiz,
                    step_index=i + 1,
                    left_items=left_items,
                    right_items=right_items,
                    correct_matches=correct_matches,
                ))

        MatchingChunk.objects.bulk_create(chunks_to_create)
