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
            (username ,password, first_name, last_name, last_login, is_superuser, email, is_staff, is_active, date_joined)
            VALUES('{username}','{hashed_password}', '{first_name}', '{last_name}', NULL, 0, '{email}', 0, 1, '{date_joined}')
            """


        try:
            with connection.cursor() as cursor:
                cursor.execute(query)

            messages.success(request, f"User created , Welcome {username}")
            return redirect('Sign_In')

        except Exception as e:
            messages.error(request, f"Database error: {e}")

    else:
        form = CustomUserCreationForm()

    return render(request, 'Sign_Up.html', {'form': form})


# An example for what to enter at the username field in order to create a superuser 
# Fill all fields respectfully
# In Last Name Field Enter: hi', NULL, '1', 'hack@boss.com', 1, 1, '2025-01-01') --
# That way u can bypass The mail integrity and create a super user
# Can go to http://127.0.0.1:8000/admin/ and see the new superuser - can see all users! 
# Using ' in the username to break the query and inject SQL
# # Using -- to comment out the rest of the query 
# One way to understand that this is a Django app is to check the cookies in the browser. 
# Look for csrftoken. By providing the ' in the username, the query breaks 
# and the near "2026": syntax error shows that it is using SQLite (Django's default DB) 
# Now we can now for sure that this is a Django app, probably using SQLite and with 
# the default auth_user table for user management. We can also now know from Django's docs 
# that the auth_user table has the following fields: # id, password, last_login, is_superuser, username, is_staff, is_active
# Now we can try to craft the full SQL injection to create a superuser 
# One way is to test the table structure by providing a different number of values in 
# different attempts and see the errors, for example in Last NaME FIELD: 
# hi,hi', NULL, '1', 'hack@boss.com', 1, 1, '2025-01-01') --
# This is a brute force way to find the correct structure of the table
