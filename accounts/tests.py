from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Patient


class RegistrationTests(TestCase):
    def test_patient_can_register(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newpatient',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'Patient',
            'phone_number': '0111111111',
            'date_of_birth': '1995-05-05',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newpatient').exists())
        self.assertTrue(Patient.objects.filter(user__username='newpatient').exists())

    def test_registration_fails_with_mismatched_passwords(self):
        self.client.post(reverse('accounts:register'), {
            'username': 'baduser',
            'email': 'bad@example.com',
            'password1': 'StrongPass123!',
            'password2': 'CompletelyDifferent456!',
        })
        self.assertFalse(User.objects.filter(username='baduser').exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='existing', password='testpass123')
        Patient.objects.create(user=self.user)

    def test_login_with_correct_credentials_succeeds(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'existing',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'existing',
            'password': 'wrongpassword',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UnauthorizedAccessTests(TestCase):
    def test_anonymous_user_is_redirected_from_profile(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
