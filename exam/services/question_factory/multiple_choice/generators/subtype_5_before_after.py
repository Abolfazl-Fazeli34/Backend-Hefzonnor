import random

from exam.models import MultipleChoiceQuestion, Option
from .base import BaseQuestionGenerator


class VerseBeforeAfterGenerator(BaseQuestionGenerator):
    def __init__(self, extra_verse_provider, direction='after'):
        assert direction in ['after', 'before'], "Direction must be 'after' or 'before'"
        self.direction = direction
        self.extra_verse_provider = extra_verse_provider

    def generate(self, quiz, participation, template, count, verses, subtype):
        valid_verses = [
            (verse, [w.arabic_text for w in verse.prefetched_words], verse.text.full_tashkeel, verse.surah.name,
             verse.verse_number)
            for verse in verses
            if len(verse.prefetched_words) >= 2
        ]

        if len(valid_verses) < 2:
            return {
                'message': f'Not enough verses to generate any questions for subtype: {subtype.code}, template: {template.code}',
                'questions': [], 'options': []}

        questions = []
        options = []
        generated = 0
        attempts = 0
        max_attempts = count * 5

        while generated < count and attempts < max_attempts:
            attempts += 1

            if self.direction == 'after':
                rand_idx = random.randint(0, len(valid_verses) - 2)
                max_distance = min(3, len(valid_verses) - 1 - rand_idx)
                if max_distance < 1:
                    continue
                step = random.randint(1, max_distance)
                source_idx = rand_idx
                target_idx = rand_idx + step
            else:  # before
                rand_idx = random.randint(1, len(valid_verses) - 1)
                max_distance = min(3, rand_idx)
                if max_distance < 1:
                    continue
                step = random.randint(1, max_distance)
                source_idx = rand_idx
                target_idx = rand_idx - step

            source_verse, words_list, source_text, surah_name, verse_number = valid_verses[source_idx]
            target_verse, _, target_text, _, _ = valid_verses[target_idx]

            if source_text == target_text:
                continue

            direction_word = 'بعد' if self.direction == 'after' else 'قبل'
            question_title = f"{step} آیه {direction_word} از آیه زیر کدام است؟ {surah_name} {verse_number}: {' '.join(words_list)}"

            q = MultipleChoiceQuestion(
                title=question_title,
                participation=participation,
                template=template
            )
            questions.append(q)

            correct_index = random.randint(0, 3)
            wrong_options = []

            for offset in range(1, len(valid_verses)):
                if len(wrong_options) >= 3:
                    break
                idx = target_idx + offset
                if idx >= len(valid_verses):
                    idx = target_idx - offset
                    if idx < 0:
                        continue
                candidate = valid_verses[idx][2]
                if candidate != source_text and candidate != target_text and candidate not in wrong_options:
                    wrong_options.append(candidate)

            if len(wrong_options) < 3:
                extra_verses = self.extra_verse_provider.get_extra_verse_texts()
                for extra in extra_verses:
                    if extra != target_text and extra not in wrong_options:
                        wrong_options.append(extra)
                        if len(wrong_options) >= 3:
                            break

            if len(wrong_options) < 3:
                questions.pop()
                continue

            for i in range(4):
                is_correct = (i == correct_index)
                option_text = target_text if is_correct else wrong_options.pop()
                options.append(
                    Option(
                        number=i + 1,
                        text=option_text,
                        is_correct=is_correct,
                        question=q
                    )
                )

            generated += 1

        return {
            'questions': questions,
            'options': options
        }


