import random

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from exam.choices import QuizCategory
from exam.models import Quiz, QuizSubtype, BaseParticipation, MultipleChoiceQuestion, Option, MultipleChoiceAnswer, \
    QuizLeaderboard, MultipleChoiceParticipation, OrderingChunk, OrderingParticipation, MatchingParticipation, \
    MatchingChunk, TypingQuestion, TypingParticipation
from quran.models import Verse

User = get_user_model()


# quiz serializers
class VerseInputSerializer(serializers.Serializer):
    surah_number = serializers.IntegerField(source='surah_id')
    verse_number = serializers.IntegerField()

    def to_internal_value(self, data):
        validated_data = super(VerseInputSerializer, self).to_internal_value(data)
        try:
            verse = Verse.objects.filter(surah_id=validated_data['surah_id']).get(
                verse_number=validated_data['verse_number'])
        except Verse.DoesNotExist:
            raise serializers.ValidationError("Verse with given surah and verse number does not exist.")
        return verse


class QuizSerializer(serializers.ModelSerializer):
    start_verse = VerseInputSerializer(read_only=True)
    end_verse = VerseInputSerializer(read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'category', 'subtypes', 'start_verse', 'end_verse',
                  'is_active', 'quiz_start_datetime', 'quiz_end_datetime', 'quiz_duration',
                  'question_count', 'allow_multiple_attempts', 'min_age', 'max_age',
                  'province', 'is_scoring_enabled', 'correct_answer_score', 'negative_score',
                  'participation_score', 'top_three_bonus', 'top_ten_bonus']


class UpdateCreateQuizSerializer(serializers.ModelSerializer):
    start_verse = VerseInputSerializer(required=True)
    end_verse = VerseInputSerializer(required=True)
    subtypes = serializers.PrimaryKeyRelatedField(
        queryset=QuizSubtype.objects.all(),
        required=True,
        allow_null=False,
        many=True
    )

    class Meta:
        model = Quiz
        exclude = ['is_active', 'creator', 'auto_generate', 'is_public']

    def validate(self, data):
        start_verse = data['start_verse']
        end_verse = data['end_verse']
        quiz_start_datetime = data['quiz_start_datetime']
        quiz_end_datetime = data['quiz_end_datetime']
        subtypes = data['subtypes']
        question_count = data['question_count']
        is_scoring_enabled = data['is_scoring_enabled']
        category = data['category']

        if start_verse.id > end_verse.id:
            raise serializers.ValidationError({
                'verse_range': 'Start verse must be smaller than end verse'
            })

        if quiz_start_datetime >= quiz_end_datetime:
            raise serializers.ValidationError({
                'time_range': 'Start time must be strictly before end time'
            })

        if quiz_start_datetime < timezone.now():
            raise serializers.ValidationError({
                'quiz_start_datetime': 'Start datetime must be in the future'
            })

        if not subtypes:
            raise serializers.ValidationError({
                'subtypes': 'Subtypes must be provided'
            })

        if subtypes and category:
            invalid_subtypes = [s for s in subtypes if s.category != category]
            if invalid_subtypes:
                raise serializers.ValidationError({
                    'subtypes': f"All selected subtypes must belong to the category '{category}'."
                })

        if category == 'multiple_choice' or (category == 'typing' and subtypes and subtypes[0] == 13):
            if not question_count:
                raise serializers.ValidationError({
                    'question_count': 'Question count is required for multiple-choice or typing with subtype 13.'
                })
            if question_count < 1 or question_count > 100:
                raise serializers.ValidationError({
                    'question_count': 'Question count must be between 1 and 100.'
                })
            if category == 'typing' and subtypes and subtypes[0] == 13:
                max_questions = end_verse.id - start_verse.id + 1
                data['question_count'] = min(question_count, max_questions)
        else:
            if len(subtypes) > 1:
                raise serializers.ValidationError({
                    'subtypes': 'Only one subtype is allowed for this category.'
                })
            data['question_count'] = end_verse.id - start_verse.id + 1

        if is_scoring_enabled:
            score_fields = ['correct_answer_score', 'negative_score', 'participation_score', 'top_three_bonus',
                            'top_ten_bonus']
            for field in score_fields:
                if field not in data or data[field] is None:
                    raise serializers.ValidationError({
                        f'{field}': f"{field} must be set if scoring is enabled."
                    })

        return data

    def create(self, validated_data):
        creator = self.context['request'].user
        subtypes = validated_data.pop('subtypes')
        start_verse = validated_data.pop('start_verse')
        end_verse = validated_data.pop('end_verse')

        quiz = Quiz.objects.create(
            **validated_data,
            creator=creator,
            start_verse=start_verse,
            end_verse=end_verse,
        )
        quiz.subtypes.set(subtypes)

        return quiz


