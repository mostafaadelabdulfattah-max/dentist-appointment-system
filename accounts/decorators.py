from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def patient_required(view_func):
    """
    Only allows users who have a Patient profile to access a view.
    Keeps dentist/admin accounts out of patient-only pages like booking
    an appointment or using the AI assistant.

    Lives here (not in appointments/views.py) so any app can reuse it
    without importing from another app's views module.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'patient_profile'):
            messages.error(request, "Only patient accounts can access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def dentist_required(view_func):
    """
    Only allows users who have a Dentist profile to access a view.
    Used for the dentist's own appointment dashboard.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'dentist_profile'):
            messages.error(request, "Only dentist accounts can access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
