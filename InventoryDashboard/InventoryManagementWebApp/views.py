from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    return login_view(request)


from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def has_valid_session(request):
    """ Helper to check if the request has a valid session """
    return request.user.is_authenticated and request.session.session_key

def login_view(request):
    """Associate login view.

    - If user already has a valid session, redirect to select_operations
    - GET: show a simple login form
    - POST: authenticate credentials; on success redirect to select_operations
      on failure, re-render login with an error message
    """
    # Check if user already has a valid session
    if has_valid_session(request):
        # User already logged in; redirect to select_operations
        return redirect('select_operations')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Ensure session is persisted after login
            request.session.save()
            # Get the Associate object and mark as authenticated
            associate = getattr(user, 'associate', None)
            if associate:
                associate.authenticate(password)
                associate.save()
            else:
                # Not a regular associate; redirect to admin site
                return redirect('/admin/')
            # Successful login -> take the user to SelectOperations screen
            return redirect('select_operations')
        else:
            # Invalid credentials -> stay on login screen with error
            messages.error(request, 'Invalid username or password')
            return render(request, 'InventoryManagementWebApp/login.html', status=200)

    return render(request, 'InventoryManagementWebApp/login.html')

def logout_view(request):
    """Associate logout view.

    Logs out the user and redirects to the login page.
    """
    # Check if user already has a valid session
    if has_valid_session(request):
        # User already logged in; log them out
        logout(request)
        # Invalidate the session
        request.session.flush()
        # Unauthenitcate the Associate object
        associate = getattr(request.user, 'associate', None)
        if associate:
            associate.is_authenticated = False
            associate.save()
    return redirect('login')

@login_required
def select_operations(request):
    """Simple landing page after successful associate login.
    
    Verifies the user has an active session before returning the page.
    Redirects to login_view if no valid session exists.
    """
    return render(request, 'InventoryManagementWebApp/select_operations.html')

@login_required
def create_new_inventory_product(request):
    """Create a new inventory product.
    If the method is a post request, process the form data to create the product."""
    if request.method == 'POST':
        # Process form data here to create a new inventory product
        pass
    return render(request, "InventoryManagementWebApp/create_new_inventory_product.html")

@login_required
def read_inventory_products(request):
    """Read existing inventory products."""
    return render(request, "InventoryManagementWebApp/read_inventory_products.html")

@login_required
def update_inventory_product_location(request):
    """Update location for an existing inventory product."""
    return render(request, "InventoryManagementWebApp/update_inventory_product_location.html")

@login_required
def update_inventory_product_quantity_on_pallet(request):
    """Update quantity on pallet for an existing inventory product."""
    return render(request, "InventoryManagementWebApp/update_inventory_product_quantity_on_pallet.html")

@login_required
def delete_inventory_product(request):
    """Delete an inventory product."""
    return render(request, "InventoryManagementWebApp/delete_inventory_product.html")
