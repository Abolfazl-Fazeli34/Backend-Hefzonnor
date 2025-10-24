from rest_framework_nested import routers

from .views import QuizViewSet, ParticipationViewSet, QuizLeaderboardViewSet, MultipleChoiceParticipationViewSet, \
    OrderingParticipationViewSet, MatchingParticipationViewSet, TypingParticipationViewSet

router = routers.DefaultRouter()
router.register(prefix='quizzes', viewset=QuizViewSet, basename='quiz')
router.register(prefix='participations', viewset=ParticipationViewSet, basename='participation')
router.register(prefix='multiplechoice', viewset=MultipleChoiceParticipationViewSet, basename='multiplechoice')
router.register(prefix='ordering', viewset=OrderingParticipationViewSet, basename='ordering')
router.register(prefix='matching', viewset=MatchingParticipationViewSet, basename='matching')
router.register(prefix='typing', viewset=TypingParticipationViewSet, basename='typing')

quiz_router = routers.NestedDefaultRouter(router, 'quizzes', lookup='quiz')
quiz_router.register('leaderboard', QuizLeaderboardViewSet, basename='quiz-leaderboard')

urlpatterns = router.urls + quiz_router.urls
