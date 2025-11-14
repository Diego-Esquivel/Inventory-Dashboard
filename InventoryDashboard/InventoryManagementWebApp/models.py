from django.db import models

# Create your models here.
class Associate(models.Model):
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