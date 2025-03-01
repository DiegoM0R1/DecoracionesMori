# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import User

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = UserLoginForm
    redirect_authenticated_user = True

class UserRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Create but don't login automatically
        user = form.save(commit=False)
        user.is_active = True  # User is active but not verified
        user.save()
        
        # Here you would typically send a verification email or SMS
        
        return super().form_valid(form)