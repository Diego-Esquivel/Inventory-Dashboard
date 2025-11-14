from django.db import models
from django.contrib.auth.models import User

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