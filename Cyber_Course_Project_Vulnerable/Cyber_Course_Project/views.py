from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Customer
from .forms import CustomerForm

def home(request):
    """Home page view"""
    return render(request, 'home.html')

@login_required
def customer_system(request):
    """Main customer management system page - VULNERABLE TO SQLi"""
    # Get search query
    search_query = request.GET.get('search', '')
    
    # VULNERABLE: Raw SQL with string concatenation
    user_id = request.user.id
    if search_query:
        sql = f"SELECT * FROM Cyber_Course_Project_customer WHERE first_name  = '{search_query}' OR last_name = '{search_query}' OR email = '{search_query}' OR company_name = '{search_query}' OR phone_number = '{search_query}'"
    else:
        sql = f"SELECT * FROM Cyber_Course_Project_customer WHERE created_by_id = '{user_id}'"
    
    customers = list(Customer.objects.raw(sql))
    
    # Pagination (convert to list for paginator)
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'total_customers': len(customers),
    }

    return render(request, 'customer_system.html', context)

@login_required
def add_customer(request):
    """Add new customer view"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(user=request.user)
            messages.success(
                request, 
                f'🎉 Customer "{customer.full_name}" has been added successfully!'
            )
            return redirect('customer_detail', customer_id=customer.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'Add New Customer',
        'button_text': 'Add Customer'
    }
    
    return render(request, 'customer_form.html', context)

@login_required
def customer_detail(request, customer_id):
    """Customer detail view"""
    customer = get_object_or_404(Customer, id=customer_id, created_by=request.user)
    
    context = {
        'customer': customer,
    }
    
    return render(request, 'customer_detail.html', context)

@login_required
def edit_customer(request, customer_id):
    """Edit customer view"""
    customer = get_object_or_404(Customer, id=customer_id, created_by=request.user)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(
                request, 
                f'✅ Customer "{customer.full_name}" has been updated successfully!'
            )
            return redirect('customer_detail', customer_id=customer.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Edit Customer: {customer.full_name}',
        'button_text': 'Update Customer'
    }
    
    return render(request, 'customer_form.html', context)

@login_required
def delete_customer(request, customer_id):
    """Delete customer view"""
    customer = get_object_or_404(Customer, id=customer_id, created_by=request.user)
    
    if request.method == 'POST':
        customer_name = customer.full_name
        customer.delete()
        messages.success(request, f'🗑️ Customer "{customer_name}" has been deleted.')
        return redirect('customer_system')
    
    context = {
        'customer': customer,
    }
    
    return render(request, 'customer_confirm_delete.html', context)