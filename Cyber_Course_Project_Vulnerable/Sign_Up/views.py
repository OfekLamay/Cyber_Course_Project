from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from .forms import CustomUserCreationForm
import datetime

def Sign_Up_view(request):
    if request.method == "POST":
        # Create the form (so it can be displayed again if it fails)
        form = CustomUserCreationForm(request.POST)
        
        # Extract raw and dangerous data (Bypassing Form Validation)
        raw_username = request.POST.get('username')
        raw_password = request.POST.get('password1')
        
        # Data to complete
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        date_joined = datetime.datetime.now()
        hashed_password = make_password(raw_password)

        # An example for what to enter at the username field in order to create a superuser
        # king', 1, 'Admin', 'Hacker', 'hack@boss.com', 1, 1, '2025-01-01') -- 
        # Can go to http://127.0.0.1:8000/admin/ and see the new superuser - can see all users!
        # Using ' in the username to break the query and inject SQL
        # Using ' 1=1 -- to comment out the rest of the query
        # One way to understand that this is a Django app is to check the cookies in the browser.
        # Look for csrftoken. By providing the ' in the username, the query breaks 
        # and the near "2026": syntax error shows that it is using SQLite (Django's default DB)
        # Now we can now for sure that this is a Django app, probably using SQLite and with
        # the default auth_user table for user management. We can also now know from Django's docs
        # that the auth_user table has the following fields:
        # id, password, last_login, is_superuser, username, is_staff, is_active
        # Now we can try to craft the full SQL injection to create a superuser
        # One way is to test the table structure by providing a different number of values in 
        # different attempts and see the errors, for example: 
        # king2','Admin', 'Hacker', 'mail@mail.com', 1, 1, 1, '2025-01-01') --
        # This is a brute force way to find the correct structure of the table

        if raw_username:
            try:                
                query = f"""
                    INSERT INTO auth_user 
                    (password, last_login, username, is_superuser, first_name, last_name, email, is_staff, is_active, date_joined)
                    VALUES 
                    ('{hashed_password}', NULL, '{raw_username}', 0, '{first_name}', '{last_name}', '{email}', 0, 1, '{date_joined}')
                """
                
                print(f"Executing Vulnerable SQL: {query}") # Look at the error in the console logs

                with connection.cursor() as cursor:
                    cursor.execute(query)
                
                messages.success(request, f"HACKED: User {raw_username} created directly via SQL Injection!")
                return redirect('Sign_In')

            except Exception as e:
                # If there is an SQL error (like in a DoS attack), print it
                error_msg = str(e)
                print(f"SQL Error: {error_msg}")
                
                # Option A: Show the user that the system "broke" (technical error message)
                messages.error(request, f"Database Error (SQL Injection Failed?): {error_msg}")
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'Sign_Up.html', {'form': form})