from rest_framework.test import APITestCase
from django.urls import reverse
from .models import User, PhoneVerification

class AuthTests(APITestCase):
    def test_register_and_verify(self):
        url = reverse('auth_register')
        data = {
            'phone_number': '+989024815665',
            'password': '@Fazeli34',
            'password2': '@Fazeli34'
        }
        r = self.client.post(url, data, format='json')
        self.assertEqual(r.status_code, 201)
        user = User.objects.get(phone_number='+989024815665')
        self.assertFalse(user.is_active)
        self.assertTrue(PhoneVerification.objects.filter(user=user).exists())

    def test_password_reset_flow(self):
        user = User.objects.create_user(phone_number='+989024815665', password='@Fazeli34')
        user.is_active = True
        user.save()
        url = reverse('password_reset_request')
        r = self.client.post('/api/auth/password-reset/', {'phone_number': '+989024815665'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(PhoneVerification.objects.filter(user=user).exists())
