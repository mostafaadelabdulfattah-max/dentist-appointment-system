from django.db import models
from django.contrib.auth.models import User


class Specialty(models.Model):
    """
    A dental specialty, e.g. "General Dentistry", "Orthodontics".

    This is its own table (instead of a plain text field on Dentist) so
    that the AI assistant and the dentist-browsing pages can filter and
    match against a fixed, reliable list of specialties.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Specialties'

    def __str__(self):
        return self.name


class Dentist(models.Model):
    """
    Extra profile information for a dentist, linked 1:1 to a Django User
    (same pattern as Patient — reuse Django's auth system for login).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dentist_profile',
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,  # don't allow deleting a specialty that's in use
        related_name='dentists',
    )
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"Dr. {full_name}"


class DentistSchedule(models.Model):
    """
    One row = one working block for a dentist on one day of the week.

    Example: Dr. Ahmed works Mondays 09:00-17:00 in 30-minute slots.
    This is separate from the Dentist model because a dentist can have
    different hours on different days (one dentist, many schedule rows).

    The appointments app reads these rows to figure out which time slots
    exist at all, before checking which of them are already booked.
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    dentist = models.ForeignKey(
        Dentist,
        on_delete=models.CASCADE,
        related_name='schedules',
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text='Length of each bookable appointment slot, in minutes.',
    )

    class Meta:
        # A dentist can only have ONE schedule row per day of the week.
        unique_together = ('dentist', 'day_of_week')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.dentist} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"
