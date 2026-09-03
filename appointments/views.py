from datetime import date, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q

from accounts.decorators import patient_required, dentist_required
from dentists.models import Dentist
from .models import Appointment
from . import services


@patient_required
def patient_dashboard(request):
    """
    The patient's landing page after login — a quick-glance summary,
    distinct from the full appointment list (my_appointments) and from
    Profile. Shows the next upcoming appointment and quick links to the
    main patient actions.
    """
    patient = request.user.patient_profile
    upcoming_appointments = Appointment.objects.filter(
        patient=patient, date__gte=date.today(),
    ).exclude(status='cancelled').select_related(
        'dentist__user', 'dentist__specialty'
    ).order_by('date', 'start_time')

    return render(request, 'appointments/patient_dashboard.html', {
        'next_appointment': upcoming_appointments.first(),
        'upcoming_count': upcoming_appointments.count(),
    })


@login_required
@require_GET
def available_slots_api(request):
    """
    JSON endpoint used by the booking page's JavaScript.

    GET /appointments/available-slots/?dentist_id=1&date=2026-09-10

    NOTE: this endpoint only affects what the browser SHOWS the patient.
    It is not the security boundary — book_appointment() in services.py
    re-checks everything independently when the actual booking happens.
    """
    dentist_id = request.GET.get('dentist_id')
    date_str = request.GET.get('date')

    dentist = get_object_or_404(Dentist, id=dentist_id)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Please select a valid appointment date.'}, status=400)

    if selected_date < date.today():
        return JsonResponse({'slots': []})

    slots = services.get_available_slots(dentist, selected_date)
    return JsonResponse({'slots': [slot.strftime('%H:%M') for slot in slots]})


@patient_required
def book_appointment(request, dentist_id):
    """
    The booking page. GET shows the form; POST attempts the actual booking.
    """
    dentist = get_object_or_404(Dentist, id=dentist_id)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_time = datetime.strptime(time_str, '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Please select a valid appointment date and time.")
            return redirect('appointments:book', dentist_id=dentist.id)

        if selected_date < date.today():
            messages.error(request, "Please select a valid appointment date.")
            return redirect('appointments:book', dentist_id=dentist.id)

        appointment, error = services.book_appointment(
            patient=request.user.patient_profile,
            dentist=dentist,
            selected_date=selected_date,
            start_time=selected_time,
        )

        if error:
            messages.error(request, error)
            return redirect('appointments:book', dentist_id=dentist.id)

        messages.success(request, "Your appointment has been booked!")
        return redirect('appointments:my_appointments')

    return render(request, 'appointments/book.html', {
        'dentist': dentist,
        'today': date.today().isoformat(),
    })


@patient_required
def my_appointments(request):
    """Upcoming appointments: today or later, and not cancelled."""
    appointments = Appointment.objects.filter(
        patient=request.user.patient_profile,
        date__gte=date.today(),
    ).exclude(status='cancelled').select_related('dentist__user', 'dentist__specialty')

    return render(request, 'appointments/my_appointments.html', {'appointments': appointments})


@patient_required
def appointment_history(request):
    """Past appointments, or any appointment that was cancelled."""
    appointments = Appointment.objects.filter(
        patient=request.user.patient_profile,
    ).filter(
        Q(date__lt=date.today()) | Q(status='cancelled')
    ).select_related('dentist__user', 'dentist__specialty')

    return render(request, 'appointments/appointment_history.html', {'appointments': appointments})


@patient_required
def cancel_appointment(request, appointment_id):
    """
    Cancels an appointment. Only works via POST (the template uses a
    small form + JS confirm dialog, not a plain link) so a cancellation
    can't happen from just visiting a URL.

    get_object_or_404 with patient=... makes sure a patient can only
    cancel THEIR OWN appointments, not anyone else's.
    """
    appointment = get_object_or_404(
        Appointment, id=appointment_id, patient=request.user.patient_profile
    )

    if request.method != 'POST':
        return redirect('appointments:my_appointments')

    if appointment.status == 'cancelled':
        messages.info(request, "This appointment was already cancelled.")
    else:
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, "Your appointment has been cancelled.")

    return redirect('appointments:my_appointments')


@dentist_required
def dentist_dashboard(request):
    """
    Lets a dentist see their own appointments (SRS FR-5: "Dentist can
    view appointments"). Cancelled ones are excluded to keep the
    working list focused — they're still visible via the admin site.
    """
    appointments = Appointment.objects.filter(
        dentist=request.user.dentist_profile,
    ).exclude(status='cancelled').select_related('patient__user')

    return render(request, 'appointments/dentist_dashboard.html', {'appointments': appointments})


@dentist_required
def update_appointment_status(request, appointment_id):
    """
    Lets a dentist confirm/update the status of one of THEIR OWN
    appointments (SRS FR-5: "Dentist can confirm/update appointment
    status"). The dentist=... filter below prevents a dentist from
    touching another dentist's appointment, same pattern as patients
    cancelling their own appointments.
    """
    appointment = get_object_or_404(
        Appointment, id=appointment_id, dentist=request.user.dentist_profile
    )

    if request.method != 'POST':
        return redirect('appointments:dentist_dashboard')

    new_status = request.POST.get('status')
    valid_statuses = dict(Appointment.STATUS_CHOICES)

    if new_status not in valid_statuses:
        messages.error(request, "Please select a valid appointment status.")
    else:
        appointment.status = new_status
        appointment.save()
        messages.success(request, f"Appointment status updated to {valid_statuses[new_status]}.")

    return redirect('appointments:dentist_dashboard')
