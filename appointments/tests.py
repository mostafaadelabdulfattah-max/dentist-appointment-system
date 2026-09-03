from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import Patient
from dentists.models import Specialty, Dentist, DentistSchedule
from .models import Appointment
from . import services


def next_weekday(weekday):
    """Returns the next date (strictly in the future) matching the given weekday (0=Monday)."""
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    days_ahead = days_ahead if days_ahead != 0 else 7
    return today + timedelta(days=days_ahead)


class AvailabilityTests(TestCase):
    def setUp(self):
        specialty = Specialty.objects.create(name='General Dentistry')
        user = User.objects.create_user(username='dr_x')
        self.dentist = Dentist.objects.create(user=user, specialty=specialty)
        self.test_date = next_weekday(0)  # next Monday
        DentistSchedule.objects.create(
            dentist=self.dentist, day_of_week=0,
            start_time='09:00', end_time='10:00', slot_duration_minutes=30,
        )

    def test_available_slot_generation(self):
        slots = services.get_available_slots(self.dentist, self.test_date)
        self.assertEqual([s.strftime('%H:%M') for s in slots], ['09:00', '09:30'])

    def test_day_with_no_schedule_returns_no_slots(self):
        tuesday = self.test_date + timedelta(days=1)
        slots = services.get_available_slots(self.dentist, tuesday)
        self.assertEqual(slots, [])


class BookingTests(TestCase):
    def setUp(self):
        specialty = Specialty.objects.create(name='General Dentistry')
        dentist_user = User.objects.create_user(username='dr_y')
        self.dentist = Dentist.objects.create(user=dentist_user, specialty=specialty)
        DentistSchedule.objects.create(
            dentist=self.dentist, day_of_week=0,
            start_time='09:00', end_time='10:00', slot_duration_minutes=30,
        )
        self.test_date = next_weekday(0)

        self.patient_user = User.objects.create_user(username='p1', password='pass12345')
        self.patient = Patient.objects.create(user=self.patient_user)

        self.patient_user2 = User.objects.create_user(username='p2', password='pass12345')
        self.patient2 = Patient.objects.create(user=self.patient_user2)

    def test_successful_booking_is_stored(self):
        self.client.login(username='p1', password='pass12345')
        response = self.client.post(f'/appointments/book/{self.dentist.id}/', {
            'date': self.test_date.isoformat(), 'time': '09:00',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Appointment.objects.filter(dentist=self.dentist, date=self.test_date, start_time='09:00').exists()
        )

    def test_double_booking_is_prevented(self):
        self.client.login(username='p1', password='pass12345')
        self.client.post(f'/appointments/book/{self.dentist.id}/', {
            'date': self.test_date.isoformat(), 'time': '09:00',
        })

        self.client.logout()
        self.client.login(username='p2', password='pass12345')
        self.client.post(f'/appointments/book/{self.dentist.id}/', {
            'date': self.test_date.isoformat(), 'time': '09:00',
        })

        active_count = Appointment.objects.filter(
            dentist=self.dentist, date=self.test_date, start_time='09:00',
        ).exclude(status='cancelled').count()
        self.assertEqual(active_count, 1)

    def test_booking_outside_working_hours_is_rejected(self):
        self.client.login(username='p1', password='pass12345')
        # Dentist only works 09:00-10:00; 11:00 is outside that window.
        self.client.post(f'/appointments/book/{self.dentist.id}/', {
            'date': self.test_date.isoformat(), 'time': '11:00',
        })
        self.assertFalse(Appointment.objects.filter(dentist=self.dentist, start_time='11:00').exists())

    def test_cancellation_frees_the_slot(self):
        self.client.login(username='p1', password='pass12345')
        self.client.post(f'/appointments/book/{self.dentist.id}/', {
            'date': self.test_date.isoformat(), 'time': '09:00',
        })
        appointment = Appointment.objects.get(dentist=self.dentist, date=self.test_date, start_time='09:00')

        self.client.post(f'/appointments/{appointment.id}/cancel/')
        appointment.refresh_from_db()

        self.assertEqual(appointment.status, 'cancelled')
        remaining_slots = services.get_available_slots(self.dentist, self.test_date)
        self.assertIn(appointment.start_time, remaining_slots)

    def test_dentist_account_cannot_access_booking_page(self):
        self.dentist.user.set_password('pass12345')
        self.dentist.user.save()
        self.client.login(username='dr_y', password='pass12345')
        response = self.client.get(f'/appointments/book/{self.dentist.id}/')
        self.assertEqual(response.status_code, 302)
