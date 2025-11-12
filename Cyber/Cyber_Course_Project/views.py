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
    """Main customer management system page"""
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all customers for the current user
    customers = Customer.objects.filter(created_by=request.user)
    
    # Apply search filter
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(customers, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'total_customers': customers.count(),
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