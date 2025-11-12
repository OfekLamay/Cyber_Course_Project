from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection


# Vulnerable SQL Injection login view || Use This in the vulnerable version of the project only || Delete in Secure version!!
def Sign_In_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password') 
        if username and password:
            # Vulnerable SQL query - directly inserting user input
            query = f"SELECT * FROM auth_user WHERE username = '{username}' AND password = '{password}'"
            
            # Opens DB connection and executes raw SQL query
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()

                if result:
                    # Get the user ID from the SQL result and actually log them in
                    user_id = result[0]  # First column is usually the ID
                    user = User.objects.get(id=user_id)
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid username or password. Please try again.')
        else:
            messages.error(request, 'Please enter both username and password.')
    #Change render to Sign_In.html in the vulnerable version of the project
    return render(request, 'Sign_In.html')