from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from . import utils

# Create your views here.
def Sign_In_view(request):
    if request.method == "POST":
         #Accepting username and password from POST request
        username , password = utils.request_Post(request)
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                #Redirect to home with login
                return utils.redirect_home(request, user)
            else:
               # Display invalid credentials message
               utils.display_message(request, error=1)
        else:
            # Display missing fields message
            utils.display_message(request, error=2)
    #render the sign-in page
    return render(request, 'Sign_In.html')