# base participation serializers
class BaseParticipationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    questions_link = serializers.SerializerMethodField()
    sub_participation = serializers.SerializerMethodField()

    class Meta:
        model = BaseParticipation
        fields = ['id', 'user', 'correct_answers', 'wrong_answers', 'total_score', 'status', 'quiz', 'questions_link',
                  'sub_participation']
        read_only_fields = ['correct_answers', 'wrong_answers', 'submitted_at', 'total_score', 'status', 'quiz',
                            'sub_participation']

    def get_questions_link(self, obj: BaseParticipation):
        category = obj.quiz.category
        request = self.context.get('request')
        if category == QuizCategory.MULTIPLE_CHOICE:
            return reverse(
                'multiplechoice-question',
                kwargs={'pk': obj.multiple_choice_participation.id},
                request=request
            )
        elif category == QuizCategory.ORDERING:
            return reverse(
                'ordering-question',
                kwargs={'pk': obj.ordering_participation.id},
                request=request
            )
        elif category == QuizCategory.MATCHING:
            return reverse(
                'matching-question',
                kwargs={'pk': obj.matching_participation.id},
                request=request,
            )
        elif category == QuizCategory.TYPING:
            return reverse(
                'typing-question',
                kwargs={'pk': obj.typing_participation.id},
                request=request
            )
        return None

    def get_sub_participation(self, obj):
        if hasattr(obj, 'ordering_participation'):
            return {
                'type': 'ordering',
                'data': OrderingParticipationSerializer(obj.ordering_participation).data
            }
        elif hasattr(obj, 'matching_participation'):
            return {
                'type': 'matching',
                'data': MatchingParticipationSerializer(obj.matching_participation).data
            }
        elif hasattr(obj, 'multiple_choice_participation'):
            return {
                'type': 'multiple_choice',
                'data': MultipleChoiceParticipationSerializer(obj.multiple_choice_participation).data
            }
        elif hasattr(obj, 'typing_participation'):
            return {
                'type': 'typing',
                'data': TypingParticipationSerializer(obj.typing_participation).data
            }
        else:
            return None


class CreateParticipationSerializer(serializers.ModelSerializer):
    quiz = serializers.PrimaryKeyRelatedField(queryset=Quiz.objects.all(), write_only=True)

    class Meta:
        model = BaseParticipation
        fields = ['id', 'quiz']

    def validate_quiz(self, quiz):
        if not quiz.is_active:
            raise serializers.ValidationError("This quiz is not active.")
        return quiz

    def validate(self, data):
        user = self.context['request'].user
        quiz = data['quiz']

        if BaseParticipation.objects.filter(quiz=quiz, user=user).exists():
            raise serializers.ValidationError('You are already participating in this quiz.')

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# multiple choice serializers
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'number', 'text']


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(read_only=True, many=True)

    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'title', 'options']


class MultipleChoiceParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceParticipation
        fields = ['id', 'participation', 'not_answered']


class SingleAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_option_id = serializers.IntegerField(allow_null=True, required=True)

    def validate_question_id(self, value):
        valid_ids = self.context.get('valid_question_ids')
        if value not in valid_ids:
            raise serializers.ValidationError('Invalid question id for this participation.')
        return value

    def validate(self, attrs):
        question_id = attrs['question_id']
        selected_option_id = attrs.get('selected_option_id')
        if selected_option_id is not None:
            option_map = self.context['valid_option_map']
            valid_options = option_map.get(question_id, set())
            if selected_option_id not in valid_options:
                raise serializers.ValidationError({
                    'selected_option_id': f'Invalid option for the given question with ID {question_id}. The options are {", ".join(map(str, valid_options))}.'
                })
        return attrs


class AnswerSubmissionSerializer(serializers.Serializer):
    answers = SingleAnswerSerializer(many=True, required=True)

    def validate_answers(self, value):
        expected_count = self.context.get('expected_question_count')
        actual_count = len(value)

        if actual_count != expected_count:
            raise serializers.ValidationError({
                'answers': f'Expected {expected_count} answers (including unanswered), but got {actual_count}.'
            })

        seen = set()
        for item in value:
            qid = item['question_id']
            if qid in seen:
                raise serializers.ValidationError({
                    'answers': f'Duplicate answer for question ID {qid}'
                })
            seen.add(qid)
        return value


