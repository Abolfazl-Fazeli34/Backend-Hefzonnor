from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, connection

from quran.models import Verse
from .choices import QuizCategory, ProvinceChoices, ParticipationStatus


class QuizSubtype(models.Model):
    category = models.CharField(max_length=20, choices=QuizCategory.choices)
    title = models.CharField(max_length=100)
    code = models.PositiveSmallIntegerField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'({self.category}){self.title}'


class QuestionTemplate(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    subtype = models.ForeignKey(QuizSubtype, on_delete=models.CASCADE, related_name='templates')
    difficulty = models.IntegerField(default=0)
    question_from = models.CharField(max_length=100, null=True, blank=True)
    answer_from = models.CharField(max_length=100, null=True, blank=True)
    code = models.PositiveSmallIntegerField(unique=True)

    def __str__(self):
        return f'ask from:{self.question_from}, answer: {self.answer_from}'


class Quiz(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=QuizCategory.choices)
    subtypes = models.ManyToManyField(QuizSubtype)
    start_verse = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='quiz_started')
    end_verse = models.ForeignKey(Verse, on_delete=models.PROTECT, related_name='quiz_ended')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    quiz_start_datetime = models.DateTimeField()
    quiz_end_datetime = models.DateTimeField()
    quiz_duration = models.PositiveIntegerField()
    is_public = models.BooleanField(default=False)
    auto_generate = models.BooleanField(default=True)
    question_count = models.PositiveIntegerField(null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quizzes')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='quizzes_joined',
                                          through='exam.BaseParticipation')
    allow_multiple_attempts = models.BooleanField(default=False)
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True, choices=ProvinceChoices.choices)
    is_scoring_enabled = models.BooleanField(default=False)
    correct_answer_score = models.PositiveIntegerField(null=True, blank=True)
    negative_score = models.PositiveIntegerField(null=True, blank=True)
    participation_score = models.PositiveIntegerField(null=True, blank=True)
    top_three_bonus = models.PositiveIntegerField(null=True, blank=True)
    top_ten_bonus = models.PositiveIntegerField(null=True, blank=True)
    chunk_size = models.PositiveIntegerField(default=7)


class BaseParticipation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quiz_participations')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='participations')
    correct_answers = models.PositiveSmallIntegerField(default=0)
    wrong_answers = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    excluded_from_leaderboard = models.BooleanField(default=False)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(choices=ParticipationStatus.choices, default=ParticipationStatus.INCOMPLETE,
                              max_length=20)


class MultipleChoiceParticipation(models.Model):
    participation = models.OneToOneField(BaseParticipation, on_delete=models.CASCADE,
                                         related_name='multiple_choice_participation')
    not_answered = models.PositiveSmallIntegerField(default=0)


class MultipleChoiceQuestion(models.Model):
    title = models.CharField(max_length=500)
    template = models.ForeignKey(QuestionTemplate, on_delete=models.CASCADE, related_name='questions')
    participation = models.ForeignKey(MultipleChoiceParticipation, on_delete=models.CASCADE, related_name='questions')


class Option(models.Model):
    number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)


class MultipleChoiceAnswer(models.Model):
    participation = models.ForeignKey(MultipleChoiceParticipation, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True, blank=True)


class QuizLeaderboardManager(models.Manager):
    def refresh_view(self):
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY quiz_leaderboard;")


class QuizLeaderboard(models.Model):
    id = models.BigIntegerField(primary_key=True)
    quiz_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    correct_answers = models.IntegerField()
    wrong_answers = models.IntegerField()
    total_score = models.IntegerField()
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField()
    time_spent = models.DurationField()
    rank = models.IntegerField()

    objects = QuizLeaderboardManager()

    class Meta:
        managed = False
        db_table = 'quiz_leaderboard'


class OrderingParticipation(models.Model):
    participation = models.OneToOneField(BaseParticipation, on_delete=models.CASCADE,
                                         related_name='ordering_participation')
    total_steps = models.PositiveIntegerField()
    current_step = models.PositiveIntegerField(default=1)
    wrong_attempts = models.PositiveIntegerField(default=0)


class OrderingChunk(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='chunks')
    correct_order = models.JSONField(models.CharField(max_length=200))
    step_index = models.PositiveIntegerField()


class MatchingParticipation(models.Model):
    participation = models.OneToOneField(BaseParticipation, on_delete=models.CASCADE,
                                         related_name='matching_participation')
    total_steps = models.PositiveIntegerField()
    current_step = models.PositiveIntegerField(default=1)
    wrong_attempts = models.PositiveIntegerField(default=0)


class MatchingChunk(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='matching_chunks')
    step_index = models.PositiveIntegerField()
    left_items = models.JSONField()
    right_items = models.JSONField()
    correct_matches = models.JSONField()


class MatchingParticipationChunkProgress(models.Model):
    participation = models.ForeignKey(MatchingParticipation, on_delete=models.CASCADE, related_name='chunk_progress')
    chunk = models.ForeignKey(MatchingChunk, on_delete=models.CASCADE)
    matched_pairs = models.JSONField()

    class Meta:
        unique_together = ('participation', 'chunk')


class TypingParticipation(models.Model):
    participation = models.OneToOneField(BaseParticipation, on_delete=models.CASCADE,
                                         related_name='typing_participation')
    total_steps = models.PositiveIntegerField(default=0)
    current_step = models.PositiveIntegerField(default=1)
    not_answered_count = models.PositiveIntegerField(default=0)


class TypingQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='typing_questions', null=True, blank=True)
    participation = models.ForeignKey(TypingParticipation, on_delete=models.CASCADE, related_name='questions',
                                      null=True, blank=True)
    template = models.ForeignKey(QuestionTemplate, on_delete=models.PROTECT, related_name='typing_questions')
    title = models.TextField()
    answer = models.JSONField()
    step_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TypingSubmittedAnswer(models.Model):
    question = models.ForeignKey(TypingQuestion, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='submitted_answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
