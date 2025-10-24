from django.db.models import Count, Q

from exam.models import TypingParticipation, TypingSubmittedAnswer, TypingQuestion
from exam.serializers import BaseParticipationReviewSerializer, \
    TypingQuestionSerializer
from exam.services.participation.base_submission import BaseSubmissionService


class TypingAnswerSubmissionService(BaseSubmissionService):
    def __init__(self, participation: TypingParticipation):
        super().__init__(participation.participation)
        self.participation = participation
        self.question = self.get_current_question()

    def get_current_question(self):
        return TypingQuestion.objects.get(Q(participation=self.participation) | Q(quiz=self.quiz),
                                          step_index=self.participation.current_step)

    def submit(self, user_input):
        self.check_deadline()
        self.check_participation_status()

        handler = self._get_handler()
        return handler(self.question, user_input)

    def _get_handler(self):
        return {
            120: self._handle_single_word_answer,
            130: self._handle_single_word_answer,
            150: self._handle_single_word_answer,
            140: self._handle_full_verse_answer,
        }.get(self.question.template.code)

    def _handle_single_word_answer(self, question, user_input: str):
        correct_answers = question.answer
        if not user_input or not user_input.strip():
            is_correct = False
            text = ""
        else:
            text = user_input.strip()
            is_correct = text in correct_answers

        TypingSubmittedAnswer.objects.create(
            question=question,
            text=text,
            is_correct=is_correct,
        )

        if self.participation.current_step >= self.participation.total_steps:
            self.complete_participation()
            return {
                'status': 'quiz_completed',
                'data': BaseParticipationReviewSerializer(self.base_participation).data
            }

        self.advance_step()

        next_question = self.get_current_question()
        return {
            "status": 'correct' if is_correct else 'wrong',
            "data": TypingQuestionSerializer(next_question).data
        }

    def _handle_full_verse_answer(self, question, user_input: list):
        correct_answers = question.answer

        if not user_input or len(user_input) == 0:
            TypingSubmittedAnswer.objects.create(
                question=question,
                text="",
                is_correct=False,
            )
            self.advance_step()
            next_question = self.get_current_question()
            return {
                'status': 'wrong',
                'data': TypingQuestionSerializer(next_question).data
            }

        correct_words = []
        wrong_words = set()

        for word in user_input:
            found = any(word in correct_verse for correct_verse in correct_answers)
            if found:
                correct_words.append(word)
            else:
                wrong_words.add(word)

        if len(user_input) < len(min(correct_answers, key=len)):
            return {
                'status': 'missing_answers',
                'data': {
                    'correct_words': correct_words,
                    'wrong_words': wrong_words,
                }
            }

        is_fully_correct = len(wrong_words) == 0

        TypingSubmittedAnswer.objects.create(
            question=question,
            text=' '.join(user_input),
            is_correct=is_fully_correct,
        )

        if is_fully_correct:
            if self.participation.current_step >= self.participation.total_steps:
                self.complete_participation()
                return {'status': 'quiz_completed',
                        'data': BaseParticipationReviewSerializer(self.base_participation).data}

            self.advance_step()
            next_question = self.get_current_question()
            return {'status': 'correct', 'data': TypingQuestionSerializer(next_question).data}
        else:
            return {'status': 'wrong', 'data': {'correct_words': correct_words, 'wrong_words': wrong_words}}

    def complete_participation(self):
        counts = TypingSubmittedAnswer.objects.filter(
            Q(question__participation=self.participation) | Q(question__quiz=self.quiz)).aggregate(
            correct=Count('id', filter=Q(is_correct=True)),
            wrong=Count('id', filter=Q(is_correct=False))
        )
        wrong_answers_count = counts['wrong']
        correct_answers_count = counts['correct']
        self.base_participation.wrong_answers = wrong_answers_count
        self.base_participation.correct_answers = correct_answers_count
        super().complete_participation()

    def advance_step(self):
        self.participation.current_step += 1
        self.participation.save()
