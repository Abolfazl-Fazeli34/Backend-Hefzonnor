import datetime
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action

from account.models import Profile
from utils import status
from utils.response import custom_response
from .models import League, Week, Division, DivisionMembership
from .paginators import LeaderboardPagination
from .serializers import LeagueSerializer, LeagueLeaderboardProfileSerializer, WeekSerializer, DivisionSerializer, \
    DivisionMembershipSerializer


class LeagueViewSet(ReadOnlyModelViewSet):
    """
    List and retrieve Leagues
    """
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk):
        profiles = (
            Profile.objects.
            filter(current_league_id=pk)
            .order_by('-total_score')
        )
        paginator = LeaderboardPagination()
        page = paginator.paginate_queryset(profiles, request)
        serializer = LeagueLeaderboardProfileSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class WeekViewSet(ReadOnlyModelViewSet):
    queryset = Week.objects.order_by('start_date')
    serializer_class = WeekSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['status']


class DivisionViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DivisionSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['week__week_number', 'week__year']

    def get_queryset(self):
        return Division.objects.filter(
            memberships__user=self.request.user.profile
        ).select_related('league', 'week')

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk):
        members = (
            DivisionMembership.objects.filter(division_id=pk).order_by('-weekly_score')
        )
        paginator = LeaderboardPagination()
        page = paginator.paginate_queryset(members, request)
        serializer = DivisionMembershipSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
