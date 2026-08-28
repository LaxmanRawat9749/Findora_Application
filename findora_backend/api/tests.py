from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from api.models import (
    User, Item, FinderReputation, PointTransaction, FinderRating,
    UserBadge, Conversation, Notification
)
from api.serializers import (
    ItemSerializer, UserSerializer, PublicProfileSerializer,
    RegisterSerializer, ConversationSerializer, ChatMessageSerializer
)
from api.views import (
    ItemListCreateView, ItemDetailView, MarkItemReturnedView,
    ConfirmItemReturnView, ReputationProfileView, PointHistoryView,
    RateFinderView, RatingStatusView, MyReportsView, RegisterView
)
from api.reputation_service import (
    award_found_report_points, process_successful_return_reward,
    submit_finder_rating, get_or_create_reputation, get_badge_progress_list,
    check_and_award_badges
)
from api.reputation_constants import BADGES


class PermanentRoleRegistrationAndEnforcementTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_register_as_owner(self):
        """User registers with role='owner'. Account has permanent role 'owner'."""
        view = RegisterView.as_view()
        req = self.factory.post('/api/register/', {
            'username': 'ram_owner',
            'email': 'ram@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'first_name': 'Ram',
            'last_name': 'Thapa',
            'phone': '9800000001',
            'role': 'owner'
        })
        res = view(req)
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(username='ram_owner')
        self.assertEqual(user.role, 'owner')

    def test_register_as_finder(self):
        """User registers with role='finder'. Account has permanent role 'finder'."""
        view = RegisterView.as_view()
        req = self.factory.post('/api/register/', {
            'username': 'shyam_finder',
            'email': 'shyam@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'first_name': 'Shyam',
            'last_name': 'Gurung',
            'phone': '9800000002',
            'role': 'finder'
        })
        res = view(req)
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(username='shyam_finder')
        self.assertEqual(user.role, 'finder')

    def test_register_as_admin_rejected(self):
        """Registration with role='admin' must be rejected."""
        view = RegisterView.as_view()
        req = self.factory.post('/api/register/', {
            'username': 'fake_admin',
            'email': 'admin@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'first_name': 'Fake',
            'last_name': 'Admin',
            'phone': '9800000003',
            'role': 'admin'
        })
        res = view(req)
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(username='fake_admin').exists())

    def test_owner_can_report_lost_item_with_optional_reward(self):
        """Owner can report a lost item and optionally offer a monetary reward."""
        owner = User.objects.create_user(
            username='owner1', email='owner1@example.com', password='Password123!', role='owner', is_verified=True
        )
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=owner)
        request.user = owner

        data = {
            'type': 'lost',
            'title': 'Lost Dell XPS 15',
            'description': 'Silver laptop lost in library',
            'category': 'electronics',
            'location': 'Library Hall B',
            'reward': '1500.00'
        }
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(user=owner)
        self.assertEqual(item.type, 'lost')
        self.assertEqual(float(item.reward), 1500.00)
        self.assertEqual(ItemSerializer(item, context={'request': request}).data['user_role'], 'owner')

    def test_owner_cannot_report_found_item(self):
        """Owner attempting to report a found item must fail validation."""
        owner = User.objects.create_user(
            username='owner2', email='owner2@example.com', password='Password123!', role='owner', is_verified=True
        )
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=owner)
        request.user = owner

        data = {
            'type': 'found',
            'title': 'Found Dell Laptop',
            'description': 'Found silver laptop',
            'category': 'electronics',
            'location': 'Library'
        }
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)

    def test_finder_can_report_found_item_and_earns_5_points(self):
        """Finder can report a found item and earns 5 Finder points. Found item reward is 0."""
        finder = User.objects.create_user(
            username='finder1', email='finder1@example.com', password='Password123!', role='finder', is_verified=True
        )
        view = ItemListCreateView.as_view()
        req = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found iPhone 14 Pro',
            'description': 'Deep purple iPhone found on bus seat',
            'category': 'phone',
            'location': 'Bus No. 4',
            'reward': '0.00'
        })
        force_authenticate(req, user=finder)
        res = view(req)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['type'], 'found')
        self.assertEqual(float(res.data['reward']), 0.00)
        self.assertEqual(res.data['user_role'], 'finder')

        # Check reputation awarded 5 points
        rep = FinderReputation.objects.get(user=finder)
        self.assertEqual(rep.total_points, 5)

    def test_finder_cannot_report_lost_item(self):
        """Finder attempting to report a lost item must fail validation."""
        finder = User.objects.create_user(
            username='finder2', email='finder2@example.com', password='Password123!', role='finder', is_verified=True
        )
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=finder)
        request.user = finder

        data = {
            'type': 'lost',
            'title': 'Lost Keys',
            'description': 'Lost my room keys',
            'category': 'keys',
            'location': 'Park'
        }
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)

    def test_found_item_cannot_have_reward_for_finder(self):
        """Found item report cannot specify a reward amount > 0."""
        finder = User.objects.create_user(
            username='finder3', email='finder3@example.com', password='Password123!', role='finder', is_verified=True
        )
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=finder)
        request.user = finder

        data = {
            'type': 'found',
            'title': 'Found Backpack',
            'description': 'Black backpack with books',
            'category': 'bag',
            'location': 'Campus Gate',
            'reward': '500.00'
        }
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('reward', serializer.errors)


class ReturnWorkflowAndReputationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='balimante', email='bali@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='bijar', email='bijar@example.com', password='Password123!', role='finder', is_verified=True
        )

    def test_complete_return_awards_100_points_and_owner_rates_finder(self):
        """Lost phone return workflow: Finder gets 100 pts, Owner rates 5 stars (+10 bonus pts)."""
        lost_item = Item.objects.create(
            user=self.owner, type='lost', title='Lost Gold Watch', category='watch', status='approved'
        )
        conv = Conversation.objects.create(item=lost_item, owner=self.owner, finder=self.finder)

        # 1. Owner marks returned
        mark_view = MarkItemReturnedView.as_view()
        req_mark = self.factory.post(f'/api/items/{lost_item.id}/mark-returned/')
        force_authenticate(req_mark, user=self.owner)
        res_mark = mark_view(req_mark, pk=lost_item.id)
        self.assertEqual(res_mark.status_code, 200)

        # 2. Finder confirms return
        confirm_view = ConfirmItemReturnView.as_view()
        req_confirm = self.factory.post(f'/api/items/{lost_item.id}/confirm-return/')
        force_authenticate(req_confirm, user=self.finder)
        res_confirm = confirm_view(req_confirm, pk=lost_item.id)
        self.assertEqual(res_confirm.status_code, 200)

        # Finder received 100 points
        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 100)
        self.assertEqual(rep.successful_returns, 1)

        # Check Owner rating status
        status_view = RatingStatusView.as_view()
        req_status = self.factory.get(f'/api/reputation/rating-status/?item_id={lost_item.id}')
        force_authenticate(req_status, user=self.owner)
        res_status = status_view(req_status)
        self.assertEqual(res_status.status_code, 200)
        self.assertTrue(res_status.data['can_rate'])
        self.assertFalse(res_status.data['has_rated'])

        # Owner rates Finder 5 stars
        rate_view = RateFinderView.as_view()
        req_rate = self.factory.post('/api/reputation/rate/', {
            'item_id': lost_item.id,
            'rating': 5,
            'review': 'Extremely helpful and polite finder!'
        })
        force_authenticate(req_rate, user=self.owner)
        res_rate = rate_view(req_rate)
        self.assertEqual(res_rate.status_code, 201)

        # Finder received +10 bonus points for 5-star rating (100 + 10 = 110)
        rep.refresh_from_db()
        self.assertEqual(rep.total_points, 110)
        self.assertEqual(rep.average_rating, 5.0)
        self.assertEqual(rep.rating_count, 1)

    def test_finder_cannot_rate_owner(self):
        """Finder attempting to rate the Owner must be forbidden."""
        lost_item = Item.objects.create(
            user=self.owner, type='lost', title='Lost Tablet', category='electronics', status='resolved'
        )
        PointTransaction.objects.create(
            user=self.finder, points=100, transaction_type='SUCCESSFUL_RETURN', related_item=lost_item
        )

        rate_view = RateFinderView.as_view()
        req_rate = self.factory.post('/api/reputation/rate/', {
            'item_id': lost_item.id,
            'rating': 5
        })
        force_authenticate(req_rate, user=self.finder)
        res_rate = rate_view(req_rate)
        self.assertEqual(res_rate.status_code, 403)

    def test_owner_reputation_and_points_access_forbidden(self):
        """Owners cannot access /api/reputation/me/ or /api/reputation/history/."""
        view_rep = ReputationProfileView.as_view()
        req_rep = self.factory.get('/api/reputation/me/')
        force_authenticate(req_rep, user=self.owner)
        res_rep = view_rep(req_rep)
        self.assertEqual(res_rep.status_code, 403)

        view_hist = PointHistoryView.as_view()
        req_hist = self.factory.get('/api/reputation/history/')
        force_authenticate(req_hist, user=self.owner)
        res_hist = view_hist(req_hist)
        self.assertEqual(res_hist.status_code, 403)

    def test_trusted_finder_qualification(self):
        """Trusted Finder requires rating >= 4.0 and successful returns > 3 (min 4 returns)."""
        rep = get_or_create_reputation(self.finder)
        rep.rating_count = 2
        rep.rating_sum = 10
        rep.average_rating = 5.0
        rep.successful_returns = 3
        rep.save()

        # 3 returns is not > 3
        self.assertFalse(rep.is_trusted_finder)
        self.assertFalse(self.finder.is_trusted_finder)

        # 4 returns is > 3
        rep.successful_returns = 4
        rep.save()
        self.assertTrue(rep.is_trusted_finder)
        self.assertTrue(self.finder.is_trusted_finder)

        # Low rating drops trusted finder status
        rep.average_rating = 3.5
        rep.save()
        self.assertFalse(rep.is_trusted_finder)


class ItemMatchingAndRoleVisibilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='thor_owner', email='thor@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='iron_finder', email='iron@example.com', password='Password123!', role='finder', is_verified=True
        )

        # Thor lost an iPhone 13
        self.lost_phone = Item.objects.create(
            user=self.owner, type='lost', title='Black iPhone 13 Pro', category='phone', status='approved'
        )
        # Iron found an iPhone
        self.matched_found_phone = Item.objects.create(
            user=self.finder, type='found', title='Found iPhone 13 in Park', category='phone', status='approved'
        )
        # Iron found unrelated sunglasses
        self.unmatched_found_glasses = Item.objects.create(
            user=self.finder, type='found', title='Found RayBan Sunglasses', category='other', status='approved'
        )

    def test_owner_sees_only_matched_found_items(self):
        """Owner browsing found items only sees found items matching their lost reports."""
        view = ItemListCreateView.as_view()
        req = self.factory.get('/api/items/?type=found')
        force_authenticate(req, user=self.owner)
        res = view(req)
        self.assertEqual(res.status_code, 200)
        item_ids = [item['id'] for item in res.data]
        self.assertIn(self.matched_found_phone.id, item_ids)
        self.assertNotIn(self.unmatched_found_glasses.id, item_ids)

    def test_finder_sees_all_found_and_lost_items(self):
        """Finder browsing items can see all approved lost and found items."""
        view = ItemListCreateView.as_view()

        # Lost items
        req_lost = self.factory.get('/api/items/?type=lost')
        force_authenticate(req_lost, user=self.finder)
        res_lost = view(req_lost)
        self.assertEqual(res_lost.status_code, 200)
        lost_ids = [item['id'] for item in res_lost.data]
        self.assertIn(self.lost_phone.id, lost_ids)

        # Found items
        req_found = self.factory.get('/api/items/?type=found')
        force_authenticate(req_found, user=self.finder)
        res_found = view(req_found)
        self.assertEqual(res_found.status_code, 200)
        found_ids = [item['id'] for item in res_found.data]
        self.assertIn(self.matched_found_phone.id, found_ids)
        self.assertIn(self.unmatched_found_glasses.id, found_ids)
