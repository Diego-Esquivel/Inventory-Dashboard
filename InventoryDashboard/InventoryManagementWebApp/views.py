from django.shortcuts import render
from django.http import HttpResponse
from django.http import QueryDict
# Create your views here.


from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Associate, Inventory, TransactionHistory
from .forms import *

class Endpoints:
    def index(request):
        return Endpoints.login_view(request)

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
        if Endpoints.has_valid_session(request):
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
        if Endpoints.has_valid_session(request):
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
        create_new_inventory_product_form = CreateInventoryProductForm()
        if request.method == 'POST':
            # Process form data here to create a new inventory product
            result = Middleware._create_new_inventory_product(request.POST, request.user.associate)
            # If the creation was successful, redirect to select_operations; if not, re-render the form
            if result == 1:
                # Return success message for the frontend to display in create_new_inventory_product.html
                messages.success(request, "Inventory product created successfully.")
                return render(request, 'InventoryManagementWebApp/create_new_inventory_product.html', {'form': create_new_inventory_product_form}, status=200)
            else:
                messages.error(request, 'Failed to create inventory product. Please try again.')
                # Return message for the frontend to display
                return render(request, "InventoryManagementWebApp/create_new_inventory_product.html", {'form': create_new_inventory_product_form}, status=200)
        return render(request, "InventoryManagementWebApp/create_new_inventory_product.html", {'form': create_new_inventory_product_form})

    @login_required
    def read_inventory_products(request):
        """Read existing inventory products.
        If the method is a post request, process the form data to filter and display products."""
        read_inventory_products_form = ReadInventoryProductsForm()
        if request.method == 'POST':
            # Process form data here to read inventory products
            products = Middleware._read_inventory_products(request.POST, request.user.associate)
            if products is None or len(products) == 0:
                # There are no products matching the criteria; re-render the form with a message
                messages.info(request, 'No inventory products found matching the criteria.')
                return render(request, "InventoryManagementWebApp/read_inventory_products.html", {'form': read_inventory_products_form}, status=200)
            else:
                # There are products matching the criteria; render them
                return render(request, "InventoryManagementWebApp/read_inventory_products.html", {'inventory_products': products, 'form': read_inventory_products_form}, status=200)
        return render(request, "InventoryManagementWebApp/read_inventory_products.html", {'form': read_inventory_products_form})
    
    @login_required
    def read_inventory_product(request):
        """Read a single existing inventory product.
        Extract the product ID from the query parameters and display the product details."""
        record_id = request.GET.get('q')
        if record_id:
            try:
                product = Inventory.objects.get(record_id=int(record_id.strip()))
                transaction_history = TransactionHistory.objects.filter(inventory_item=product).order_by('-timestamp')
                return render(request, "InventoryManagementWebApp/read_inventory_product.html", {'inventory_product': product, 'transaction_history': transaction_history})
            except Inventory.DoesNotExist:
                messages.error(request, f'No inventory product found with Record ID: {record_id}.')
                return redirect('read_inventory_products')
        return redirect('read_inventory_products')

    @login_required
    def update_inventory_product_location(request):
        """Update location for an existing inventory product.
        If the method is a post request, it is either updating the location or searching for products to update.
        If it is a request to search for products, it will render the products matching the criteria.
        If it is a request to update the location, it will process the form data to update the location."""
        read_inventory_products_form = ReadInventoryProductsForm()
        if request.method == 'POST':
            if 'new_storage_location' in request.POST:
                # This is a request to update the location
                result = Middleware._update_inventory_product_location(request.POST, request.user.associate)
                # Get the products again to display
                products = Middleware._read_inventory_products(request.POST, request.user.associate)
                if result == 1:
                    messages.success(request, "Inventory product location updated successfully.")
                else:
                    messages.error(request, 'Failed to update inventory product location. Please try again.')
                return render(request, "InventoryManagementWebApp/update_inventory_product_location.html", {'form': read_inventory_products_form, 'inventory_products': products}, status=200)
            else:
                # This is a request to search for products to update
                products = Middleware._read_inventory_products(request.POST, request.user.associate)
                if products is None or len(products) == 0:
                    # There are no products matching the criteria; re-render the form with a message
                    messages.info(request, 'No inventory products found matching the criteria.')
                    return render(request, "InventoryManagementWebApp/update_inventory_product_location.html", {'form': read_inventory_products_form}, status=200)
                else:
                    # There are products matching the criteria; render them
                    return render(request, "InventoryManagementWebApp/update_inventory_product_location.html", {'inventory_products': products, 'form': read_inventory_products_form}, status=200)
        return render(request, "InventoryManagementWebApp/update_inventory_product_location.html", {'form': read_inventory_products_form})

    @login_required
    def update_inventory_product_quantity_on_pallet(request):
        """Update quantity on pallet for an existing inventory product.
        If the method is a post request, it is either updating the quantity or searching for products to update.
        If it is a request to search for products, it will render the products matching the criteria.
        If it is a request to update the quantity, it will process the form data to update the quantity."""
        read_inventory_products_form = ReadInventoryProductsForm()
        if request.method == 'POST':
            if 'new_quantity' in request.POST:
                # This is a request to update the location
                result = Middleware._update_inventory_product_quantity_on_pallet(request.POST, request.user.associate)
                # Get the products again to display
                products = Middleware._read_inventory_products(request.POST, request.user.associate)
                if result == 1:
                    messages.success(request, "Inventory product quantity updated successfully.")
                else:
                    messages.error(request, 'Failed to update inventory product quantity. Please try again.')
                return render(request, "InventoryManagementWebApp/update_inventory_product_quantity_on_pallet.html", {'form': read_inventory_products_form, 'inventory_products': products}, status=200)
            else:
                # This is a request to search for products to update
                products = Middleware._read_inventory_products(request.POST, request.user.associate)
                if products is None or len(products) == 0:
                    # There are no products matching the criteria; re-render the form with a message
                    messages.info(request, 'No inventory products found matching the criteria.')
                    return render(request, "InventoryManagementWebApp/update_inventory_product_quantity_on_pallet.html", {'form': read_inventory_products_form}, status=200)
                else:
                    # There are products matching the criteria; render them
                    return render(request, "InventoryManagementWebApp/update_inventory_product_quantity_on_pallet.html", {'inventory_products': products, 'form': read_inventory_products_form}, status=200)
        return render(request, "InventoryManagementWebApp/update_inventory_product_quantity_on_pallet.html", {'form': read_inventory_products_form})

    @login_required
    def delete_inventory_product(request):
        """Delete an inventory product."""
        return render(request, "InventoryManagementWebApp/delete_inventory_product.html")

