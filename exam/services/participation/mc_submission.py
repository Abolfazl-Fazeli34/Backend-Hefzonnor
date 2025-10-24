from django.shortcuts import get_object_or_404

from exam.models import BaseParticipation, MultipleChoiceParticipation, MultipleChoiceQuestion, Option, \
    MultipleChoiceAnswer
from exam.serializers import AnswerSubmissionSerializer
from exam.services.participation.base_submission import BaseSubmissionService


class MCParticipationSubmissionService(BaseSubmissionService):
    def __init__(self, participation: BaseParticipation):
        super().__init__(participation)
        self.participation = get_object_or_404(MultipleChoiceParticipation, participation=participation)

    def submit_answers(self, submitted_data):
        self.check_participation_status()
        self.check_deadline()

        questions = MultipleChoiceQuestion.objects.filter(participation=self.participation).prefetch_related('options')
        question_ids = {q.id for q in questions}
        options = Option.objects.filter(question__in=questions)

        option_map = {q.id: set() for q in questions}
        correct_option_map = {}

        for o in options:
            option_map[o.question_id].add(o.id)
            if o.is_correct:
                correct_option_map[o.question_id] = o.id

        serializer = AnswerSubmissionSerializer(
            data=submitted_data,
            context={
                'valid_question_ids': question_ids,
                'valid_option_map': option_map,
                'expected_question_count': self.quiz.question_count
            }
        )
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data['answers']

        answers_to_submit = []
        not_answered_count = 0

        for answer in answers:
            qid = answer['question_id']
            selected_id = answer['selected_option_id']
            correct_id = correct_option_map[qid]

            if selected_id is None:
                not_answered_count += 1
                continue

            is_correct = selected_id == correct_id
            answers_to_submit.append(
                MultipleChoiceAnswer(
                    participation=self.participation,
                    question_id=qid,
                    selected_option_id=selected_id,
                    is_correct=is_correct
                )
            )

            if is_correct:
                self.base_participation.correct_answers += 1
            else:
                self.base_participation.wrong_answers += 1

        MultipleChoiceAnswer.objects.bulk_create(answers_to_submit)
        self.participation.not_answered = not_answered_count
        self.participation.save()

        self.complete_participation()
        self.update_leaderboard()

        return self.base_participation
