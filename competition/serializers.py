from account.models import Profile
from .models import League, DivisionMembership, Week, Division
from rest_framework import serializers

class LeagueSerializer(serializers.ModelSerializer):
    current = serializers.SerializerMethodField()

    class Meta:
        model = League
        fields = ['id', 'name', 'order', 'promote_rate', 'demote_rate', 'promotion_minimum_score', 'current']

    def get_current(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            profile = user.profile
            return profile.current_league_id == obj.id
        return False


class LeagueLeaderboardProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'total_score', 'first_name', 'last_name', 'level']


class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = ['id', 'start_date', 'end_date', 'status', 'week_number', 'year']


class DivisionSerializer(serializers.ModelSerializer):
    league = LeagueSerializer(read_only=True)
    week = WeekSerializer(read_only=True)

    class Meta:
        model = Division
        fields = ['id', 'league', 'week', 'size']


class DivisionMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = DivisionMembership
        fields = ['id', 'user', 'weekly_score', 'rank_in_division', 'promotion_status']