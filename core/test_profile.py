from django.test import TestCase
from django.urls import reverse

from .models import User


class ProfilePageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='sho@example.com', password='OldPassword123!X', first_name='Sho', last_name='Example')
        self.client.force_login(self.user)

    def test_profile_page_renders(self):
        response = self.client.get(reverse('profile-page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your profile')
        self.assertContains(response, 'Change password')

    def test_profile_updates_name_and_email_with_current_password(self):
        response = self.client.post(reverse('profile-page'), {
            'form_type': 'profile',
            'first_name': 'Mohammed',
            'last_name': 'Shoaib',
            'email': 'new@example.com',
            'profile_current_password': 'OldPassword123!X',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Mohammed')
        self.assertEqual(self.user.last_name, 'Shoaib')
        self.assertEqual(self.user.email, 'new@example.com')

    def test_password_change_keeps_session(self):
        response = self.client.post(reverse('profile-page'), {
            'form_type': 'password',
            'current_password': 'OldPassword123!X',
            'new_password': 'NewPassword123!Y',
            'confirm_password': 'NewPassword123!Y',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!Y'))
        self.assertEqual(response.wsgi_request.user.pk, self.user.pk)
