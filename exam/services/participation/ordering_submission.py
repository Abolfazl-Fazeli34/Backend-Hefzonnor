from django.shortcuts import get_object_or_404

from exam.models import OrderingParticipation, OrderingChunk
from exam.serializers import OrderingChunkSerializer, BaseParticipationReviewSerializer
from exam.services.participation.base_submission import BaseSubmissionService


class OrderingSubmissionService(BaseSubmissionService):
    def __init__(self, participation: OrderingParticipation):
        super().__init__(participation.participation)
        self.participation = participation

    def get_chunk(self) -> OrderingChunk:
        return get_object_or_404(
            OrderingChunk,
            quiz=self.quiz,
            step_index=self.participation.current_step
        )

    def update_base_participation(self):
        self.base_participation.correct_answers = self.quiz.question_count
        self.base_participation.wrong_answers = self.participation.wrong_attempts
        self.complete_participation()

    def submit_answer(self, user_words: list[str]) -> dict:
        self.check_deadline()
        self.check_participation_status()

        chunk = self.get_chunk()
        correct_words = chunk.correct_order

        is_correct = (
                len(user_words) == len(correct_words)
                and all(u == c for u, c in zip(user_words, correct_words))
        )

        if is_correct:
            if self.participation.current_step == self.participation.total_steps:
                self.update_base_participation()
                self.update_leaderboard()
                return {
                    'result': 'quiz_completed',
                    'data': BaseParticipationReviewSerializer(self.base_participation).data
                }

            self.participation.current_step += 1
            self.participation.save(update_fields=['current_step'])
            next_chunk = self.get_chunk()
            return {
                'result': 'correct',
                'data': OrderingChunkSerializer(next_chunk).data
            }

        else:
            self.participation.wrong_attempts += 1
            self.participation.save(update_fields=['wrong_attempts'])
            return {
                'result': 'wrong',
                'data': OrderingChunkSerializer(chunk).data
            }
