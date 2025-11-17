from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from .models import *


class LoginTests(TestCase):
    def setUp(self):
        # Create a test user for successful login
        self.username = 'testassociate'
        self.password = 'Secr3tPass!'
        Associate.objects.create(name=self.username, password=self.password)

    def test_login_success(self):
        resp = self.client.post('/login/', {'username': self.username, 'password': self.password})
        # on success we redirect to select-operations
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.endswith('/select-operations/'))

    def test_login_failure(self):
        resp = self.client.post('/login/', {'username': self.username, 'password': 'badpass'})
        # invalid credentials should re-render login page (status 200) with error message
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')
        
    def test_logout(self):
        # First, log in the user
        self.client.post('/login/', {'username': self.username, 'password': self.password})
        # Now, log out
        resp = self.client.get('/logout/')
        # After logout, we should be redirected to the login page
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.endswith('/login/'))
        # Verify that the user is logged out by checking the session
        resp = self.client.get('/select-operations/')
        self.assertEqual(resp.status_code, 302)  # Should redirect to login since user is logged out

class InventoryTests(TestCase):
    def setUp(self):
        # Create a test associate
        self.not_manager = Associate.objects.create(name='testassociate', password='Secr3tPass!', is_manager=False)
        self.associate = Associate.objects.create(name='inventorymanager', password='Inv3nt0ry!', is_manager=True)
        # Create a test inventory item
        self.inventory_item = Inventory.objects.create(
            label_id='ITEM123',
            storage_location='A1',
            quantity_on_pallet=50,
            product_description='Test Product',
            associate=self.associate
        )

    def test_create_inventory_item(self):
        initial_count = Inventory.objects.count()
        new_item = Inventory.objects.create(
            label_id='ITEM456',
            storage_location='B2',
            quantity_on_pallet=30,
            product_description='Another Product',
            associate=self.associate
        )
        new_item = Inventory.objects.get(label_id='ITEM456')
        self.assertEqual(Inventory.objects.count(), initial_count + 1)
        self.assertEqual(new_item.label_id, 'ITEM456')
        self.assertEqual(new_item.storage_location, 'B2')
        self.assertEqual(new_item.quantity_on_pallet, 30)
        self.assertEqual(new_item.product_description, 'Another Product')
    
    def test_update_inventory_quantity(self):
        previous_quantity = self.inventory_item.quantity_on_pallet
        new_quantity = 75
        self.inventory_item.update_quantity(new_quantity, self.associate)
        updated_item = Inventory.objects.get(record_id=self.inventory_item.record_id)
        self.assertEqual(updated_item.quantity_on_pallet, new_quantity)
        # Verify that a transaction history record was created
        transaction = TransactionHistory.objects.filter(
            inventory_item=updated_item,
            action_name=TransactionHistory.Actions.EDIT_QUANTITY
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.previous_quantity, previous_quantity)

    def test_update_inventory_location(self):
        previous_location = self.inventory_item.storage_location
        new_location = 'C3'
        self.inventory_item.update_location(new_location, self.associate)
        updated_item = Inventory.objects.get(record_id=self.inventory_item.record_id)
        self.assertEqual(updated_item.storage_location, new_location)
        # Verify that a transaction history record was created
        transaction = TransactionHistory.objects.filter(
            inventory_item=updated_item,
            action_name=TransactionHistory.Actions.MOVE_LOCATION
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.previous_location, previous_location)
    
    def test_can_delete_inventory_item_as_manager(self):
        self.inventory_item.delete(self.associate)
        deleted_item = Inventory.objects.get(record_id=self.inventory_item.record_id)
        self.assertIsNotNone(deleted_item.scheduled_for_deletion)
        # Verify that a transaction history record was created
        transaction = TransactionHistory.objects.filter(
            inventory_item=deleted_item,
            action_name=TransactionHistory.Actions.DELETED
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.inventory_item.record_id, deleted_item.record_id)
        self.assertEqual(transaction.action_name, TransactionHistory.Actions.DELETED)
        self.assertEqual(transaction.performed_by.id, self.associate.id)

    def test_cannot_delete_inventory_item_as_non_manager(self):
        with self.assertRaises(PermissionError):
            self.inventory_item.delete(self.not_manager)

    def test_create_inventory_item_without_location(self):
        new_item = Inventory.objects.create(
            label_id='ITEM789',
            product_description='No Location Product',
            associate=self.associate,
            quantity_on_pallet=100
        )
        new_item = Inventory.objects.get(label_id='ITEM789')
        self.assertEqual(new_item.storage_location, 'HOLD')
        self.assertEqual(new_item.quantity_on_pallet, 100)
    
    def test_create_inventory_item_without_quantity(self):
        new_item = Inventory.objects.create(
            label_id='ITEM101',
            product_description='No Quantity Product',
            associate=self.associate,
            storage_location='D4'
        )
        new_item = Inventory.objects.get(label_id='ITEM101')
        self.assertEqual(new_item.storage_location, 'D4')
        self.assertEqual(new_item.quantity_on_pallet, -100)
    
    def test_create_inventory_item_without_location_and_quantity(self):
        new_item = Inventory.objects.create(
            label_id='ITEM202',
            product_description='No Location and Quantity Product',
            associate=self.associate
        )
        new_item = Inventory.objects.get(label_id='ITEM202')
        self.assertEqual(new_item.storage_location, 'HOLD')
        self.assertEqual(new_item.quantity_on_pallet, -100)
    
    def test_cannot_create_inventory_item_without_label_id(self):
        with self.assertRaises(Exception):
            Inventory.objects.create(
                product_description='No Label ID Product',
                associate=self.associate,
                storage_location='E5',
                quantity_on_pallet=20
            )
    
    def test_cannot_create_inventory_item_without_description(self):
        with self.assertRaises(Exception):
            Inventory.objects.create(
                label_id='ITEM303',
                associate=self.associate,
                storage_location='F6',
                quantity_on_pallet=20
            )
    
    def test_cannot_create_inventory_item_without_associate(self):
        with self.assertRaises(Exception):
            Inventory.objects.create(
                label_id='ITEM404',
                product_description='No Associate Product',
                storage_location='G7',
                quantity_on_pallet=20
            )

    def test_create_inventory_item_with_duplicate_label_id(self):
        Inventory.objects.create(
            label_id='DUPLICATE123',
            product_description='First Product',
            associate=self.associate,
            storage_location='H8',
            quantity_on_pallet=10
        )
        # Creating another item with the same label_id should be allowed
        second_item = Inventory.objects.create(
            label_id='DUPLICATE123',
            product_description='Second Product',
            associate=self.associate,
            storage_location='I9',
            quantity_on_pallet=15
        )
        self.assertIsNotNone(second_item)
        self.assertEqual(second_item.label_id, 'DUPLICATE123')

