from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from .models import Associate


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
