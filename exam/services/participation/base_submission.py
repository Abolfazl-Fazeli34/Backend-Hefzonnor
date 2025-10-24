from django.utils import timezone
from rest_framework.exceptions import ValidationError

from exam.choices import ParticipationStatus
from exam.models import BaseParticipation, QuizLeaderboard
from exam.services.scoring import calculate_score


class BaseSubmissionService:
    def __init__(self, base_participation: BaseParticipation):
        self.base_participation = base_participation
        self.quiz = base_participation.quiz
        self.user = base_participation.user

    def check_deadline(self):
        if self.base_participation.deadline and self.base_participation.deadline < timezone.now():
            raise ValidationError("Deadline has passed.")

    def check_participation_status(self):
        if self.base_participation.status == ParticipationStatus.COMPLETED:
            raise ValidationError("Participation is already completed.")

    def complete_participation(self):
        self.base_participation.status = ParticipationStatus.COMPLETED
        self.base_participation.submitted_at = timezone.now()
        if self.quiz.is_scoring_enabled:
            self.base_participation.total_score = calculate_score(self.base_participation)
        self.base_participation.save(
            update_fields=["total_score", "status", "submitted_at", "wrong_answers", "correct_answers"])

    def update_leaderboard(self):
        QuizLeaderboard.objects.refresh_view()
