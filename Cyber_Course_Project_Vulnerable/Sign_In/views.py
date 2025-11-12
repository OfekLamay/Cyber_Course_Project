from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from . import utils


def Sign_In_view(request):
    if request.method == "POST":
        #Accepting username and password from POST request
        username , password =  utils.request_Post(request)
        if username and password:
            # Vulnerable SQL query - directly inserting user input
            result = utils.Vulnerable_query_pass(username, password)
            if result:
                # Redirect to home with login
                return utils.redirect_login(request, result)
            else:
                # Display invalid credentials message
                utils.display_message(request, error=1)
        else:
            # Display missing fields message
            utils.display_message(request, error=2)
    # render the sign-in page
    return render(request, 'Sign_In.html')


