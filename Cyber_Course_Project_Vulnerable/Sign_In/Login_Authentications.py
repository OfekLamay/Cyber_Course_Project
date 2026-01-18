from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db import connection
from django.contrib.auth.models import User

class User_Session_Manager:

    @staticmethod
    def _create_welcome_message(user_obj):
        return f'Welcome back, {user_obj.get_full_name()}!'
    
    @staticmethod
    def redirect_login(request, user,success_url):
        login(request, user)
        welcome_message = User_Session_Manager._create_welcome_message(user)
        messages.success(request, welcome_message)
        return redirect(success_url)
    
    @staticmethod
    def display_message(request, error):
        match error:
         case 1:
            messages.error(request, 'Invalid username or password. Please try again.')
         case 2:
            messages.error(request, 'Please enter both username and password.')


    @staticmethod
    def request_Post(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        return username, password


    @staticmethod
    def Vulnerable_query_user(username):
        query = f"""
            SELECT id FROM auth_user
            WHERE username = '{username}'
            LIMIT 1
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

        if not row:
            return None

        return User.objects.get(id=row[0])
    
    @staticmethod
    def Vulnerable_Sign_In_query(username, password):
        query = f"""
            SELECT id FROM auth_user
            WHERE username = '{username}' AND password = '{password}'
            LIMIT 1
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

        if not row:
            return None

        return User.objects.get(id=row[0])

        