from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    """
    Extra profile information for a patient.

    We DON'T create a custom User model from scratch — we reuse Django's
    built-in User (which already handles password hashing, login, etc.)
    and attach a Patient record to it with a OneToOneField. This is the
    standard, beginner-friendly way to add role-specific fields in Django.

    Administrators don't get their own model here: an admin is just a
    Django User with is_staff=True (Django's built-in admin site already
    understands this).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
