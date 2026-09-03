from django.db import models
from accounts.models import Patient
from dentists.models import Dentist


class Appointment(models.Model):
    """
    A single booked appointment between a Patient and a Dentist.

    This is the table the whole availability system revolves around:
    to know which slots are "free" on a given day, we generate all
    possible slots from DentistSchedule and then subtract whatever
    already has a non-cancelled Appointment row here.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    dentist = models.ForeignKey(
        Dentist,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']
        constraints = [
            # DATABASE-LEVEL double-booking prevention.
            # Even if two requests hit the server at the exact same time,
            # PostgreSQL itself will reject the second INSERT for the same
            # dentist/date/start_time — this is the final safety net,
            # in addition to the check we'll do in appointments/services.py.
            #
            # Cancelled appointments don't count, so a cancelled slot can
            # be re-booked.
            models.UniqueConstraint(
                fields=['dentist', 'date', 'start_time'],
                condition=~models.Q(status='cancelled'),
                name='unique_active_slot_per_dentist',
            )
        ]

    def __str__(self):
        return f"{self.patient} with {self.dentist} on {self.date} at {self.start_time} ({self.status})"