class CreateNewInventoryProductViewTests(TestCase):
    def setUp(self):
        # Create a test associate and log in
        self.associate = Associate.objects.create(name='inventorymanager', password='Inv3nt0ry!', is_manager=True)
        self.associate2 = Associate.objects.create(name='testassociate', password='Secr3tPass!', is_manager=False)
        self.client.post('/login/', {'username': 'inventorymanager', 'password': 'Inv3nt0ry!'})

    def test_create_new_inventory_product_view_get(self):
        resp = self.client.get('/create-new-inventory-product/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Create New Inventory Item')

    def test_create_new_inventory_product_view_post_success(self):
        resp = self.client.post('/create-new-inventory-product/', {
            'label_id': 'NEWITEM123',
            'product_description': 'New Test Product',
            'quantity_on_pallet': 40,
            'storage_location': 'J10'
        })
        # On success, we should get a 200 status with success message
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Inventory product created successfully.')
        # Verify that the item was created in the database
        new_item = Inventory.objects.get(label_id='NEWITEM123')
        self.assertIsNotNone(new_item)
        self.assertEqual(new_item.product_description, 'New Test Product')

    def test_create_new_inventory_product_view_post_failure(self):
        resp = self.client.post('/create-new-inventory-product/', {
            'label_id': '',  # Missing label_id should cause failure
            'product_description': 'New Test Product',
            'quantity_on_pallet': 40,
            'storage_location': 'J10'
        })
        # On failure, we should get a 200 status with error message
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Failed to create inventory product. Please try again.')
        # Verify that the item was not created in the database
        with self.assertRaises(Inventory.DoesNotExist):
            Inventory.objects.get(product_description='New Test Product')

