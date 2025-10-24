from django.contrib import admin

from .models import QuizSubtype, QuestionTemplate, BaseParticipation


@admin.register(QuizSubtype)
class QuizSubtypeAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'category']


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'subtype', 'question_from', 'answer_from', 'difficulty']


@admin.register(BaseParticipation)
class ParticipationAdmin(admin.ModelAdmin):
    pass
