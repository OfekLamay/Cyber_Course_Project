from django.contrib import admin
from django.urls import path, include
from . views import home


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home,name='home'),
    path('home/',home,name='home'),
    path('Sign_Up/', include('Sign_Up.urls')),
    path('Sign_In/', include('Sign_In.urls')),
    path('Sign_Out/', include('Sign_Out.urls')),
]
