from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

TIME_TO_WAIT_BEFORE_DELETION = 45  # days

# Create your models here.
class Associate(models.Model):
    # Create an Associate model linked to Django's built-in User model with a valid default
    django_user = models.OneToOneField('auth.User', on_delete=models.CASCADE, default=None, blank=True, null=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=20)
    is_manager = models.BooleanField(default=False)
    is_authenticated = models.BooleanField(default=False)

    def authenticate(self, password):
        """ Authenticate the associate with the given password. 
        Using a simple password check for demonstration purposes.
        A real application should use hashed passwords."""
        if self.password == password:
            self.is_authenticated = True
        else:
            self.is_authenticated = False
        self.save()
        return self.is_authenticated

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure that the associated User object is created/updated
        if not self.django_user:
            user = User.objects.create_user(username=self.name, password=self.password)
            self.django_user = user
        super().save(*args, **kwargs)

class TransactionHistory(models.Model):
    """Model to store transaction history for inventory items.
    
    A transaction history record includes the record id of the inventory item modified,
    name of the action being performed, the date and time of the transaction, and the 
    associate who performed it."""
    class Actions(models.TextChoices):
        CREATED = 'CREA', 'Created'
        DELETED = 'DELE', 'Deleted'
        MOVE_LOCATION = 'MOVE', 'Move Location'
        EDIT_QUANTITY = 'QUAN', 'Edit Quantity'
    record_id = models.AutoField(primary_key=True)
    inventory_item = models.ForeignKey('Inventory', on_delete=models.CASCADE)
    action_name = models.CharField(max_length=4, choices=Actions.choices, default=Actions.CREATED)
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(Associate, on_delete=models.CASCADE)
    previous_quantity = models.IntegerField(null=True, blank=True)
    new_quantity = models.IntegerField(null=True, blank=True)
    previous_location = models.CharField(max_length=4, null=True, blank=True)
    new_location = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return f"TransactionHistory {self.record_id}"

class Inventory(models.Model):
    record_id = models.AutoField(primary_key=True)
    label_id = models.CharField(max_length=100)
    storage_location = models.CharField(max_length=4)
    quantity_on_pallet = models.IntegerField(default=0)
    product_description = models.CharField(max_length=200)
    transaction_history = models.OneToOneField(TransactionHistory, on_delete=models.CASCADE)
    scheduled_for_deletion = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.product_name} - {self.quantity} units at location {self.storage_location}"

    def delete(self, associate):
        # Override delete method to create a transaction history record
        self.scheduled_for_deletion = datetime.now()
        self.save()
        # Schedule for deletion after TIME_TO_WAIT_BEFORE_DELETION days
        TransactionHistory.objects.create(
            inventory_item=self,
            action_name=TransactionHistory.Actions.DELETED,
            performed_by=self.associate  # In a real application, set the associate performing the deletion
        )
        