class Middleware:
    def _create_new_inventory_product(form_data:QueryDict, associate):
        """Create a new inventory product.
        Extracts data from the html form data and creates the product in the database.
        Returns 1 on success, 0 on failure."""
        label_id = form_data.get('label_id').strip()
        product_description = form_data.get('product_description').strip()
        quantity_on_pallet = form_data.get('quantity_on_pallet').strip()
        storage_location = form_data.get('storage_location').strip()
        try:
            Inventory.objects.create(
                label_id=label_id,
                product_description=product_description,
                quantity_on_pallet=int(quantity_on_pallet),
                storage_location=storage_location,
                associate=associate
            )
            return 1
        except Exception as e:
            print(f"Error creating inventory product: {e}")
            return 0
        
    def _read_inventory_products(form_data:QueryDict, associate):
        """Read existing inventory products.
        Returns a list of inventory products matching the criteria.
        Extracts data from the html form data to filter the products."""
        record_id = form_data.get('product_id')
        label_id = form_data.get('label_id')
        storage_location = form_data.get('storage_location')
        quantity_on_pallet = form_data.get('quantity_on_pallet')
        product_description = form_data.get('product_description')
        scheduled_for_deletion = form_data.get('scheduled_for_deletion')
        filters = {}
        if record_id:
            filters['record_id'] = int(record_id.strip())
        if label_id:
            filters['label_id__icontains'] = label_id.strip()
        if storage_location:
            filters['storage_location__icontains'] = storage_location.strip()
        if quantity_on_pallet:
            filters['quantity_on_pallet'] = int(quantity_on_pallet.strip())
        if product_description:
            filters['product_description__icontains'] = product_description.strip()
        if scheduled_for_deletion:
            # If the checkbox is checked, filter for scheduled for deletion items with non-null deletion date
            filters['scheduled_for_deletion__isnull'] = False
        return Inventory.objects.filter(**filters)

    def _update_inventory_product_location(form_data, associate):
        """Update location for an existing inventory product.
        Extracts data from the html form data to update the product location.
        Returns 1 on success, 0 on failure."""
        new_location = form_data.get('new_storage_location')
        product_id = form_data.get('product_id')
        try:
            inventory_item = Inventory.objects.get(record_id=int(product_id.strip()))
            inventory_item.update_location(new_location.strip(), associate)
            return 1
        except Exception as e:
            print(f"Error updating inventory product location: {e}")
            return 0

    def _update_inventory_product_quantity_on_pallet(form_data, associate):
        """Update quantity on pallet for an existing inventory product.
        Extracts data from the html form data to update the product quantity.
        Returns 1 on success, 0 on failure."""
        new_quantity = form_data.get('new_quantity')
        product_id = form_data.get('product_id')
        try:
            if int(new_quantity.strip()) < 0:
                raise ValueError("Quantity on pallet cannot be negative.")
            inventory_item = Inventory.objects.get(record_id=int(product_id.strip()))
            inventory_item.update_quantity(int(new_quantity.strip()), associate)
            return 1
        except Exception as e:
            print(f"Error updating inventory product quantity: {e}")
            return 0

    def _delete_inventory_product(form_data, associate):
        """Delete an inventory product."""
        return render(request, "InventoryManagementWebApp/delete_inventory_product.html")