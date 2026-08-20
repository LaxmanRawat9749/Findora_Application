"""
Findora Unit and Integration Tests.
"""

from django.test import TestCase, Client
from api.models import (
    User,
    Administrator,
    Item,
    Claim,
    Payment,
    Notification,
    AdminAuditLog,
)


class AdminSeparationTestCase(TestCase):
    """Test suite ensuring strict structural separation of Admin and App Users."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='unit_owner',
            email='unit_owner@test.com',
            password='OwnerPassword123!',
            role='owner',
            is_verified=True,
        )
        self.finder = User.objects.create_user(
            username='unit_finder',
            email='unit_finder@test.com',
            password='FinderPassword123!',
            role='finder',
            is_verified=True,
        )
        self.admin = Administrator.objects.create_superuser(
            username='unit_admin',
            email='unit_admin@test.com',
            password='AdminPassword123!',
        )

    def test_user_isolation(self):
        """Ensure Owners/Finders are in User table and Admins in Administrator table."""
        self.assertTrue(User.objects.filter(username='unit_owner').exists())
        self.assertTrue(User.objects.filter(username='unit_finder').exists())
        self.assertFalse(User.objects.filter(username='unit_admin').exists())

        self.assertTrue(Administrator.objects.filter(username='unit_admin').exists())
        self.assertFalse(Administrator.objects.filter(username='unit_owner').exists())
        self.assertFalse(Administrator.objects.filter(username='unit_finder').exists())

    def test_admin_login_and_dashboard(self):
        """Admin can log in to /admin/ and view the dashboard."""
        logged_in = self.client.login(username='unit_admin', password='AdminPassword123!')
        self.assertTrue(logged_in)

        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_owner_finder_denied_admin_access(self):
        """Owner and Finder credentials cannot log into Django Admin."""
        # Submitting to /admin/login/
        res_owner = self.client.post('/admin/login/', {'username': 'unit_owner', 'password': 'OwnerPassword123!'}, follow=True)
        self.assertFalse(self.client.session.get('_auth_user_id'))

        res_finder = self.client.post('/admin/login/', {'username': 'unit_finder', 'password': 'FinderPassword123!'}, follow=True)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_api_login_success_for_users_only(self):
        """API login works for users, but rejects admin accounts."""
        res_owner = self.client.post('/api/login/', {'username': 'unit_owner', 'password': 'OwnerPassword123!'}, content_type='application/json')
        self.assertEqual(res_owner.status_code, 200)
        self.assertIn('access', res_owner.json())

        res_admin = self.client.post('/api/login/', {'username': 'unit_admin', 'password': 'AdminPassword123!'}, content_type='application/json')
        self.assertEqual(res_admin.status_code, 401)

    def test_deletion_decoupling(self):
        """Deleting an application user does not delete admin and vice-versa."""
        self.owner.delete()
        self.assertTrue(Administrator.objects.filter(username='unit_admin').exists())

        self.admin.delete()
        self.assertTrue(User.objects.filter(username='unit_finder').exists())
