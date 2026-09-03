from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Patient


class PatientRegistrationForm(UserCreationForm):
    """
    Public registration form — for PATIENTS only.

    Dentist accounts are created by an Administrator (through the Django
    admin site), not through public self-registration — the SRS doesn't
    ask for dentists to sign themselves up, and it keeps us from having
    to verify who's "really" a dentist.
    """
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def save(self, commit=True):
        # First create the User (handles password hashing via UserCreationForm)
        user = super().save(commit=commit)
        if commit:
            # Then attach the Patient profile with the extra fields
            Patient.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
            )
        return user


class PatientProfileForm(forms.ModelForm):
    """
    Lets a logged-in patient update their own extra profile fields.
    Their name/email (stored on the User model, not Patient) are
    handled directly in the view alongside this form.
    """
    class Meta:
        model = Patient
        fields = ['phone_number', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
