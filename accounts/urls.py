from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# This app_name lets us refer to these URLs elsewhere as
# 'accounts:register', 'accounts:login', etc. instead of hard-coding paths.
app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('post-login/', views.post_login_redirect, name='post_login_redirect'),

    # We use Django's BUILT-IN login/logout views instead of writing our
    # own — they already handle password checking, sessions, and CSRF
    # protection correctly. We only supply our own template.
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
