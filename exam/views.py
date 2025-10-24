from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet

from utils import status
from utils.response import custom_response
from .choices import QuizCategory
from .models import Quiz, BaseParticipation, QuizLeaderboard, \
    MultipleChoiceParticipation, OrderingParticipation, OrderingChunk, MultipleChoiceQuestion, MatchingChunk, \
    MatchingParticipation, MatchingParticipationChunkProgress, TypingParticipation, \
    TypingQuestion
from .permissions import IsAdminOrReadOnly, HasCompleteProfile
from .serializers import QuizSerializer, BaseParticipationSerializer, UpdateCreateQuizSerializer, \
    CreateParticipationSerializer, MCParticipationReviewSerializer, QuizLeaderboardSerializer, \
    MultipleChoiceParticipationSerializer, OrderingChunkSerializer, \
    OrderingAnswerSerializer, OrderingParticipationSerializer, MultipleChoiceQuestionSerializer, \
    MatchingParticipationSerializer, MatchingChunkSerializer, MatchingAnswerSerializer, TypingQuestionSerializer, \
    TypingParticipationSerializer, TypingAnswerSubmissionSerializer
from .services.participation import MCParticipationRestartService, MCParticipationSubmissionService, \
    OrderingParticipationRestartService, OrderingSubmissionService, MatchingSubmissionService, \
    MatchingParticipationRestartService, TypingParticipationRestartService, TypingAnswerSubmissionService
from .services.question_factory.matching.matching_chunk_generator import MatchingChunkGenerator
from .services.question_factory.multiple_choice.subtype_dispatcher import generate_questions as generate_mc_questions
from .services.question_factory.ordering.ordering_chunk_generator import ordering_subtype_dispatcher
from .services.question_factory.typing.typing_question_generator import CommonTypingQuestionGenerator, \
    MiddleWordTypingQuestionGenerator


class QuizViewSet(ModelViewSet):
    queryset = Quiz.objects.prefetch_related('subtypes').select_related('start_verse', 'end_verse').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT']:
            return UpdateCreateQuizSerializer
        return QuizSerializer

class QuizLeaderboardViewSet(ReadOnlyModelViewSet):
    serializer_class = QuizLeaderboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_pk')
        return QuizLeaderboard.objects.filter(quiz_id=quiz_id).order_by('rank')


class ParticipationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, HasCompleteProfile]
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateParticipationSerializer
        return BaseParticipationSerializer

    def get_queryset(self):
        queryset = (
            BaseParticipation.objects
            .select_related('quiz__start_verse', 'quiz__end_verse', 'quiz')
            .prefetch_related('quiz__subtypes')
            .prefetch_related('quiz__chunks')
            .all()
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        participation = self.get_queryset().get(pk=serializer.instance.pk)
        output_serializer = BaseParticipationSerializer(participation, context=self.get_serializer_context())
        return custom_response(
            data={
                'participation': output_serializer.data,
            },
            status_code=status.CREATED_201
        )

    def perform_create(self, serializer):
        with transaction.atomic():
            participation = serializer.save(user=self.request.user)
            quiz = participation.quiz

            if quiz.category == QuizCategory.MULTIPLE_CHOICE:
                multiple_choice_participation = MultipleChoiceParticipation.objects.create(participation=participation)
                generate_mc_questions(participation=multiple_choice_participation, quiz=quiz)
            elif quiz.category == QuizCategory.ORDERING:
                chunk_count = len(quiz.chunks.all())
                OrderingParticipation.objects.create(participation=participation, total_steps=chunk_count)
            elif quiz.category == QuizCategory.MATCHING:
                chunk_count = len(quiz.matching_chunks.all())
                MatchingParticipation.objects.create(participation=participation, total_steps=chunk_count)
            elif quiz.category == QuizCategory.TYPING:
                total_steps = len(quiz.typing_questions.all())
                typing_participation = TypingParticipation.objects.create(participation=participation,
                                                                          total_steps=total_steps)
                generator = MiddleWordTypingQuestionGenerator(typing_participation)
                if quiz.subtypes.first().code == 13:
                    generator.generate()

        return participation


class MultipleChoiceParticipationViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = MultipleChoiceParticipation.objects.prefetch_related('questions', 'questions__options').all()

    def get_serializer_class(self):
        if self.action == 'question':
            return MultipleChoiceQuestionSerializer
        elif self.action == 'restart':
            return BaseParticipationSerializer
        elif self.action == 'submit':
            return MCParticipationReviewSerializer
        else:
            return MultipleChoiceParticipationSerializer

    def get_object(self):
        obj = super().get_object()
        if obj.participation.user != self.request.user:
            raise PermissionDenied()
        return obj

    @action(detail=True, methods=['get'], url_path='question')
    def question(self, request, pk=None):
        mc_participation = self.get_object()
        base_participation = mc_participation.participation
        quiz = base_participation.quiz

        now = timezone.now()

        if not base_participation.started_at or not base_participation.deadline:
            base_participation.started_at = now
            base_participation.deadline = now + timedelta(seconds=quiz.quiz_duration)
            base_participation.save(update_fields=['started_at', 'deadline'])

        if base_participation.deadline < now:
            return custom_response(error={'message': 'the deadline is passed'})

        questions = MultipleChoiceQuestion.objects.prefetch_related('options').filter(participation=mc_participation)
        serializer = self.get_serializer_class()(questions, many=True)
        return custom_response(data=serializer.data)

    @action(detail=True, methods=['patch'], url_path='restart')
    def restart(self, request, pk=None):
        old_mc_participation = self.get_object()
        base_participation = old_mc_participation.participation
        quiz = base_participation.quiz

        service = MCParticipationRestartService(quiz=quiz, old_participation=base_participation, user=request.user)

        try:
            with transaction.atomic():
                new_participation = service.get_participation()
                MultipleChoiceParticipation.objects.filter(participation=new_participation).delete()
                new_mc_participation = MultipleChoiceParticipation.objects.create(participation=new_participation)
                generate_mc_questions(participation=new_mc_participation, quiz=quiz)
        except ValidationError as e:
            return custom_response(error={'detail': str(e.detail)}, status_code=status.BAD_REQUEST_400)

        output_serializer = self.get_serializer_class()(new_mc_participation.participation,
                                                        context={'request': request})
        return custom_response(data=output_serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        mc_participation = self.get_object()

        service = MCParticipationSubmissionService(participation=mc_participation.participation)

        try:
            updated_participation = service.submit_answers(request.data)
        except ValidationError as e:
            return custom_response(error={'detail': str(e.detail)}, status_code=status.BAD_REQUEST_400)

        serializer = self.get_serializer_class()(updated_participation, context={'request': request})
        return custom_response(data={'participation': serializer.data})


class OrderingParticipationViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = OrderingParticipation.objects.select_related('participation__quiz').all()

    def get_serializer_class(self):
        if self.action == 'question':
            return OrderingChunkSerializer
        elif self.action == 'submit':
            return OrderingAnswerSerializer
        elif self.action == 'restart':
            return BaseParticipationSerializer
        else:
            return OrderingParticipationSerializer

    def get_object(self):
        obj = super().get_object()
        if obj.participation.user != self.request.user:
            raise PermissionDenied()
        return obj

    @action(detail=True, methods=['get'], url_path='question')
    def question(self, request, pk=None):
        ordering_participation = self.get_object()
        base_participation = ordering_participation.participation
        quiz = base_participation.quiz

        now = timezone.now()

        if not base_participation.started_at or not base_participation.deadline:
            base_participation.started_at = now
            base_participation.deadline = now + timedelta(seconds=quiz.quiz_duration)
            base_participation.save(update_fields=['started_at', 'deadline'])

        if base_participation.deadline < now:
            return custom_response(error={'message': 'Deadline is passed'}, status_code=status.BAD_REQUEST_400)

        chunk = get_object_or_404(
            OrderingChunk,
            quiz=quiz,
            step_index=ordering_participation.current_step
        )

        serializer = self.get_serializer_class()(chunk)
        return custom_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        ordering_participation = self.get_object()
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_words = serializer.validated_data['words']
        service = OrderingSubmissionService(ordering_participation)
        try:
            result = service.submit_answer(user_words)
        except ValidationError as e:
            return custom_response(
                error={'message': str(e.detail)},
                status_code=status.BAD_REQUEST_400
            )
        return custom_response(data=result)

    @action(detail=True, methods=['patch'], url_path='restart')
    def restart(self, request, pk=None):
        old_ordering_participation = self.get_object()
        base_participation = old_ordering_participation.participation
        quiz = base_participation.quiz
        total_steps = len(quiz.chunks.all())

        service = OrderingParticipationRestartService(
            quiz=quiz,
            old_participation=base_participation,
            user=request.user
        )

        try:
            with transaction.atomic():
                new_participation = service.get_participation()
                OrderingParticipation.objects.filter(participation=new_participation).delete()
                new_ordering_participation = OrderingParticipation.objects.create(
                    participation=new_participation,
                    total_steps=total_steps
                )
        except ValidationError as e:
            return custom_response(error={'detail': str(e.detail)}, status_code=status.BAD_REQUEST_400)

        serializer = self.get_serializer_class()(new_ordering_participation.participation, context={'request': request})
        return custom_response(data=serializer.data)


class MatchingParticipationViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = MatchingParticipation.objects.select_related('participation__quiz').all()

    def get_serializer_class(self):
        if self.action == 'question':
            return MatchingChunkSerializer
        elif self.action == 'submit':
            return MatchingAnswerSerializer
        elif self.action == 'restart':
            return BaseParticipationSerializer
        else:
            return MatchingParticipationSerializer

    def get_object(self):
        obj = super().get_object()
        if obj.participation.user != self.request.user:
            raise PermissionDenied()
        return obj

    @action(detail=True, methods=['get'], url_path='question')
    def question(self, request, pk=None):
        matching_participation = self.get_object()
        base_participation = matching_participation.participation
        quiz = base_participation.quiz

        now = timezone.now()

        if not base_participation.started_at or not base_participation.deadline:
            base_participation.started_at = now
            base_participation.deadline = now + timedelta(seconds=quiz.quiz_duration)
            base_participation.save(update_fields=['started_at', 'deadline'])

        if base_participation.deadline < now:
            return custom_response(error={'message': 'Deadline is passed'}, status_code=status.BAD_REQUEST_400)

        chunk = get_object_or_404(
            MatchingChunk,
            quiz=quiz,
            step_index=matching_participation.current_step
        )

        serializer = self.get_serializer_class()(chunk)

        return custom_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        participation = self.get_object()
        base_participation = participation.participation
        quiz = base_participation.quiz

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        chunk = MatchingChunk.objects.get(quiz=quiz, step_index=participation.current_step)

        chunk_progress, _ = MatchingParticipationChunkProgress.objects.get_or_create(
            participation=participation,
            chunk=chunk,
            defaults={"matched_pairs": []}
        )

        service = MatchingSubmissionService(
            participation=participation,
            pairs=[(p['left'], p['right']) for p in serializer.validated_data['pairs']],
            chunk_progress=chunk_progress,
            chunk=chunk,
        )

        result = service.submit_answer()
        return custom_response(data=result)

    @action(detail=True, methods=['patch'], url_path='restart')
    def restart(self, request, pk=None):
        old_matching_participation = self.get_object()
        base_participation = old_matching_participation.participation
        quiz = base_participation.quiz
        total_steps = len(quiz.chunks.all())

        service = MatchingParticipationRestartService(
            quiz=quiz,
            old_participation=base_participation,
            user=request.user
        )

        try:
            with transaction.atomic():
                new_participation = service.get_participation()
                MatchingParticipation.objects.filter(participation=new_participation).delete()
                new_ordering_participation = MatchingParticipation.objects.create(
                    participation=new_participation,
                    total_steps=total_steps
                )
        except ValidationError as e:
            return custom_response(error={'detail': e.detail}, status_code=status.BAD_REQUEST_400)

        serializer = self.get_serializer_class()(new_ordering_participation.participation, context={'request': request})
        return custom_response(data=serializer.data)


class TypingParticipationViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = TypingParticipation.objects.all()

    def get_serializer_class(self):
        if self.action == 'submit':
            return TypingAnswerSubmissionSerializer
        elif self.action == 'question':
            return TypingQuestionSerializer
        elif self.action == 'restart':
            return BaseParticipationSerializer
        else:
            return TypingParticipationSerializer

    def get_object(self):
        obj = super().get_object()
        if obj.participation.user != self.request.user:
            raise PermissionDenied()
        return obj

    @action(detail=True, methods=['get'], url_path='question')
    def question(self, request, pk=None):
        participation = self.get_object()
        base_participation = participation.participation
        quiz = base_participation.quiz

        now = timezone.now()
        if not base_participation.started_at or not base_participation.deadline:
            base_participation.started_at = now
            base_participation.deadline = now + timedelta(seconds=quiz.quiz_duration)
            base_participation.save()

        if base_participation.deadline < now:
            return custom_response(error={'message': 'The deadline is passed'})

        question = get_object_or_404(TypingQuestion.objects.filter(Q(quiz=quiz) | Q(participation=participation)),
                                     step_index=participation.current_step)
        serializer = self.get_serializer_class()(question)

        return custom_response(data=serializer.data)

    @action(detail=True, methods=['patch'], url_path='restart')
    def restart(self, request, pk=None):
        old_typing_participation = self.get_object()
        base_participation = old_typing_participation.participation
        quiz = base_participation.quiz
        total_steps = len(quiz.chunks.all())

        service = TypingParticipationRestartService(
            quiz=quiz,
            old_participation=base_participation,
            user=request.user
        )

        try:
            with transaction.atomic():
                new_participation = service.get_participation()
                TypingParticipation.objects.filter(participation=new_participation).delete()
                new_typing_participation = TypingParticipation.objects.create(
                    participation=new_participation,
                    total_steps=total_steps
                )
                if quiz.subtypes.first().code == 13:
                    generator = MiddleWordTypingQuestionGenerator(new_typing_participation)
                    generator.generate()
        except ValidationError as e:
            return custom_response(error={'detail': str(e.detail)}, status_code=status.BAD_REQUEST_400)

        serializer = self.get_serializer_class()(new_typing_participation.participation, context={'request': request})
        return custom_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        participation = self.get_object()
        service = TypingAnswerSubmissionService(participation)
        question = service.get_current_question()
        answer_serializer = TypingAnswerSubmissionSerializer(data=request.data,
                                                             context={'question_type': question.template.code})
        answer_serializer.is_valid(raise_exception=True)
        user_input = answer_serializer.data['answer']
        result = service.submit(user_input)
        return custom_response(data=result)
