from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from account.views import OTPRequestView, OTPVerifyView, ProfileView

urlpatterns = [
    path('request-otp/', OTPRequestView.as_view(), name='request-otp'),
    path('verify-otp/', OTPVerifyView.as_view(), name='verify-otp'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
