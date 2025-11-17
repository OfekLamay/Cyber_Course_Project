from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from . import utils

#ADI#
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

# Create your views here.
def Sign_In_view(request):
    if request.method == "POST":
        #Accepting username and password from POST request
        username, password = utils.request_Post(request)
        if username and password:
            # Vulnerable SQL query - directly inserting user input
            user = authenticate(request, username=username, password=password)
            if user:
                # Redirect to home with login
                return utils.redirect_login(request, user)
            else:
                utils.display_message(request, error=1)
        else:
            utils.display_message(request, error=2)

    return render(request, 'Sign_In.html')
 

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
