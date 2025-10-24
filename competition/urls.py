from django.urls import path
from rest_framework.routers import DefaultRouter

from competition.views import LeagueViewSet, WeekViewSet, DivisionViewSet

router = DefaultRouter()
router.register('leagues', LeagueViewSet, basename='league')
router.register('weeks', WeekViewSet, basename='week')
router.register('divisions', DivisionViewSet, basename='division')

urlpatterns = router.urls

