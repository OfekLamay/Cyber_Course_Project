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


def redirect_login(request, result):
    # Log the user in
    user_obj = User.objects.get(id=result[0][0])  # Assuming user ID is in the first column
    login(request, user_obj)
    messages.success(request, f'Welcome back, {user_obj.get_full_name() or user_obj.username}!')
    return redirect('home')


# Function to extract username and password from POST request
def request_Post(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    return username, password


# Vulnerable function to execute raw SQL query
def Vulnerable_query_pass(username, password):
    query = f"SELECT * FROM auth_user WHERE username = '{username}' AND password = '{password}'"
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()