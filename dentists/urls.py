from django.urls import path
from . import views

app_name = 'dentists'

urlpatterns = [
    path('', views.dentist_list, name='list'),
    path('<int:dentist_id>/', views.dentist_detail, name='detail'),
]
