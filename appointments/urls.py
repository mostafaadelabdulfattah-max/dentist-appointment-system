from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('book/<int:dentist_id>/', views.book_appointment, name='book'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('history/', views.appointment_history, name='history'),
    path('<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel'),
    path('available-slots/', views.available_slots_api, name='available_slots_api'),
    path('dentist/dashboard/', views.dentist_dashboard, name='dentist_dashboard'),
    path('dentist/<int:appointment_id>/update-status/', views.update_appointment_status, name='update_status'),
]
