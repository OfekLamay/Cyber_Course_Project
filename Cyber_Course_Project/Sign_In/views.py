from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection

# Create your views here.
def Sign_In_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    return render(request, 'Sign_In.html')