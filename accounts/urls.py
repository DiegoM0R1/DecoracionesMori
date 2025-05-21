from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Nuevas rutas para verificación de email
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify-email/<str:email>/<str:token>/', views.verify_email, name='verify_email'),
]