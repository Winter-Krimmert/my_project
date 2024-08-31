from rest_framework.test import APITestCase

class UserRegistrationTests(APITestCase):
    def test_username_taken(self):
        self.client.post('/api/register/', {'username': 'testuser', 'password': 'Testpassword1'})
        response = self.client.post('/api/register/', {'username': 'testuser', 'password': 'Testpassword1'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username already taken', str(response.data))

    def test_weak_password(self):
        response = self.client.post('/api/register/', {'username': 'newuser', 'password': 'weak'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Password must be at least 8 characters long', str(response.data))
