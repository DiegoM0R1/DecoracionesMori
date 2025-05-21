
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),  # Añade esta línea
        path('verify/', views.verify_account_view, name='verify'),
    path('resend-code/', views.resend_verification_code, name='resend_code'),
]