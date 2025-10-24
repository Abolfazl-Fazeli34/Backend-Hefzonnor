# exam/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from exam.models import BaseParticipation, Quiz, OrderingChunk, MatchingChunk, TypingQuestion
from exam.choices import QuizCategory
from exam.services.question_factory.matching.matching_chunk_generator import MatchingChunkGenerator
from exam.services.question_factory.ordering.ordering_chunk_generator import ordering_subtype_dispatcher
from competition.models import DivisionMembership, Week
from competition.choices import WeekStatusChoices
from exam.services.question_factory.typing.typing_question_generator import CommonTypingQuestionGenerator


@receiver(post_save, sender=Quiz)
def create_chunks_for_quiz(sender, instance, created, **kwargs):
    quiz = instance

    if quiz.category == QuizCategory.ORDERING:
        chunks = OrderingChunk.objects.filter(quiz=quiz)
        if chunks.exists():
            chunks.delete()
        ordering_subtype_dispatcher(quiz)
    elif quiz.category == QuizCategory.MATCHING:
        chunks = MatchingChunk.objects.filter(quiz=quiz)
        if chunks.exists():
            chunks.delete()
        generator = MatchingChunkGenerator(quiz, chunk_size=quiz.chunk_size)
        generator.generate()
    elif quiz.category == QuizCategory.TYPING and quiz.subtypes.first().code != 13:
        chunks = TypingQuestion.objects.filter(quiz=quiz)
        if chunks.exists():
            chunks.delete()
        generator = CommonTypingQuestionGenerator(quiz)
        generator.generate()


@receiver(post_save, sender=BaseParticipation)
def update_weekly_and_total_scores(sender, instance, created, **kwargs):
    with transaction.atomic():
        participation = instance
        user = participation.user
        profile = getattr(user, "profile", None)
        if not profile:
            return

        if participation.status != "completed":
            return


        previous = (
            BaseParticipation.objects.filter(user=user, quiz=participation.quiz)
            .exclude(id=participation.id)
            .order_by("-total_score")
            .first()
        )

        old_score = previous.total_score if previous else 0
        new_score = participation.total_score

        if new_score <= old_score:
            return

        delta = new_score - old_score

        profile.total_score = F("total_score") + delta
        profile.save(update_fields=["total_score"])

        week = Week.objects.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date(),
            status=WeekStatusChoices.ACTIVE,
        ).first()

        if not week:
            return

        membership = (
            DivisionMembership.objects.select_for_update()
            .filter(user=profile, division__week=week)
            .first()
        )

        if not membership:
            return

        membership.weekly_score = F("weekly_score") + delta
        membership.save(update_fields=["weekly_score"])