# review serializers
class BaseParticipationReviewSerializer(serializers.ModelSerializer):
    time_spent = serializers.SerializerMethodField()

    class Meta:
        model = BaseParticipation
        fields = ['id', 'correct_answers', 'wrong_answers', 'total_score', 'time_spent']

    def get_time_spent(self, participation):
        return participation.submitted_at - participation.started_at


class OptionWithAnswerSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    is_correct = serializers.BooleanField()

    class Meta:
        model = Option
        fields = ['id', 'number', 'text', 'is_correct', 'is_selected']

    def get_is_selected(self, option):
        question = self.context.get('question')
        user_answers_id = self.context.get('user_answers_id')

        return user_answers_id.get(question.id) == option.id


class QuestionReviewSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = MultipleChoiceQuestion
        fields = ['id', 'title', 'options']

    def get_options(self, question):
        return OptionWithAnswerSerializer(
            question.options.all(),
            many=True,
            context={
                'question': question,
                'user_answers_id': self.context.get('user_answers_id', {}),
            }
        ).data


class MCParticipationReviewSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    time_spent = serializers.SerializerMethodField()
    not_answered = serializers.IntegerField(source='multiple_choice_participation.not_answered')

    class Meta:
        model = BaseParticipation
        fields = ['id', 'correct_answers', 'wrong_answers', 'not_answered', 'total_score', 'questions', 'time_spent']

    def get_time_spent(self, participation):
        return participation.submitted_at - participation.started_at

    def get_questions(self, participation):
        answers = MultipleChoiceAnswer.objects.filter(participation=participation.multiple_choice_participation)
        user_answers_id = {a.question.id: a.selected_option.id for a in answers}

        return QuestionReviewSerializer(
            participation.multiple_choice_participation.questions.all(),
            many=True,
            context={'user_answers_id': user_answers_id}
        ).data


# leader board serializer
class QuizLeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizLeaderboard
        fields = ['user_id', 'rank', 'correct_answers', 'wrong_answers', 'total_score', 'time_spent']


# ordering serializers
class OrderingParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderingParticipation
        fields = ['id', 'total_steps', 'current_step', 'wrong_attempts']


class OrderingChunkSerializer(serializers.ModelSerializer):
    shuffled_word = serializers.SerializerMethodField()

    class Meta:
        model = OrderingChunk
        fields = ['id', 'step_index', 'shuffled_word']

    def get_shuffled_word(self, chunk):
        words = chunk.correct_order[:]
        shuffled = words[:]

        if len(shuffled) <= 1:
            return shuffled

        random.shuffle(shuffled)
        return shuffled


class OrderingAnswerSerializer(serializers.Serializer):
    words = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )


# matching serializers
class MatchingParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingParticipation
        fields = ['id', 'total_steps', 'current_step', 'wrong_attempts']


class MatchingChunkSerializer(serializers.ModelSerializer):
    shuffled_left_items = serializers.SerializerMethodField()
    shuffled_right_items = serializers.SerializerMethodField()

    class Meta:
        model = MatchingChunk
        fields = ['shuffled_left_items', 'shuffled_right_items']

    def get_shuffled_left_items(self, matching_participation):
        left_items = matching_participation.left_items
        shuffled = left_items[:]

        if len(shuffled) <= 1:
            return shuffled
        random.shuffle(shuffled)
        return shuffled

    def get_shuffled_right_items(self, matching_participation):
        right_items = matching_participation.right_items
        shuffled = right_items[:]

        if len(shuffled) <= 1:
            return shuffled
        random.shuffle(shuffled)
        return shuffled


class MatchingAnswerSerializer(serializers.Serializer):
    pairs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
        ),
    )

    def validate_pairs(self, value):
        if not all("left" in pair and "right" in pair for pair in value):
            raise serializers.ValidationError("Each pair must have 'left' and 'right'.")
        return value


# typing serializer
class TypingParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypingParticipation
        fields = ['id', 'total_steps', 'current_step']


class TypingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypingQuestion
        fields = ['title']


class TypingAnswerField(serializers.Field):
    def to_internal_value(self, data):
        question_type = None
        if self.parent.context:
            question_type = self.context.get('question_type')

        if question_type == 140:
            if not isinstance(data, list):
                raise serializers.ValidationError("Expected a list of strings.")
            if not all(isinstance(item, str) for item in data):
                raise serializers.ValidationError("All items must be strings.")
            return data
        else:
            if not isinstance(data, str):
                raise serializers.ValidationError("Expected a string.")
            return data

    def to_representation(self, value):
        return value


class TypingAnswerSubmissionSerializer(serializers.Serializer):
    answer = TypingAnswerField()
