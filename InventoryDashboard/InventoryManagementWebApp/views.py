from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    return login_view(request)


from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    """Associate login view.

    - GET: show a simple login form
    - POST: authenticate credentials; on success redirect to select_operations
      on failure, re-render login with an error message
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Successful login -> take the user to SelectOperations screen
            return redirect('select_operations')
        else:
            # Invalid credentials -> stay on login screen with error
            messages.error(request, 'Invalid username or password')
            return render(request, 'InventoryManagementWebApp/login.html', status=200)

    return render(request, 'InventoryManagementWebApp/login.html')


@login_required
def select_operations(request):
    """Simple landing page after successful associate login."""
    return render(request, 'InventoryManagementWebApp/select_operations.html')