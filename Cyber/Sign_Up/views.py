from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm

def Sign_Up_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the new user
            user = form.save()
            
            # Auto-login the user after successful registration
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"🎉 Welcome {user.first_name}! Your account has been created successfully and you're now logged in!")
                # Redirect directly to home page instead of login
                return redirect('home')
            else:
                messages.success(request, f"Account created successfully for {user.username}! Please log in.")
                return redirect('Sign_In')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'Sign_Up.html', {'form': form})