class ReadInventoryProductsViewTests(TestCase):
    def setUp(self):
        # Create a test associate and log in
        self.associate = Associate.objects.create(name='inventorymanager', password='Inv3nt0ry!', is_manager=True)
        self.client.post('/login/', {'username': 'inventorymanager', 'password': 'Inv3nt0ry!'})
        # Create some test inventory items
        Inventory.objects.create(
            label_id='ITEM001',
            storage_location='A1',
            quantity_on_pallet=20,
            product_description='Test Product 1',
            associate=self.associate
        )
        Inventory.objects.create(
            label_id='ITEM002',
            storage_location='B2',
            quantity_on_pallet=30,
            product_description='Test Product 2',
            associate=self.associate
        )

    def test_read_inventory_products_view_get(self):
        resp = self.client.get('/read-inventory-products/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Read Inventory Products')

    def test_read_inventory_products_view_post_with_results(self):
        resp = self.client.post('/read-inventory-products/', {
            'label_id': 'ITEM001'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Product 1')
        self.assertNotContains(resp, 'Test Product 2')

    def test_read_inventory_products_view_post_no_results(self):
        resp = self.client.post('/read-inventory-products/', {
            'label_id': 'NONEXISTENT'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No inventory products found matching the criteria.')

class UpdateInventoryProductLocationViewTests(TestCase):
    def setUp(self):
        # Create a test associate and log in
        self.associate = Associate.objects.create(name='inventorymanager', password='Inv3nt0ry!', is_manager=True)
        self.client.post('/login/', {'username': 'inventorymanager', 'password': 'Inv3nt0ry!'})
        # Create some test inventory items
        self.item1 = Inventory.objects.create(
            label_id='ITEM001',
            storage_location='A1',
            quantity_on_pallet=20,
            product_description='Test Product 1',
            associate=self.associate
        )
        self.item2 = Inventory.objects.create(
            label_id='ITEM002',
            storage_location='B2',
            quantity_on_pallet=30,
            product_description='Test Product 2',
            associate=self.associate
        )

    def test_update_inventory_product_location_view_get(self):
        resp = self.client.get('/update-inventory-product-location/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Update Inventory Product Location')

    def test_update_inventory_product_location_view_post_search_with_results(self):
        resp = self.client.post('/update-inventory-product-location/', {
            'label_id': 'ITEM001'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Product 1')
        self.assertNotContains(resp, 'Test Product 2')

    def test_update_inventory_product_location_view_post_search_no_results(self):
        resp = self.client.post('/update-inventory-product-location/', {
            'label_id': 'NONEXISTENT'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No inventory products found matching the criteria.')

class ReadInventoryProductViewTests(TestCase):
    def setUp(self):
        # Create a test associate and log in
        self.associate = Associate.objects.create(name='inventorymanager', password='Inv3nt0ry!', is_manager=True)
        self.client.post('/login/', {'username': 'inventorymanager', 'password': 'Inv3nt0ry!'})
        # Create a test inventory item
        self.inventory_item = Inventory.objects.create(
            label_id='ITEM123',
            storage_location='A1',
            quantity_on_pallet=50,
            product_description='Test Product',
            associate=self.associate
        )

    def test_read_inventory_product_view_get(self):
        resp = self.client.get('/read-inventory-product/')
        # Verify redirected to read inventory products page
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/read-inventory-products/')

    def test_read_inventory_product_view_get_found(self):
        resp = self.client.get('/read-inventory-product/?q={}'.format(self.inventory_item.record_id))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Product')
        self.assertContains(resp, 'ITEM123')

    def test_read_inventory_product_view_get_not_found(self):
        resp = self.client.get('/read-inventory-product/', {'q': 9999})  # Assuming 9999 does not exist
        # Verify redirected to read inventory products page
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/read-inventory-products/')
