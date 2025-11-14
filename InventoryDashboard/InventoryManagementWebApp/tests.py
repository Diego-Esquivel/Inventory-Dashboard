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
