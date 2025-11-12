from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection


def display_message(request, error):
    match error:
        case 1:
            messages.error(request, 'Invalid username or password. Please try again.')
        case 2:
            messages.error(request, 'Please enter both username and password.')


def redirect_home(request, user):
    # Log the user in (user is already a User object from authenticate())
    login(request, user)
    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
    return redirect('home')


# Function to extract username and password from POST request
def request_Post(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    return username, password


#Secured function to execute parameterized SQL query
def Secure_query_pass(username, password):
    return None  # Placeholder for secured implementation