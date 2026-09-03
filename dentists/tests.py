from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Specialty, Dentist, DentistSchedule


class DentistModelTests(TestCase):
    def test_dentist_creation_and_string_representation(self):
        specialty = Specialty.objects.create(name='General Dentistry')
        user = User.objects.create_user(username='dr_test', first_name='Test', last_name='Dentist')
        dentist = Dentist.objects.create(user=user, specialty=specialty)

        self.assertEqual(str(dentist), 'Dr. Test Dentist')
        self.assertEqual(dentist.specialty, specialty)


class DentistListingTests(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name='Orthodontics')
        self.user = User.objects.create_user(username='dr_ortho', first_name='Sara', last_name='Ali')
        self.dentist = Dentist.objects.create(user=self.user, specialty=self.specialty)

    def test_dentist_list_page_shows_dentist(self):
        response = self.client.get(reverse('dentists:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Sara Ali')
        self.assertContains(response, 'Orthodontics')

    def test_dentist_detail_page_shows_schedule(self):
        DentistSchedule.objects.create(
            dentist=self.dentist, day_of_week=1, start_time='10:00', end_time='14:00'
        )
        response = self.client.get(reverse('dentists:detail', args=[self.dentist.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tuesday')

    def test_invalid_dentist_id_returns_clean_404(self):
        response = self.client.get(reverse('dentists:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)
