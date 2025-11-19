from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from Cyber_Course_Project.hashers import HMACPasswordHasher

class AuthenticationUtils:
    """
    Utility class for authentication-related operations
    Methods:
    - display_message: Display error messages to user
    - redirect_login: Handle user login and redirect
    - request_Post: Extract username and password from POST request
    - custom_authenticate: Custom authentication using HMAC+Salt hasher
    - get_user_object: Get User object from user data
    - _create_welcome_message: Create personalized welcome message
    - Private methods are prefixed with an underscore
    - Backward compatibility wrapper functions provided at module level
    """

    @staticmethod
    def display_message(request, error):
        match error:
            case 1:
                messages.error(request, 'Invalid username or password. Please try again.')
            case 2:
                messages.error(request, 'Please enter both username and password.')
    
    @staticmethod
    def get_user_object(user):
        return User.objects.get(id=user.id)
    
    @staticmethod
    def redirect_login(request, user):
        user_obj = AuthenticationUtils.get_user_object(user)
        login(request, user_obj)
        
        welcome_message = AuthenticationUtils._create_welcome_message(user_obj)
        messages.success(request, welcome_message)
        return redirect('home')
    
    @staticmethod
    def request_Post(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        return username, password
    
    
    @staticmethod
    def _create_welcome_message(user_obj):
        return f'Welcome back, {user_obj.get_full_name() or user_obj.username}!'
    
    @staticmethod
    def custom_authenticate(username, password):
        try:
            # Step 1: Find user by username
            user = User.objects.get(username=username)
            # Step 2: Use custom HMAC+Salt hasher directly from imported module hashers.py
            hasher = HMACPasswordHasher()
            # Step 3: Verify password using your custom hasher
            if hasher.verify(password, user.password):
                return user
            else:
                return None
        except User.DoesNotExist:
            # User not found
            return None
        except Exception as e:
            # Handle any other errors
            return None
