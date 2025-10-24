from exam.models import BaseParticipation


def calculate_score(participation: BaseParticipation):
    corrects_count = participation.correct_answers
    wrongs_count = participation.wrong_answers

    correct_answer_score = participation.quiz.correct_answer_score
    negative_score = participation.quiz.negative_score
    participation_score = participation.quiz.participation_score

    total_score = (correct_answer_score * corrects_count) + (negative_score * wrongs_count) + participation_score

    return total_score
