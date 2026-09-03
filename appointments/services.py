"""
Appointment availability and booking logic.

This is the most important file in the whole project — it's the ONLY
place that decides whether a time slot is available. Both the JSON
endpoint (for the JavaScript on the booking page) and the actual booking
view call these same functions, so the rules can never get out of sync.
"""

from datetime import datetime, timedelta
from django.db import transaction, IntegrityError

from dentists.models import DentistSchedule
from .models import Appointment


def get_available_slots(dentist, selected_date):
    """
    Returns a list of available start times (as `time` objects) for a
    dentist on a given date.

    Steps:
    1. Find the dentist's working hours for that day of the week.
    2. Generate every possible slot between start_time and end_time.
    3. Remove any slot that already has a non-cancelled Appointment.
    """
    day_of_week = selected_date.weekday()  # Monday=0 ... Sunday=6

    try:
        schedule = DentistSchedule.objects.get(dentist=dentist, day_of_week=day_of_week)
    except DentistSchedule.DoesNotExist:
        # The dentist doesn't work on this day at all.
        return []

    # Step 1 & 2: generate all possible slots for this day.
    possible_slots = []
    current = datetime.combine(selected_date, schedule.start_time)
    day_end = datetime.combine(selected_date, schedule.end_time)
    step = timedelta(minutes=schedule.slot_duration_minutes)

    while current + step <= day_end:
        possible_slots.append(current.time())
        current += step

    # Step 3: remove slots that are already booked (ignore cancelled ones).
    booked_times = set(
        Appointment.objects.filter(dentist=dentist, date=selected_date)
        .exclude(status='cancelled')
        .values_list('start_time', flat=True)
    )

    return [slot for slot in possible_slots if slot not in booked_times]


def is_slot_available(dentist, selected_date, start_time):
    """Convenience check: is this exact slot currently free?"""
    return start_time in get_available_slots(dentist, selected_date)


def book_appointment(patient, dentist, selected_date, start_time):
    """
    Attempts to create an Appointment.

    Returns a tuple: (appointment_or_None, error_message_or_None)

    This function re-checks availability itself — it NEVER trusts that
    the slot the browser sent is actually still free. Two safety nets:
      1. is_slot_available() re-runs the same query the booking page used
      2. the database UniqueConstraint on Appointment (from Phase 3) is
         the final backstop in case two bookings land at the exact same
         instant (a "race condition")
    """
    day_of_week = selected_date.weekday()

    try:
        schedule = DentistSchedule.objects.get(dentist=dentist, day_of_week=day_of_week)
    except DentistSchedule.DoesNotExist:
        return None, "This dentist does not work on the selected day."

    if not is_slot_available(dentist, selected_date, start_time):
        return None, "This appointment slot is no longer available."

    end_datetime = datetime.combine(selected_date, start_time) + timedelta(
        minutes=schedule.slot_duration_minutes
    )

    try:
        with transaction.atomic():
            appointment = Appointment.objects.create(
                patient=patient,
                dentist=dentist,
                date=selected_date,
                start_time=start_time,
                end_time=end_datetime.time(),
                status='pending',
            )
        return appointment, None
    except IntegrityError:
        # The database constraint caught a race condition: someone else
        # booked this exact slot a split second before us.
        return None, "This appointment slot is no longer available."