class VerseRelativeWordGenerator(BaseQuestionGenerator):
    def __init__(self, direction: str, extra_words_provider=None):
        assert direction in ('before', 'after'), "direction must be 'before' or 'after'"
        self.direction = direction
        self.extra_word_provider = extra_words_provider

    def generate(self, quiz, participation, template, count, verses, subtype):
        valid_verses = [
            (i, verse, [w.arabic_text for w in verse.prefetched_words], verse.surah.name, verse.verse_number)
            for i, verse in enumerate(verses)
        ]

        if len(valid_verses) < 2:
            return {
                'message': f'Not enough verses to generate questions for subtype: {subtype.code}, template: {template.code}',
                'questions': [], 'options': []}

        questions, options = [], []
        generated = 0
        attempts = 0
        max_attempts = count * 5

        while generated < count and attempts < max_attempts:
            attempts += 1

            indices = (
                list(range(1, len(valid_verses))) if self.direction == 'before'
                else list(range(0, len(valid_verses) - 1))
            )
            random.shuffle(indices)

            for idx in indices:
                if generated >= count:
                    break

                max_distance = (
                    min(3, idx) if self.direction == 'before'
                    else min(3, len(valid_verses) - 1 - idx)
                )
                if max_distance < 1:
                    continue

                distance = random.randint(1, max_distance)

                source_idx = idx
                target_idx = idx - distance if self.direction == 'before' else idx + distance
                if not (0 <= target_idx < len(valid_verses)):
                    continue

                source_verse_data = valid_verses[source_idx]
                target_verse_data = valid_verses[target_idx]

                _, source_verse, source_words, surah_name, verse_number = source_verse_data
                _, target_verse, target_words, *_ = target_verse_data

                if len(target_words) < 3:
                    continue

                candidate_words = [w for w in target_words if len(w) >= 2]
                if not candidate_words:
                    continue

                correct_word = random.choice(candidate_words)
                q_title = f"در {distance} آیه {'قبل' if self.direction == 'before' else 'بعد'} از آیه زیر چه کلمه‌ای به کار رفته است؟ {surah_name} {verse_number}: {' '.join(source_words)}"

                q = MultipleChoiceQuestion(title=q_title, participation=participation, template=template)
                correct_index = random.randint(0, 3)
                wrong_words = set()

                for offset in range(1, len(valid_verses)):
                    if len(wrong_words) >= 3:
                        break
                    alt_idx = target_idx + offset if self.direction == 'after' else target_idx - offset
                    if not (0 <= alt_idx < len(valid_verses)):
                        continue
                    _, _, other_words, *_ = valid_verses[alt_idx]
                    candidates = [w for w in other_words if len(w) >= 2 and w not in target_words]
                    random.shuffle(candidates)
                    for w in candidates:
                        if w != correct_word and w not in wrong_words:
                            wrong_words.add(w)
                            break

                # fallback to external provider
                if len(wrong_words) < 3 and self.extra_word_provider:
                    exclude_words = set(wrong_words) | set(target_words)

                    extra_words = self.extra_word_provider.get_extra_words(
                        verse_id=target_verse.id,
                        correct_word=correct_word,
                        exclude_list=list(exclude_words),
                        need_count=3 - len(wrong_words)
                    )
                    for ew in extra_words:
                        if ew != correct_word and ew not in wrong_words:
                            wrong_words.add(ew)
                        if len(wrong_words) >= 3:
                            break

                if len(wrong_words) < 3:
                    continue

                for i in range(4):
                    is_correct = (i == correct_index)
                    word = correct_word if is_correct else wrong_words.pop()
                    options.append(
                        Option(
                            number=i + 1,
                            text=word,
                            is_correct=is_correct,
                            question=q
                        )
                    )
                questions.append(q)
                generated += 1

        return {
            'questions': questions,
            'options': options
        }


class VerseOrderGenerator(BaseQuestionGenerator):
    def get_first_two_words(self, word_list):
        if not word_list:
            return ""
        elif len(word_list) == 1:
            return word_list[0]
        else:
            return f"{word_list[0]} {word_list[1]}"

    def get_order_signature(self, verses):
        return ' - '.join(self.get_first_two_words(v[2]) for v in verses)

    def generate_wrong_options(self, valid_verses, true_verses, correct_signature, needed=3, max_attempts=50):
        used_signatures = {correct_signature}
        wrong_options = set()
        attempts = 0

        while len(wrong_options) < needed and attempts < max_attempts:
            start = random.randint(0, len(valid_verses) - 4)
            candidate_verses = valid_verses[start:start + 4]

            if any(len(v[2]) < 2 for v in candidate_verses):
                attempts += 1
                continue

            signature = self.get_order_signature(candidate_verses)
            if signature in used_signatures:
                attempts += 1
                continue

            # shuffle to create incorrect order
            shuffled = candidate_verses[:]
            random.shuffle(shuffled)
            shuffled_signature = self.get_order_signature(shuffled)

            if shuffled_signature not in used_signatures:
                wrong_options.add(shuffled_signature)
                used_signatures.add(shuffled_signature)

            attempts += 1

        return list(wrong_options)

    def generate(self, quiz, participation, template, count, verses, subtype):
        valid_verses = [
            (i, verse, [w.arabic_text for w in verse.prefetched_words], verse.surah.name, verse.verse_number)
            for i, verse in enumerate(verses)
        ]

        if len(valid_verses) < 4:
            return {'questions': [], 'options': [],
                    'message': f'Not enough verses to generate questions for subtype: {subtype.code}, template: {template.code}'}

        questions = []
        options = []
        generated = 0

        while generated < count:
            start_idx = random.randint(0, len(valid_verses) - 4)
            end_idx = start_idx + 4
            true_verses = valid_verses[start_idx:end_idx]

            if any(len(v[2]) < 2 for v in true_verses):
                continue

            correct_option = self.get_order_signature(true_verses)
            wrong_options = self.generate_wrong_options(valid_verses, true_verses, correct_option)

            if len(wrong_options) < 3:
                continue

            q = MultipleChoiceQuestion(
                participation=participation,
                template=template,
                title="ترتیب صحیح آیه‌ها در کدام گزینه آمده است؟"
            )

            correct_index = random.randint(0, 3)
            for i in range(4):
                is_correct = (i == correct_index)
                text = correct_option if is_correct else wrong_options.pop()
                options.append(
                    Option(
                        number=i + 1,
                        question=q,
                        text=text,
                        is_correct=is_correct,
                    )
                )
            questions.append(q)
            generated += 1

        return {
            'questions': questions,
            'options': options
        }
