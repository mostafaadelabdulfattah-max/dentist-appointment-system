from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PatientRegistrationForm, PatientProfileForm


def register(request):
    """
    Handles the patient registration page.

    GET  -> show a blank form
    POST -> validate it; if valid, create the User + Patient (see
            PatientRegistrationForm.save()), log them in immediately,
            and send them to their dashboard.
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('appointments:patient_dashboard')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def post_login_redirect(request):
    """
    Sends a freshly logged-in user to the right landing page based on
    their role — this is what settings.LOGIN_REDIRECT_URL points to,
    so it fires after every login regardless of which page asked for
    the login in the first place (unless a specific 'next' was set).
    """
    user = request.user
    if hasattr(user, 'patient_profile'):
        return redirect('appointments:patient_dashboard')
    if hasattr(user, 'dentist_profile'):
        return redirect('appointments:dentist_dashboard')
    if user.is_staff:
        return redirect('/admin/')
    return redirect('home')


@login_required
def profile(request):
    """
    Shows the logged-in user's profile.
    @login_required means: if they're not logged in, Django sends them
    to the login page automatically (using settings.LOGIN_URL).
    """
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile(request):
    """
    Lets a PATIENT update their own profile (phone/DOB + name/email).
    Dentist/admin profile editing isn't in scope for the SRS — dentist
    info is managed by an Administrator via the Django admin site.
    """
    if not hasattr(request.user, 'patient_profile'):
        messages.error(request, "Only patient accounts can edit a profile here.")
        return redirect('accounts:profile')

    patient = request.user.patient_profile

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            # first_name/last_name/email live on the User model, not
            # Patient, so we update them directly here.
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            request.user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = PatientProfileForm(instance=patient)

    return render(request, 'accounts/edit_profile.html', {'form': form})
