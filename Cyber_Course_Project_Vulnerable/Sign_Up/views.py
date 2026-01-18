from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from .forms import CustomUserCreationForm
import datetime

def Sign_Up_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if not form.is_valid():
            return render(request, 'Sign_Up.html', {'form': form})

        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']

        hashed_password = make_password(password)
        date_joined = datetime.datetime.now()

        query = f"""
            INSERT INTO auth_user
            (password, last_login, is_superuser, username,
             first_name, last_name, email, is_staff, is_active, date_joined)
            VALUES
            ('{hashed_password}', NULL, 0, '{username}',
             '{first_name}', '{last_name}', '{email}', 0, 1, '{date_joined}')
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query)

            messages.success(request, "User created")
            return redirect('Sign_In')

        except Exception as e:
            messages.error(request, f"Database error: {e}")

    else:
        form = CustomUserCreationForm()

    return render(request, 'Sign_Up.html', {'form': form})
