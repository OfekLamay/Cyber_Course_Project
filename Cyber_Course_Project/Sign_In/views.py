from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from django.views import View
from django.views.generic import FormView
from django import forms
from django.contrib.auth.hashers import check_password
from . import utils

#ADI#
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

class SignInForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# Create your views here.
class SignInView(FormView):
    """
    Class-based view for Sign-In functionality
    Methods:
    - form_valid: Handle valid form submission filtering input
    - _authenticate_user: Private method for user authentication
    - _handle_successful_login: Private method for successful login handling
    - _handle_failed_login: Private method for failed login handling
    - private methods are prefixed with an underscore _
    """ 
    
    template_name = 'Sign_In.html'
    form_class = SignInForm
    success_url = '/home/'
    
    def _authenticate_user(self, username, password):
        return utils.AuthenticationUtils.custom_authenticate(username, password)
        
    def _handle_successful_login(self, user):
        return utils.AuthenticationUtils.redirect_login(self.request, user)
    
    def _handle_failed_login(self):
        utils.AuthenticationUtils.display_message(self.request, error=1)
 
    
    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = self._authenticate_user(username, password)
        if user:
            return self._handle_successful_login(user)
        else:
            self._handle_failed_login()
            return super().form_invalid(form)
    
   

# Keep the old function-based view as an alias for backward compatibility
"""def Sign_In_view(request):
    #Function-based view wrapper for backward compatibility
    view = SignInView()
    if request.method == 'GET':
        return view.get(request)
    elif request.method == 'POST':
        return view.post(request)
    else:
        return view.get(request)
 """

def forgot_password(request):
    # Placeholder page (client-side only for now)
    return render(request, 'forgot_password.html')

#ADI#
@login_required
def change_password(request):
    """
    Handles the Change Password screen.

    GET  -> render the change_password.html form
    POST -> validate current password and update to a new one
    """

    # If the user submitted the form (POST request)
    if request.method == "POST":
        # Read form fields from the POST data
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        #  Basic validation: all fields must be filled
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, "change_password.html")

        #  New password and confirmation must match
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return render(request, "change_password.html")

        #  Check that the current password is correct for the logged-in user
        user = request.user
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, "change_password.html")


        # Update the password securely using Django's built-in method
        user.set_password(new_password)
        user.save()

        #  Keep the user logged in after the password change
        update_session_auth_hash(request, user)

        #  Show success message to the user
        messages.success(request, "Password changed successfully.")
        return render(request, "change_password.html")

    # If this is a GET request, simply render the form
    return render(request, "change_password.html")
