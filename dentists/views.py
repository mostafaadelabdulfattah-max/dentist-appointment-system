from django.shortcuts import render, get_object_or_404
from .models import Dentist


def dentist_list(request):
    """
    Patient-facing page: browse all dentists.

    select_related pulls the linked User and Specialty in the SAME
    database query instead of one extra query per dentist — a small
    but standard Django performance habit worth knowing early.
    """
    dentists = Dentist.objects.select_related('user', 'specialty').all()
    return render(request, 'dentists/dentist_list.html', {'dentists': dentists})


def dentist_detail(request, dentist_id):
    """
    Patient-facing page: one dentist's info, specialty, and weekly schedule.

    get_object_or_404 automatically shows a clean "not found" page instead
    of crashing if someone visits a URL with an invalid dentist_id.
    """
    dentist = get_object_or_404(
        Dentist.objects.select_related('user', 'specialty').prefetch_related('schedules'),
        id=dentist_id,
    )
    return render(request, 'dentists/dentist_detail.html', {'dentist': dentist})
