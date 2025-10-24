from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from exam.choices import ParticipationStatus
from exam.models import BaseParticipation


class BaseRestartService:
    def __init__(self, user, quiz, old_participation=None):
        self.user = user
        self.quiz = quiz
        self.old_participation = old_participation

    def _check_quiz_active(self):
        if not self.quiz.is_active:
            raise ValidationError("This quiz is not currently active.")

    def _check_deadline(self):
        if self.old_participation.deadline and timezone.now() > self.old_participation.deadline:
            raise ValidationError("The deadline for this quiz has passed.")

    def _check_last_participation_exists(self):
        queryset = BaseParticipation.objects.filter(quiz=self.quiz, user=self.user).exclude(
            status=ParticipationStatus.COMPLETED)
        if self.old_participation:
            queryset = queryset.exclude(pk=self.old_participation.pk)
        return queryset.exists()

    def create_new_participation(self):
        if self._check_last_participation_exists():
            raise ValidationError(
                "You already have an completed or incomplete participation for this quiz. Please finish it before restarting or restart that quiz.")

        return BaseParticipation.objects.create(
            user=self.user,
            quiz=self.quiz,
            status=ParticipationStatus.INCOMPLETE,
            started_at=timezone.now(),
            deadline=timezone.now() + timedelta(seconds=self.quiz.quiz_duration),
        )

    def restart_existing_participation(self):
        self.old_participation.started_at = None
        self.old_participation.deadline = None
        self.old_participation.status = ParticipationStatus.INCOMPLETE
        self.old_participation.correct_answers = 0
        self.old_participation.wrong_answers = 0
        self.old_participation.total_score = 0

        self.get_subtype_participation().objects.filter(participation=self.old_participation).delete()
        self.old_participation.save()
        return self.old_participation

    def get_participation(self):
        self._check_quiz_active()

        if not self.old_participation:
            return self.create_new_participation()

        if self.old_participation.status == ParticipationStatus.COMPLETED:
            if not self.quiz.allow_multiple_attempts:
                raise ValidationError("Multiple attempts are not allowed.")
            return self.create_new_participation()

        if self.quiz.allow_multiple_attempts:
            return self.restart_existing_participation()

        self._check_deadline()
        return self.old_participation

    def get_subtype_participation(self):
        raise NotImplementedError()
