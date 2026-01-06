from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from Cyber_Course_Project.hashers import HMACPasswordHasher


class User_Session_Manager:
    """
    This class manages user sessions and related messages.
    TODO: Expand with more session management features as needed. 
    Such as session timeout, redirection, welcome messages, session tracking, etc.
    """
    @staticmethod
    def _create_welcome_message(user_obj):
        return f'Welcome back, {user_obj.get_full_name()}!'
    
    @staticmethod
    def redirect_login(request, user,success_url):
        login(request, user)
        welcome_message = User_Session_Manager._create_welcome_message(user)
        messages.success(request, welcome_message)
        return redirect(success_url)