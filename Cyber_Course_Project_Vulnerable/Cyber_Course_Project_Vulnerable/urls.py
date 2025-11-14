from django.contrib import admin
from django.urls import path, include
from . views import home, customer_system, add_customer, customer_detail, edit_customer, delete_customer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home,name='home'),
    path('home/',home,name='home'),
    path('Sign_Up/', include('Sign_Up.urls')),
    path('Sign_In/', include('Sign_In.urls')),
    path('Sign_Out/', include('Sign_Out.urls')),
    
    # Customer Management URLs
    path('customers/', customer_system, name='customer_system'),
    path('customers/add/', add_customer, name='add_customer'),
    path('customers/<int:customer_id>/', customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', edit_customer, name='edit_customer'),
    path('customers/<int:customer_id>/delete/', delete_customer, name='delete_customer'),
]
