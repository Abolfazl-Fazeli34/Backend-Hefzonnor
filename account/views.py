from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from account.services.otp_service import OTPService

from account.serializers import OTPRequestSerializer, OTPVerifySerializer, ProfileSerializer, UpdateProfileSerializer
from utils import status
from utils.response import custom_response
from .models import User


class OTPRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']

        otp_service = OTPService(phone_number)
        otp = otp_service.generate()
        otp_service.send(otp)

        return custom_response(data={f'message': f'OTP send to {phone_number}'}, status_code=status.OK_200)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp']

        otp_service = OTPService(phone_number)
        valid, message = otp_service.verify(otp_code)
        if not valid:
            return custom_response(data={"detail": message}, status_code=status.BAD_REQUEST_400)


        user, created = User.objects.get_or_create(phone_number=phone_number)

        refresh = RefreshToken.for_user(user)
        return custom_response(data={
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        },
        status_code=status.CREATED_201 if created else status.OK_200
        )

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        profile = request.user.profile
        serializer = UpdateProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return custom_response(data=serializer.data, status_code=status.OK_200)

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return custom_response(data=serializer.data, status_code=status.OK_200)
