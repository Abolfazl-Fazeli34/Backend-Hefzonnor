from rest_framework import serializers
from account.models import Profile


class OTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 11 or not value.startswith("09"):
            raise serializers.ValidationError("Enter a valid 11-digit phone number.")
        return value


class OTPVerifySerializer(OTPRequestSerializer):
    otp = serializers.CharField(max_length=6)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "first_name", "last_name", "total_score", "diamonds_count", "level", "current_league", "age", "province", "gender"]

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "first_name", "last_name","age", "gender", "province"]
