from django.shortcuts import get_object_or_404

from exam.models import MatchingParticipation, MatchingChunk, \
    MatchingParticipationChunkProgress
from exam.serializers import BaseParticipationReviewSerializer, \
    MatchingChunkSerializer
from exam.services.participation.base_submission import BaseSubmissionService


class MatchingSubmissionService(BaseSubmissionService):
    def __init__(self, participation: MatchingParticipation, pairs: list,
                 chunk_progress: MatchingParticipationChunkProgress, chunk: MatchingChunk):
        super().__init__(participation.participation)
        self.participation = participation
        self.pairs = pairs
        self.chunk_progress = chunk_progress
        self.chunk = chunk

    def get_chunk(self) -> MatchingChunk:
        return get_object_or_404(
            MatchingChunk,
            quiz=self.quiz,
            step_index=self.participation.current_step
        )

    def submit_answer(self) -> dict:
        self.check_deadline()
        self.check_participation_status()

        chunk = self.chunk
        correct_pairs = chunk.correct_matches
        matched_pairs = self.chunk_progress.matched_pairs.copy()

        newly_correct = []
        wrong_pairs = []

        for left, right in self.pairs:
            if [left, right] in matched_pairs:
                continue
            if [left, right] in correct_pairs:
                matched_pairs.append([left, right])
                newly_correct.append({'left': left, 'right': right})
            else:
                wrong_pairs.append({'left': left, 'right': right})

        self.chunk_progress.matched_pairs = matched_pairs
        self.chunk_progress.save()

        chunk_completed = self.is_chunk_fully_completed(correct_pairs, matched_pairs)

        if chunk_completed:
            quiz_completed = self.advance_step()
            if quiz_completed:
                return {
                    'status': 'quiz_completed',
                    'result': BaseParticipationReviewSerializer(self.base_participation).data
                }

            chunk = self.get_chunk()
            return {
                'status': 'chunk_completed',
                'chunk': MatchingChunkSerializer(chunk).data
            }

        return {
            "status": 'wrong_answers',
            "wrong_pairs": wrong_pairs
        }

    def is_chunk_fully_completed(self, correct_pairs: list, matched_pairs: list) -> bool:
        return set(tuple(p) for p in correct_pairs) == set(tuple(p) for p in matched_pairs)

    def advance_step(self) -> bool:
        if self.participation.current_step >= self.participation.total_steps:
            self.complete_participation()
            return True

        self.participation.current_step += 1
        self.participation.save()
        return False
