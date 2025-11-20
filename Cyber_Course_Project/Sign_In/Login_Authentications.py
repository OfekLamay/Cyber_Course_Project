from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from Cyber_Course_Project.hashers import HMACPasswordHasher

class Authentication:
    """
    This class handles Custom authentication using HMAC with Salt 
    And SQL queries, and brute force protection. 
    #TODO: implement query parameterization to prevent SQL injection
    #TODO: implement account lockout mechanism for brute force protection
    #TODO: implement input sanitization to prevent XSS attacks
    """
    @staticmethod
    def display_message(request, error):
        match error:
            case 1:
                messages.error(request, 'Invalid username or password. Please try again.')
            case 2:
                messages.error(request, 'Please enter both username and password.')
            case 3:
                messages.error(request, 'Account locked due to multiple failed login attempts. Please try again later')
        
    
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