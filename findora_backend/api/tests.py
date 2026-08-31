from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from api.models import (
    User, Item, ItemImage, FinderReputation, PointTransaction, FinderRating,
    UserBadge, Conversation, Notification, ChatMessage
)
from api.serializers import (
    ItemSerializer, UserSerializer, PublicProfileSerializer,
    RegisterSerializer, ConversationSerializer, ChatMessageSerializer
)
from api.views import (
    ItemListCreateView, ItemDetailView, MarkItemReturnedView,
    ConfirmItemReturnView, ReputationProfileView, PointHistoryView,
    RateFinderView, RatingStatusView, MyReportsView, RegisterView,
    ConversationInitView, ChatListView, NotificationListView,
    AdminItemListView, AdminVerifyItemView
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

    @patch('api.views.send_otp_email')
    def test_register_as_owner(self, mock_send_email):
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

    @patch('api.views.send_otp_email')
    def test_register_as_finder(self, mock_send_email):
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
        """Finder can report a found item with exactly 1 photo and earns 5 Finder points. Found item reward is 0."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        finder = User.objects.create_user(
            username='finder1', email='finder1@example.com', password='Password123!', role='finder', is_verified=True
        )
        view = ItemListCreateView.as_view()
        img = SimpleUploadedFile('iphone.jpg', b'fake_photo_data', content_type='image/jpeg')
        req = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found iPhone 14 Pro',
            'description': 'Deep purple iPhone found on bus seat',
            'category': 'phone',
            'location': 'Bus No. 4',
            'reward': '0.00',
            'images': [img]
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

    def test_finder_without_photo_is_rejected(self):
        """Finder attempting to report a found item without a photo must fail."""
        finder = User.objects.create_user(
            username='finder_no_photo', email='finder_np@example.com', password='Password123!', role='finder', is_verified=True
        )
        view = ItemListCreateView.as_view()
        req = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Keys',
            'description': 'Found keychain',
            'category': 'keys',
            'location': 'Cafeteria',
        })
        force_authenticate(req, user=finder)
        res = view(req)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], 'Please upload 1 photo of the found item.')

    def test_owner_with_0_or_1_photo(self):
        """Owner can report a lost item with 0 photos or 1 photo."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        owner = User.objects.create_user(
            username='owner_photos', email='owner_p@example.com', password='Password123!', role='owner', is_verified=True
        )
        view = ItemListCreateView.as_view()
        # 0 photos
        req0 = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost Keys 0 Photo',
            'description': 'Lost my room keys',
            'category': 'keys',
            'location': 'Park',
        })
        force_authenticate(req0, user=owner)
        res0 = view(req0)
        self.assertEqual(res0.status_code, 201)

        # 1 photo
        img = SimpleUploadedFile('keys.jpg', b'keys_photo_data', content_type='image/jpeg')
        req1 = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost Keys 1 Photo',
            'description': 'Lost my room keys with photo',
            'category': 'keys',
            'location': 'Park',
            'images': [img]
        })
        force_authenticate(req1, user=owner)
        res1 = view(req1)
        self.assertEqual(res1.status_code, 201)

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

    def test_owner_visibility_and_finder_visibility(self):
        """
        Owner A sees only Owner A's items.
        Owner B sees only Owner B's items.
        Finder sees ALL lost and found items.
        """
        owner_a = User.objects.create_user(
            username='owner_a', email='owner_a@example.com', password='Password123!', role='owner', is_verified=True
        )
        owner_b = User.objects.create_user(
            username='owner_b', email='owner_b@example.com', password='Password123!', role='owner', is_verified=True
        )
        finder_a = User.objects.create_user(
            username='finder_a', email='finder_a@example.com', password='Password123!', role='finder', is_verified=True
        )

        item_a = Item.objects.create(
            user=owner_a, title="Owner A's Wallet", description="Black leather wallet",
            category="wallet", type="lost", status="approved"
        )
        item_b = Item.objects.create(
            user=owner_b, title="Owner B's Phone", description="Samsung S23",
            category="phone", type="lost", status="approved"
        )
        item_f = Item.objects.create(
            user=finder_a, title="Finder A's Found Watch", description="Casio watch",
            category="other", type="found", status="approved"
        )

        view = ItemListCreateView.as_view()

        # 1. Owner A queries dashboard (/api/items/)
        req_a = self.factory.get('/api/items/')
        force_authenticate(req_a, user=owner_a)
        res_a = view(req_a)
        item_ids_a = [it['id'] for it in res_a.data]
        self.assertIn(item_a.id, item_ids_a)
        self.assertNotIn(item_b.id, item_ids_a)
        self.assertNotIn(item_f.id, item_ids_a)

        # 2. Owner B queries dashboard (/api/items/)
        req_b = self.factory.get('/api/items/')
        force_authenticate(req_b, user=owner_b)
        res_b = view(req_b)
        item_ids_b = [it['id'] for it in res_b.data]
        self.assertIn(item_b.id, item_ids_b)
        self.assertNotIn(item_a.id, item_ids_b)
        self.assertNotIn(item_f.id, item_ids_b)

        # 3. Finder queries dashboard (/api/items/)
        req_f = self.factory.get('/api/items/')
        force_authenticate(req_f, user=finder_a)
        res_f = view(req_f)
        item_ids_f = [it['id'] for it in res_f.data]
        self.assertIn(item_a.id, item_ids_f)
        self.assertIn(item_b.id, item_ids_f)
        self.assertIn(item_f.id, item_ids_f)

    def test_promote_item_allowed_for_lost_item_forbidden_for_found_item(self):
        """Owner can initiate promotion for Lost Item, but Found Items cannot be promoted."""
        from api.payment_views import InitiatePaymentView
        from unittest.mock import patch

        owner = User.objects.create_user(
            username='promo_owner', email='promo_owner@example.com', password='Password123!', role='owner', is_verified=True
        )
        finder = User.objects.create_user(
            username='promo_finder', email='promo_finder@example.com', password='Password123!', role='finder', is_verified=True
        )

        lost_item = Item.objects.create(
            user=owner, title="Lost MacBook", description="M2 Air", category="electronics", type="lost", status="approved"
        )
        found_item = Item.objects.create(
            user=finder, title="Found MacBook", description="M2 Air", category="electronics", type="found", status="approved"
        )

        view = InitiatePaymentView.as_view()

        # 1. Finder tries to promote Found Item -> 400 'Only lost items can be promoted.'
        req_found = self.factory.post('/api/payments/initiate/', {
            'item_id': found_item.id,
            'package': '24h',
            'provider': 'esewa'
        })
        force_authenticate(req_found, user=finder)
        res_found = view(req_found)
        self.assertEqual(res_found.status_code, 400)
        self.assertEqual(res_found.data['error'], 'Only lost items can be promoted.')

        # 2. Owner attempts to promote with Khalti -> 400 'Only eSewa is supported for item promotion.'
        req_khalti = self.factory.post('/api/payments/initiate/', {
            'item_id': lost_item.id,
            'package': '24h',
            'provider': 'khalti'
        })
        force_authenticate(req_khalti, user=owner)
        res_khalti = view(req_khalti)
        self.assertEqual(res_khalti.status_code, 400)
        self.assertEqual(res_khalti.data['error'], 'Only eSewa is supported for item promotion.')

        # 3. Owner promotes Lost Item with eSewa -> Accepted and initiated
        with patch('api.payment_views.InitiatePaymentView._initiate_esewa') as mock_esewa:
            from rest_framework.response import Response
            mock_esewa.return_value = Response({'payment_url': 'https://test.esewa.com/pay', 'pidx': 'test_pidx'})
            req_lost = self.factory.post('/api/payments/initiate/', {
                'item_id': lost_item.id,
                'package': '24h',
                'provider': 'esewa'
            })
            force_authenticate(req_lost, user=owner)
            res_lost = view(req_lost)
            self.assertEqual(res_lost.status_code, 200)


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
        # Iron found an iPhone and established contact with Thor
        self.matched_found_phone = Item.objects.create(
            user=self.finder, type='found', title='Found iPhone 13 in Park', category='phone', status='approved'
        )
        Conversation.objects.create(
            item=self.matched_found_phone, owner=self.owner, finder=self.finder
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

    def test_owner_can_view_matched_found_item_details(self):
        """Owner can retrieve details of a matched found item (HTTP 200)."""
        view = ItemDetailView.as_view()
        req = self.factory.get(f'/api/items/{self.matched_found_phone.id}/')
        force_authenticate(req, user=self.owner)
        res = view(req, pk=self.matched_found_phone.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['id'], self.matched_found_phone.id)
        self.assertEqual(res.data['title'], self.matched_found_phone.title)

    def test_owner_unmatched_found_item_forbidden(self):
        """Owner cannot retrieve details of an unmatched found item without existing association (HTTP 403)."""
        view = ItemDetailView.as_view()
        req = self.factory.get(f'/api/items/{self.unmatched_found_glasses.id}/')
        force_authenticate(req, user=self.owner)
        res = view(req, pk=self.unmatched_found_glasses.id)
        self.assertEqual(res.status_code, 403)

    def test_finder_can_view_any_approved_found_item_details(self):
        """Finder can retrieve details of any approved found item."""
        view = ItemDetailView.as_view()
        req = self.factory.get(f'/api/items/{self.unmatched_found_glasses.id}/')
        force_authenticate(req, user=self.finder)
        res = view(req, pk=self.unmatched_found_glasses.id)
        self.assertEqual(res.status_code, 200)


class OwnerFinderChatCommunicationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='owner_alice', email='alice@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='finder_bob', email='bob@example.com', password='Password123!', role='finder', is_verified=True
        )
        self.intruder = User.objects.create_user(
            username='user_intruder', email='intruder@example.com', password='Password123!', role='owner', is_verified=True
        )

        self.lost_phone = Item.objects.create(
            user=self.owner, type='lost', title='Lost iPhone', category='phone', status='approved'
        )
        self.found_phone = Item.objects.create(
            user=self.finder, type='found', title='Found iPhone', category='phone', status='approved'
        )

    def test_finder_initiates_chat_on_lost_item_and_sends_message(self):
        """Finder contacts Owner from Lost Item and sends message via 'conversation' key."""
        # 1. Finder initiates conversation
        init_view = ConversationInitView.as_view()
        req_init = self.factory.post('/api/conversations/init/', {'item_id': self.lost_phone.id})
        force_authenticate(req_init, user=self.finder)
        res_init = init_view(req_init)
        self.assertEqual(res_init.status_code, 200)
        conv_id = res_init.data['conversation_id']

        # 2. Finder sends message using Android ChatMessage JSON schema: {"conversation": id, "message": "..."}
        chat_view = ChatListView.as_view()
        req_send = self.factory.post('/api/chat/', {
            'conversation': conv_id,
            'message': 'Hello, I think I found your iPhone!'
        })
        force_authenticate(req_send, user=self.finder)
        res_send = chat_view(req_send)
        self.assertEqual(res_send.status_code, 201)
        self.assertEqual(res_send.data['conversation'], conv_id)
        self.assertEqual(res_send.data['sender_name'], 'finder_bob')

        # 3. Verify message is stored in DB
        msg = ChatMessage.objects.get(id=res_send.data['id'])
        self.assertEqual(msg.message, 'Hello, I think I found your iPhone!')
        self.assertEqual(msg.sender, self.finder)
        self.assertEqual(msg.conversation_id, conv_id)

        # 4. Owner reads conversation messages
        req_get = self.factory.get(f'/api/chat/?conversation_id={conv_id}')
        force_authenticate(req_get, user=self.owner)
        res_get = chat_view(req_get)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.data), 1)
        self.assertEqual(res_get.data[0]['message'], 'Hello, I think I found your iPhone!')

        # 5. Owner replies
        req_reply = self.factory.post('/api/chat/', {
            'conversation': conv_id,
            'message': 'Thank you! Where can we meet?'
        })
        force_authenticate(req_reply, user=self.owner)
        res_reply = chat_view(req_reply)
        self.assertEqual(res_reply.status_code, 201)

        # 6. Finder retrieves both messages
        req_get_finder = self.factory.get(f'/api/chat/?conversation_id={conv_id}')
        force_authenticate(req_get_finder, user=self.finder)
        res_get_finder = chat_view(req_get_finder)
        self.assertEqual(len(res_get_finder.data), 2)

    def test_owner_initiates_chat_on_found_item_and_sends_message(self):
        """Owner contacts Finder from Found Item and sends message via 'conversation' key."""
        init_view = ConversationInitView.as_view()
        req_init = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_init, user=self.owner)
        res_init = init_view(req_init)
        self.assertEqual(res_init.status_code, 200)
        conv_id = res_init.data['conversation_id']

        chat_view = ChatListView.as_view()
        req_send = self.factory.post('/api/chat/', {
            'conversation': conv_id,
            'message': 'Hi! Is this iPhone still with you?'
        })
        force_authenticate(req_send, user=self.owner)
        res_send = chat_view(req_send)
        self.assertEqual(res_send.status_code, 201)

        # Verify Notification created for Finder
        self.assertTrue(Notification.objects.filter(user=self.finder, type='message').exists())

    def test_unauthorized_user_forbidden_from_chat(self):
        """Intruder cannot read or send messages in a conversation they do not belong to."""
        conv = Conversation.objects.create(item=self.lost_phone, owner=self.owner, finder=self.finder)

        chat_view = ChatListView.as_view()
        # Attempt to read
        req_get = self.factory.get(f'/api/chat/?conversation_id={conv.id}')
        force_authenticate(req_get, user=self.intruder)
        res_get = chat_view(req_get)
        self.assertEqual(res_get.status_code, 403)

        # Attempt to post
        req_send = self.factory.post('/api/chat/', {
            'conversation': conv.id,
            'message': 'I am spying on your conversation!'
        })
        force_authenticate(req_send, user=self.intruder)
        res_send = chat_view(req_send)
        self.assertEqual(res_send.status_code, 403)

    def test_sending_multiple_messages_does_not_create_or_duplicate_found_items(self):
        """Sending messages must NOT create new Found Items in DB or duplicate items in dashboard."""
        initial_found_count = Item.objects.filter(type='found').count()

        # 1. Initialize conversation
        init_view = ConversationInitView.as_view()
        req_init = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_init, user=self.owner)
        res_init = init_view(req_init)
        conv_id = res_init.data['conversation_id']

        # 2. Check initial Owner dashboard found items
        list_view = ItemListCreateView.as_view()
        req_list = self.factory.get('/api/items/?type=found')
        force_authenticate(req_list, user=self.owner)
        res_list0 = list_view(req_list)
        self.assertEqual(len(res_list0.data), 1)

        # 3. Send 5 messages (Owner -> Finder and Finder -> Owner)
        chat_view = ChatListView.as_view()
        for i in range(5):
            sender = self.owner if i % 2 == 0 else self.finder
            req_msg = self.factory.post('/api/chat/', {
                'conversation': conv_id,
                'message': f'Message #{i + 1}: K xa?'
            })
            force_authenticate(req_msg, user=sender)
            res_msg = chat_view(req_msg)
            self.assertEqual(res_msg.status_code, 201)

        # 4. Verify Database Found Item count is UNCHANGED
        after_found_count = Item.objects.filter(type='found').count()
        self.assertEqual(after_found_count, initial_found_count)

        # 5. Verify Owner dashboard STILL has exactly 1 Found Item (no duplicates)
        res_list_after = list_view(req_list)
        self.assertEqual(len(res_list_after.data), 1)
        self.assertEqual(res_list_after.data[0]['id'], self.found_phone.id)

        # 6. Verify All tab also has no duplicates
        req_all = self.factory.get('/api/items/')
        force_authenticate(req_all, user=self.owner)
        res_all = list_view(req_all)
        found_in_all = [it for it in res_all.data if it['id'] == self.found_phone.id]
        self.assertEqual(len(found_in_all), 1)

    def test_opening_chat_multiple_times_does_not_create_found_items(self):
        """Opening / initializing chat repeatedly must NOT create duplicate conversations or Found Items."""
        initial_found_count = Item.objects.filter(type='found').count()
        initial_conv_count = Conversation.objects.count()

        init_view = ConversationInitView.as_view()
        for _ in range(5):
            req_init = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
            force_authenticate(req_init, user=self.owner)
            res_init = init_view(req_init)
            self.assertEqual(res_init.status_code, 200)

        self.assertEqual(Item.objects.filter(type='found').count(), initial_found_count)
        self.assertEqual(Conversation.objects.count(), initial_conv_count + 1)

    def test_owner_and_finder_share_same_conversation_across_lost_and_found_items(self):
        """
        Owner contacting Finder from Found Item and Finder contacting Owner from Lost Item
        must resolve to the SAME canonical conversation and preserve complete message history.
        """
        init_view = ConversationInitView.as_view()
        chat_view = ChatListView.as_view()

        # Step 1: Owner contacts Finder on Found Item -> sends "Hello"
        req_init1 = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_init1, user=self.owner)
        res_init1 = init_view(req_init1)
        self.assertEqual(res_init1.status_code, 200)
        conv_id1 = res_init1.data['conversation_id']

        req_send1 = self.factory.post('/api/chat/', {'conversation': conv_id1, 'message': 'Hello'})
        force_authenticate(req_send1, user=self.owner)
        res_send1 = chat_view(req_send1)
        self.assertEqual(res_send1.status_code, 201)

        # Step 2: Finder contacts Owner on Lost Item -> must resolve to the SAME conversation
        req_init2 = self.factory.post('/api/conversations/init/', {'item_id': self.lost_phone.id})
        force_authenticate(req_init2, user=self.finder)
        res_init2 = init_view(req_init2)
        self.assertEqual(res_init2.status_code, 200)
        conv_id2 = res_init2.data['conversation_id']
        self.assertEqual(conv_id1, conv_id2, "Owner and Finder must resolve to the same canonical conversation ID")

        # Step 3: Finder retrieves chat history and sees "Hello"
        req_get1 = self.factory.get(f'/api/chat/?conversation_id={conv_id2}')
        force_authenticate(req_get1, user=self.finder)
        res_get1 = chat_view(req_get1)
        self.assertEqual(res_get1.status_code, 200)
        self.assertEqual(len(res_get1.data), 1)
        self.assertEqual(res_get1.data[0]['message'], 'Hello')
        self.assertEqual(res_get1.data[0]['sender_name'], 'owner_alice')

        # Step 4: Finder replies "Hi, I found your item."
        req_send2 = self.factory.post('/api/chat/', {'conversation': conv_id2, 'message': 'Hi, I found your item.'})
        force_authenticate(req_send2, user=self.finder)
        res_send2 = chat_view(req_send2)
        self.assertEqual(res_send2.status_code, 201)

        # Step 5: Owner reopens chat from Found Item and sees both messages
        req_init3 = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_init3, user=self.owner)
        res_init3 = init_view(req_init3)
        self.assertEqual(res_init3.data['conversation_id'], conv_id1)

        req_get2 = self.factory.get(f'/api/chat/?conversation_id={conv_id1}')
        force_authenticate(req_get2, user=self.owner)
        res_get2 = chat_view(req_get2)
        self.assertEqual(len(res_get2.data), 2)
        self.assertEqual(res_get2.data[0]['message'], 'Hello')
        self.assertEqual(res_get2.data[1]['message'], 'Hi, I found your item.')

        # Step 6: Owner sends "Where can we meet?"
        req_send3 = self.factory.post('/api/chat/', {'conversation': conv_id1, 'message': 'Where can we meet?'})
        force_authenticate(req_send3, user=self.owner)
        res_send3 = chat_view(req_send3)
        self.assertEqual(res_send3.status_code, 201)

        # Step 7: Finder reopens chat from Lost Item and sees all 3 messages chronologically
        req_get3 = self.factory.get(f'/api/chat/?conversation_id={conv_id2}')
        force_authenticate(req_get3, user=self.finder)
        res_get3 = chat_view(req_get3)
        self.assertEqual(len(res_get3.data), 3)
        self.assertEqual(res_get3.data[0]['message'], 'Hello')
        self.assertEqual(res_get3.data[1]['message'], 'Hi, I found your item.')
        self.assertEqual(res_get3.data[2]['message'], 'Where can we meet?')

    def test_chat_notification_includes_conversation_id_and_resolves_exact_chat(self):
        """
        When a chat message notification is created, NotificationSerializer must include
        conversation_id, and clicking 'View Conversation' on item details resolves that exact conversation.
        """
        init_view = ConversationInitView.as_view()
        chat_view = ChatListView.as_view()
        notif_view = NotificationListView.as_view()

        # 1. Owner contacts Finder on Found Phone -> sends "Hi!"
        req_init = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_init, user=self.owner)
        res_init = init_view(req_init)
        conv_id = res_init.data['conversation_id']

        req_send = self.factory.post('/api/chat/', {'conversation': conv_id, 'message': 'Hi!'})
        force_authenticate(req_send, user=self.owner)
        res_send = chat_view(req_send)
        self.assertEqual(res_send.status_code, 201)

        # 2. Finder fetches notifications
        req_notif = self.factory.get('/api/notifications/')
        force_authenticate(req_notif, user=self.finder)
        res_notif = notif_view(req_notif)
        self.assertEqual(res_notif.status_code, 200)
        self.assertTrue(len(res_notif.data) >= 1)

        # Verify notification payload contains related_item and matching conversation_id
        msg_notif = [n for n in res_notif.data if n['type'] == 'message'][0]
        self.assertEqual(msg_notif['related_item'], self.found_phone.id)
        self.assertEqual(msg_notif['conversation_id'], conv_id)

        # 3. Finder resolves conversation on the found item -> returns exact conv_id
        req_finder_init = self.factory.post('/api/conversations/init/', {'item_id': self.found_phone.id})
        force_authenticate(req_finder_init, user=self.finder)
        res_finder_init = init_view(req_finder_init)
        self.assertEqual(res_finder_init.status_code, 200)
        self.assertEqual(res_finder_init.data['conversation_id'], conv_id)

        # 4. Finder loads messages for that conversation -> sees "Hi!"
        req_get = self.factory.get(f'/api/chat/?conversation_id={conv_id}')
        force_authenticate(req_get, user=self.finder)
        res_get = chat_view(req_get)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.data), 1)
        self.assertEqual(res_get.data[0]['message'], 'Hi!')


from django.core.files.uploadedfile import SimpleUploadedFile

class OwnerReportItemImageAndMatchingIndependenceTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.finder = User.objects.create_user(
            username='finder_user', email='finder@example.com', password='Password123!', role='finder', is_verified=True
        )
        self.owner_a = User.objects.create_user(
            username='owner_a', email='ownera@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.owner_b = User.objects.create_user(
            username='owner_b', email='ownerb@example.com', password='Password123!', role='owner', is_verified=True
        )

    def test_new_owner_reports_laptop_when_found_laptop_exists(self):
        """
        When Finder has reported a Found Laptop with Photo A (approved),
        and Owner B reports a Lost Laptop with Photo B:
        - Owner B's item is created with its own record and Photo B
        - Owner B's item remains 'lost' with status 'pending' (NOT converted to found)
        - Owner B's GET /api/items/ returns Owner B's Lost Laptop (Photo B)
        - Finder's Found Laptop (Photo A) remains a completely separate record
        """
        # 1. Finder reports Found Laptop with Photo A (status approved)
        photo_a = SimpleUploadedFile("laptop_a.jpg", b"photo_a_bytes", content_type="image/jpeg")
        found_item = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Silver Laptop',
            description='Found Dell laptop near library',
            category='electronics',
            status='approved',
            image=photo_a
        )

        # 2. Owner B reports Lost Laptop with Photo B
        photo_b = SimpleUploadedFile("laptop_b.jpg", b"photo_b_bytes", content_type="image/jpeg")
        view = ItemListCreateView.as_view()
        req_create = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost ThinkPad Laptop',
            'description': 'Black ThinkPad lost in cafe',
            'category': 'electronics',
            'location': 'Central Cafe',
            'images': [photo_b]
        }, format='multipart')
        force_authenticate(req_create, user=self.owner_b)
        res_create = view(req_create)

        self.assertEqual(res_create.status_code, 201)
        owner_b_item_id = res_create.data['id']
        self.assertNotEqual(owner_b_item_id, found_item.id)
        self.assertEqual(res_create.data['type'], 'lost')
        self.assertEqual(res_create.data['status'], 'pending')
        self.assertTrue('laptop_b' in res_create.data['image_url'] or (res_create.data['images'] and 'laptop_b' in res_create.data['images'][0]['image_url']))

        # 3. Before approval: Owner B fetches public items (Home screen) -> pending item is NOT visible
        req_list_before = self.factory.get('/api/items/')
        force_authenticate(req_list_before, user=self.owner_b)
        res_list_before = view(req_list_before)
        self.assertEqual(res_list_before.status_code, 200)
        item_ids_before = [item['id'] for item in res_list_before.data]
        self.assertNotIn(owner_b_item_id, item_ids_before)

        # 4. Owner B can see their pending item in private My Reports view
        my_reports_view = MyReportsView.as_view()
        req_my_reports = self.factory.get('/api/profile/items/?filter=lost')
        force_authenticate(req_my_reports, user=self.owner_b)
        res_my_reports = my_reports_view(req_my_reports)
        self.assertEqual(res_my_reports.status_code, 200)
        my_report_ids = [item['id'] for item in res_my_reports.data]
        self.assertIn(owner_b_item_id, my_report_ids)

        # 5. Admin approves Owner B's item
        Item.objects.filter(id=owner_b_item_id).update(status='approved')

        # 6. After approval: Owner B fetches items (Home screen) -> approved item is now visible
        req_list = self.factory.get('/api/items/')
        force_authenticate(req_list, user=self.owner_b)
        res_list = view(req_list)
        self.assertEqual(res_list.status_code, 200)

        item_ids = [item['id'] for item in res_list.data]
        self.assertIn(owner_b_item_id, item_ids)

        owner_b_item_data = next(item for item in res_list.data if item['id'] == owner_b_item_id)
        self.assertEqual(owner_b_item_data['type'], 'lost')
        self.assertEqual(owner_b_item_data['user'], self.owner_b.id)
        self.assertTrue('laptop_b' in owner_b_item_data['image_url'] or (owner_b_item_data['images'] and 'laptop_b' in owner_b_item_data['images'][0]['image_url']))

        # Found item remains separate
        found_item_db = Item.objects.get(id=found_item.id)
        self.assertEqual(found_item_db.type, 'found')
        self.assertEqual(found_item_db.user, self.finder)

    def test_multiple_owners_reporting_same_category_retain_separate_photos(self):
        """
        Owner A reports Wallet + Photo A.
        Owner B reports Wallet + Photo B.
        Both retain distinct records, images, and lost status.
        """
        view = ItemListCreateView.as_view()

        photo_a = SimpleUploadedFile("wallet_a.jpg", b"wallet_a_bytes", content_type="image/jpeg")
        req_a = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Brown Leather Wallet',
            'description': 'Lost with credit cards',
            'category': 'wallet',
            'location': 'Bus Stand',
            'images': [photo_a]
        }, format='multipart')
        force_authenticate(req_a, user=self.owner_a)
        res_a = view(req_a)
        self.assertEqual(res_a.status_code, 201)

        photo_b = SimpleUploadedFile("wallet_b.jpg", b"wallet_b_bytes", content_type="image/jpeg")
        req_b = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Black Slim Wallet',
            'description': 'Lost near food court',
            'category': 'wallet',
            'location': 'Mall',
            'images': [photo_b]
        }, format='multipart')
        force_authenticate(req_b, user=self.owner_b)
        res_b = view(req_b)
        self.assertEqual(res_b.status_code, 201)

        self.assertNotEqual(res_a.data['id'], res_b.data['id'])
        self.assertTrue('wallet_a' in (res_a.data['image_url'] or res_a.data['images'][0]['image_url']))
        self.assertTrue('wallet_b' in (res_b.data['image_url'] or res_b.data['images'][0]['image_url']))


class LostItemAdminApprovalWorkflowTests(TestCase):
    """
    Complete end-to-end verification of the Findora Lost Item approval workflow:
    1. Owner submits new Lost Item -> saved as Pending
    2. Pending item does NOT appear in public dashboards / list APIs / search
    3. Finder cannot see Pending item
    4. Admin can see Pending item in Admin item list
    5. Admin changes Pending -> Approved
    6. Approved item appears normally in dashboards / lists / matching
    7. Rejected item remains hidden from public lists
    8. Existing approved items remain visible
    9. Owner's private My Reports view preserves visibility of their own pending reports
    10. Detail view permissions enforce privacy of pending items for non-creators
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='test_owner', email='owner@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.other_owner = User.objects.create_user(
            username='other_owner', email='other_owner@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='test_finder', email='finder@example.com', password='Password123!', role='finder', is_verified=True
        )
        self.admin_user = User.objects.create_user(
            username='test_admin', email='admin@example.com', password='Password123!', role='admin', is_staff=True, is_superuser=True, is_verified=True
        )

    def test_owner_submits_lost_item_saved_as_pending(self):
        """Owner reports a lost item -> saved in database with status='pending'."""
        view = ItemListCreateView.as_view()
        req = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost Sony Headphones',
            'description': 'Black WH-1000XM4 lost on bus',
            'category': 'electronics',
            'location': 'Bus No. 10',
            'reward': '500.00'
        })
        force_authenticate(req, user=self.owner)
        res = view(req)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['status'], 'pending')

        item = Item.objects.get(id=res.data['id'])
        self.assertEqual(item.status, 'pending')
        self.assertEqual(item.user, self.owner)

    def test_pending_lost_item_hidden_from_public_dashboards_and_lists(self):
        """
        Pending lost item must NOT appear in:
        - Owner's public dashboard (/api/items/)
        - Finder's public dashboard (/api/items/)
        - Search results (/api/items/?search=Sony)
        - Filtered category results (/api/items/?category=electronics)
        """
        pending_item = Item.objects.create(
            user=self.owner, title='Lost Sony Headphones', description='Black WH-1000XM4',
            category='electronics', type='lost', status='pending', reward=500.00
        )
        approved_item = Item.objects.create(
            user=self.owner, title='Lost Apple Watch', description='Series 8',
            category='electronics', type='lost', status='approved'
        )

        view = ItemListCreateView.as_view()

        # 1. Owner's view of /api/items/ (dashboard)
        req_owner = self.factory.get('/api/items/')
        force_authenticate(req_owner, user=self.owner)
        res_owner = view(req_owner)
        ids_owner = [it['id'] for it in res_owner.data]
        self.assertNotIn(pending_item.id, ids_owner)
        self.assertIn(approved_item.id, ids_owner)

        # 2. Finder's view of /api/items/
        req_finder = self.factory.get('/api/items/')
        force_authenticate(req_finder, user=self.finder)
        res_finder = view(req_finder)
        ids_finder = [it['id'] for it in res_finder.data]
        self.assertNotIn(pending_item.id, ids_finder)
        self.assertIn(approved_item.id, ids_finder)

        # 3. Search query
        req_search = self.factory.get('/api/items/?search=Sony')
        force_authenticate(req_search, user=self.owner)
        res_search = view(req_search)
        ids_search = [it['id'] for it in res_search.data]
        self.assertNotIn(pending_item.id, ids_search)

    def test_owner_private_my_reports_view_shows_pending_item(self):
        """Owner can see their own pending item in private My Reports view with 'pending' status."""
        pending_item = Item.objects.create(
            user=self.owner, title='Lost Sony Headphones', description='Black WH-1000XM4',
            category='electronics', type='lost', status='pending'
        )

        view = MyReportsView.as_view()
        req = self.factory.get('/api/profile/items/?filter=lost')
        force_authenticate(req, user=self.owner)
        res = view(req)
        self.assertEqual(res.status_code, 200)

        ids = [it['id'] for it in res.data]
        self.assertIn(pending_item.id, ids)
        item_data = next(it for it in res.data if it['id'] == pending_item.id)
        self.assertEqual(item_data['status'], 'pending')

    def test_pending_item_not_matched_for_discovery_until_approved(self):
        """Pending lost item must NOT generate discovery matches for found items until approved."""
        found_item = Item.objects.create(
            user=self.finder, title='Found Sony Headphones WH-1000XM4', description='Found on bus seat',
            category='electronics', type='found', status='approved'
        )

        # Owner has only a pending lost item and an established match notification
        pending_item = Item.objects.create(
            user=self.owner, title='Lost Sony Headphones', description='Black WH-1000XM4',
            category='electronics', type='lost', status='pending'
        )
        Notification.objects.create(
            user=self.owner, related_item=found_item, type='match', message='Possible match found!'
        )

        view = ItemListCreateView.as_view()

        # Before approval: Owner does NOT see their own pending item on the dashboard
        req1 = self.factory.get('/api/items/')
        force_authenticate(req1, user=self.owner)
        res1 = view(req1)
        ids1 = [it['id'] for it in res1.data]
        self.assertNotIn(pending_item.id, ids1)

        # Admin approves the lost item
        pending_item.status = 'approved'
        pending_item.save()

        # After approval: Owner sees both their approved lost item and the matched found item
        req2 = self.factory.get('/api/items/')
        force_authenticate(req2, user=self.owner)
        res2 = view(req2)
        ids2 = [it['id'] for it in res2.data]
        self.assertIn(found_item.id, ids2)
        self.assertIn(pending_item.id, ids2)

    def test_admin_review_and_approval_workflow(self):
        """
        Admin sees pending items in Admin API.
        Admin verifies/approves pending item.
        Item status updates to 'approved', notification is created, and item becomes visible.
        """
        pending_item = Item.objects.create(
            user=self.owner, title='Lost MacBook Air M2', description='Space grey laptop',
            category='electronics', type='lost', status='pending'
        )

        # 1. Admin lists pending items
        admin_list_view = AdminItemListView.as_view()
        req_list = self.factory.get('/api/admin/items/?status=pending')
        force_authenticate(req_list, user=self.admin_user)
        res_list = admin_list_view(req_list)
        self.assertEqual(res_list.status_code, 200)
        admin_ids = [it['id'] for it in res_list.data]
        self.assertIn(pending_item.id, admin_ids)

        # 2. Non-admin cannot access admin verify endpoint
        verify_view = AdminVerifyItemView.as_view()
        req_forbidden = self.factory.post(f'/api/admin/items/{pending_item.id}/verify/', {'action': 'approve'})
        force_authenticate(req_forbidden, user=self.owner)
        res_forbidden = verify_view(req_forbidden, pk=pending_item.id)
        self.assertEqual(res_forbidden.status_code, 403)

        # 3. Admin approves the item
        req_approve = self.factory.post(f'/api/admin/items/{pending_item.id}/verify/', {'action': 'approve'})
        force_authenticate(req_approve, user=self.admin_user)
        res_approve = verify_view(req_approve, pk=pending_item.id)
        self.assertEqual(res_approve.status_code, 200)
        self.assertEqual(res_approve.data['item']['status'], 'approved')

        # 4. Item status is now 'approved' in database
        pending_item.refresh_from_db()
        self.assertEqual(pending_item.status, 'approved')

        # 5. Notification was sent to owner
        notif = Notification.objects.filter(user=self.owner, type='approved', related_item=pending_item).first()
        self.assertIsNotNone(notif)
        self.assertIn('approved and is now public', notif.message)

        # 6. Approved item now visible on dashboards
        items_view = ItemListCreateView.as_view()
        req_owner = self.factory.get('/api/items/')
        force_authenticate(req_owner, user=self.owner)
        res_owner = items_view(req_owner)
        self.assertIn(pending_item.id, [it['id'] for it in res_owner.data])

        req_finder = self.factory.get('/api/items/')
        force_authenticate(req_finder, user=self.finder)
        res_finder = items_view(req_finder)
        self.assertIn(pending_item.id, [it['id'] for it in res_finder.data])

    def test_admin_reject_workflow_keeps_item_hidden(self):
        """Admin rejecting an item sets status='rejected' and it remains hidden from public feeds."""
        pending_item = Item.objects.create(
            user=self.owner, title='Spam / Inappropriate Item', description='Bad content',
            category='other', type='lost', status='pending'
        )

        verify_view = AdminVerifyItemView.as_view()
        req_reject = self.factory.post(f'/api/admin/items/{pending_item.id}/verify/', {'action': 'reject'})
        force_authenticate(req_reject, user=self.admin_user)
        res_reject = verify_view(req_reject, pk=pending_item.id)
        self.assertEqual(res_reject.status_code, 200)

        pending_item.refresh_from_db()
        self.assertEqual(pending_item.status, 'rejected')

        # Ensure not visible on owner dashboard or finder dashboard
        items_view = ItemListCreateView.as_view()
        req_owner = self.factory.get('/api/items/')
        force_authenticate(req_owner, user=self.owner)
        res_owner = items_view(req_owner)
        self.assertNotIn(pending_item.id, [it['id'] for it in res_owner.data])

        req_finder = self.factory.get('/api/items/')
        force_authenticate(req_finder, user=self.finder)
        res_finder = items_view(req_finder)
        self.assertNotIn(pending_item.id, [it['id'] for it in res_finder.data])

    def test_item_detail_view_permissions_for_pending_items(self):
        """
        Owner can view their own pending item detail.
        Admin can view any pending item detail.
        Other users (Finders / Other Owners) are forbidden (403) from viewing pending items.
        """
        pending_item = Item.objects.create(
            user=self.owner, title='Lost Citizen Watch', description='Silver watch',
            category='other', type='lost', status='pending'
        )

        detail_view = ItemDetailView.as_view()

        # 1. Owner views own pending item -> 200 OK
        req_owner = self.factory.get(f'/api/items/{pending_item.id}/')
        force_authenticate(req_owner, user=self.owner)
        res_owner = detail_view(req_owner, pk=pending_item.id)
        self.assertEqual(res_owner.status_code, 200)
        self.assertEqual(res_owner.data['status'], 'pending')

        # 2. Admin views pending item -> 200 OK
        req_admin = self.factory.get(f'/api/items/{pending_item.id}/')
        force_authenticate(req_admin, user=self.admin_user)
        res_admin = detail_view(req_admin, pk=pending_item.id)
        self.assertEqual(res_admin.status_code, 200)

        # 3. Finder attempts to view pending lost item -> 403 Forbidden
        req_finder = self.factory.get(f'/api/items/{pending_item.id}/')
        force_authenticate(req_finder, user=self.finder)
        res_finder = detail_view(req_finder, pk=pending_item.id)
        self.assertEqual(res_finder.status_code, 403)

        # 4. Other Owner attempts to view pending lost item -> 403 Forbidden
        req_other = self.factory.get(f'/api/items/{pending_item.id}/')
        force_authenticate(req_other, user=self.other_owner)
        res_other = detail_view(req_other, pk=pending_item.id)
        self.assertEqual(res_other.status_code, 403)

    def test_finder_submits_found_item_saved_as_pending_and_approval_workflow(self):
        """
        Finder reports a found item:
        1. Saved in database with status='pending'.
        2. Hidden from Finder public dashboard, Owner dashboard, public search, matching.
        3. Visible in Finder's private My Reports view.
        4. Detail view forbidden for Owner while pending.
        5. Admin approves -> item becomes status='approved' and visible to Finder and matched Owner.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        photo = SimpleUploadedFile("found_wallet.jpg", b"fake_wallet_bytes", content_type="image/jpeg")

        # 1. Finder reports Found item
        items_view = ItemListCreateView.as_view()
        req_create = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Black Leather Wallet',
            'description': 'Found near canteen table',
            'category': 'wallet',
            'location': 'Campus Canteen',
            'images': [photo]
        }, format='multipart')
        force_authenticate(req_create, user=self.finder)
        res_create = items_view(req_create)
        self.assertEqual(res_create.status_code, 201)
        self.assertEqual(res_create.data['status'], 'pending')
        found_id = res_create.data['id']

        found_item = Item.objects.get(id=found_id)
        self.assertEqual(found_item.status, 'pending')

        # Owner has an approved lost wallet report
        approved_lost = Item.objects.create(
            user=self.owner, title='Lost Black Leather Wallet', description='Lost wallet in canteen',
            category='wallet', type='lost', status='approved'
        )

        # 2. Before approval: Finder public dashboard (/api/items/) -> pending found item NOT visible
        req_f = self.factory.get('/api/items/')
        force_authenticate(req_f, user=self.finder)
        res_f = items_view(req_f)
        self.assertNotIn(found_id, [it['id'] for it in res_f.data])

        # Before approval: Owner dashboard (/api/items/) -> pending found item NOT visible
        req_o = self.factory.get('/api/items/')
        force_authenticate(req_o, user=self.owner)
        res_o = items_view(req_o)
        self.assertNotIn(found_id, [it['id'] for it in res_o.data])

        # Before approval: Search (/api/items/?search=wallet) -> pending found item NOT visible
        req_s = self.factory.get('/api/items/?search=wallet')
        force_authenticate(req_s, user=self.finder)
        res_s = items_view(req_s)
        self.assertNotIn(found_id, [it['id'] for it in res_s.data])

        # 3. Finder private My Reports (/api/profile/items/?filter=found) -> pending found item IS visible
        my_reports_view = MyReportsView.as_view()
        req_rep = self.factory.get('/api/profile/items/?filter=found')
        force_authenticate(req_rep, user=self.finder)
        res_rep = my_reports_view(req_rep)
        self.assertIn(found_id, [it['id'] for it in res_rep.data])

        # 4. Detail view permissions: Finder can view own pending found item, Owner is forbidden
        detail_view = ItemDetailView.as_view()
        req_det_f = self.factory.get(f'/api/items/{found_id}/')
        force_authenticate(req_det_f, user=self.finder)
        res_det_f = detail_view(req_det_f, pk=found_id)
        self.assertEqual(res_det_f.status_code, 200)

        req_det_o = self.factory.get(f'/api/items/{found_id}/')
        force_authenticate(req_det_o, user=self.owner)
        res_det_o = detail_view(req_det_o, pk=found_id)
        self.assertEqual(res_det_o.status_code, 403)

        # 5. Admin approves the found item
        verify_view = AdminVerifyItemView.as_view()
        req_app = self.factory.post(f'/api/admin/items/{found_id}/verify/', {'action': 'approve'})
        force_authenticate(req_app, user=self.admin_user)
        res_app = verify_view(req_app, pk=found_id)
        self.assertEqual(res_app.status_code, 200)

        found_item.refresh_from_db()
        self.assertEqual(found_item.status, 'approved')

        # 6. After approval: Found item is visible on Finder dashboard
        res_f_after = items_view(req_f)
        self.assertIn(found_id, [it['id'] for it in res_f_after.data])

        # Owner does NOT automatically receive the found item just because category is 'wallet'
        res_o_after = items_view(req_o)
        self.assertNotIn(found_id, [it['id'] for it in res_o_after.data])

        # 7. When a conversation/match is established between Finder and Owner, Found item becomes visible to Owner
        Conversation.objects.create(item=found_item, owner=self.owner, finder=self.finder)
        res_o_matched = items_view(req_o)
        self.assertIn(found_id, [it['id'] for it in res_o_matched.data])


class CrossUserFoundItemIndependenceTests(TestCase):
    """
    Verifies that a Found item reported by Finder1 and approved by Admin
    does NOT cross-contaminate or automatically appear on the dashboard of Owner2
    who reports a new Lost item in the same category or with similar keywords.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner1 = User.objects.create_user(
            username='owner_one', email='owner1@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.owner2 = User.objects.create_user(
            username='owner_two', email='owner2@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder1 = User.objects.create_user(
            username='finder_one', email='finder1@example.com', password='Password123!', role='finder', is_verified=True
        )
        self.admin = User.objects.create_user(
            username='admin_boss', email='admin_boss@example.com', password='Password123!', role='admin', is_staff=True, is_superuser=True, is_verified=True
        )

    def test_owner2_lost_laptop_does_not_see_finder1_found_laptop_in_same_category(self):
        """
        1. Owner1 reports Lost Laptop (Electronics) -> Approved.
        2. Finder1 reports Found Laptop (Electronics) -> Approved.
        3. Owner1 and Finder1 establish conversation -> Owner1 sees Finder1's Found Laptop.
        4. Owner2 reports another Lost Laptop (Electronics) -> Approved.
        5. Owner2's dashboard shows ONLY Owner2's Lost Laptop and NOT Finder1's Found Laptop.
        """
        items_view = ItemListCreateView.as_view()

        # Step 1: Owner1 Lost Laptop
        lost1 = Item.objects.create(
            user=self.owner1, type='lost', title='Lost Dell XPS Laptop', category='electronics', status='approved'
        )

        # Step 2: Finder1 Found Laptop
        found1 = Item.objects.create(
            user=self.finder1, type='found', title='Found Dell XPS Laptop', category='electronics', status='approved'
        )

        # Step 3: Owner1 connects with Finder1
        Conversation.objects.create(item=found1, owner=self.owner1, finder=self.finder1)

        # Owner1 dashboard: sees own Lost Laptop and matched Found Laptop
        req_o1 = self.factory.get('/api/items/')
        force_authenticate(req_o1, user=self.owner1)
        res_o1 = items_view(req_o1)
        o1_ids = [it['id'] for it in res_o1.data]
        self.assertIn(lost1.id, o1_ids)
        self.assertIn(found1.id, o1_ids)

        # Step 4: Owner2 reports another Lost Laptop (Category: Electronics)
        lost2 = Item.objects.create(
            user=self.owner2, type='lost', title='Lost Lenovo ThinkPad Laptop', category='electronics', status='approved'
        )

        # Step 5: Owner2 dashboard: shows ONLY Owner2's Lost Laptop, NOT Finder1's Found Laptop
        req_o2 = self.factory.get('/api/items/')
        force_authenticate(req_o2, user=self.owner2)
        res_o2 = items_view(req_o2)
        o2_ids = [it['id'] for it in res_o2.data]
        self.assertIn(lost2.id, o2_ids)
        self.assertNotIn(found1.id, o2_ids)
        self.assertNotIn(lost1.id, o2_ids)

        # Finder1 dashboard: sees all approved lost and found items
        req_f1 = self.factory.get('/api/items/')
        force_authenticate(req_f1, user=self.finder1)
        res_f1 = items_view(req_f1)
        f1_ids = [it['id'] for it in res_f1.data]
        self.assertIn(lost1.id, f1_ids)
        self.assertIn(found1.id, f1_ids)
        self.assertIn(lost2.id, f1_ids)

    def test_cross_category_and_multi_owner_isolation(self):
        """
        Tests across multiple categories (Wallet, Phone, Keys) ensuring no cross-contamination.
        """
        items_view = ItemListCreateView.as_view()

        # Phone category
        lost_phone_o1 = Item.objects.create(
            user=self.owner1, type='lost', title='Lost iPhone 14', category='phone', status='approved'
        )
        found_phone_f1 = Item.objects.create(
            user=self.finder1, type='found', title='Found iPhone 14', category='phone', status='approved'
        )
        Notification.objects.create(user=self.owner1, related_item=found_phone_f1, type='match')

        # Owner2 lost phone in same category
        lost_phone_o2 = Item.objects.create(
            user=self.owner2, type='lost', title='Lost Samsung Phone', category='phone', status='approved'
        )

        req_o2 = self.factory.get('/api/items/')
        force_authenticate(req_o2, user=self.owner2)
        res_o2 = items_view(req_o2)
        o2_ids = [it['id'] for it in res_o2.data]

        self.assertIn(lost_phone_o2.id, o2_ids)
        self.assertNotIn(found_phone_f1.id, o2_ids)
        self.assertNotIn(lost_phone_o1.id, o2_ids)


class ItemAdminCleanOwnerItemChangePageTests(TestCase):
    """
    Tests that the ItemAdmin change interface for an Owner-reported item
    displays ONLY 'Lost Reports' and cleanly omits 'Found Reports', 'Successful Returns',
    'Reputation', and 'Points'.
    """

    def setUp(self):
        from django.contrib.admin.sites import AdminSite
        from api.admin import ItemAdmin
        from api.models import ItemImage

        self.site = AdminSite()
        self.item_admin = ItemAdmin(Item, self.site)

        self.owner = User.objects.create_user(
            username='owner_user', email='owner_u@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='finder_user', email='finder_u@example.com', password='Password123!', role='finder', is_verified=True
        )

        self.lost_item = Item.objects.create(
            user=self.owner, type='lost', title='Lost Apple Watch', category='electronics', status='approved', reward=1000.00
        )
        self.found_item = Item.objects.create(
            user=self.finder, type='found', title='Found Watch', category='electronics', status='approved'
        )

        self.admin_user = User.objects.create_superuser(
            username='super_admin', email='super@example.com', password='Password123!'
        )

    def test_owner_reported_item_shows_only_lost_reports(self):
        """Owner-reported item history display must keep Lost Reports and remove Found Reports, Returns, Reputation, Points."""
        history_html = self.item_admin.reporter_history_display(self.lost_item)

        # KEEP
        self.assertIn('Lost Reports', history_html)

        # REMOVE
        self.assertNotIn('Found Reports', history_html)
        self.assertNotIn('Successful Returns', history_html)
        self.assertNotIn('Reputation', history_html)
        self.assertNotIn('Points', history_html)

    def test_finder_reported_item_removes_lost_reports_and_keeps_finder_metrics(self):
        """Finder-reported item history display removes Lost Reports while preserving Finder metrics."""
        history_html = self.item_admin.reporter_history_display(self.found_item)

        # REMOVE
        self.assertNotIn('Lost Reports', history_html)

        # KEEP
        self.assertIn('Found Reports', history_html)
        self.assertIn('Successful Returns', history_html)
        self.assertIn('Reputation', history_html)
        self.assertIn('Points', history_html)

    def test_finder_item_change_page_loads_normally(self):
        """Verify the Finder Item change page in Django Admin displays Finder metrics and not Lost Reports."""
        self.client.login(username='super_admin', password='Password123!')

        res = self.client.get(f'/admin/api/item/{self.found_item.id}/change/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertNotIn('Lost Reports', content)
        self.assertIn('Found Reports', content)
        self.assertIn('Successful Returns', content)

    def test_owner_item_change_page_loads_and_saves_normally(self):
        """Verify the Item can still be opened and saved normally in Django Admin."""
        self.client.login(username='super_admin', password='Password123!')

        # 1. GET change item page
        res = self.client.get(f'/admin/api/item/{self.lost_item.id}/change/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Lost Reports', content)
        self.assertNotIn('Found Reports', content)
        self.assertNotIn('Successful Returns', content)

        # 2. POST save item
        post_data = {
            'type': 'lost',
            'title': 'Lost Apple Watch Series 9',
            'description': 'Updated description',
            'category': 'electronics',
            'reward': '1200.00',
            'location': 'Library',
            'status': 'approved',
            'images-TOTAL_FORMS': '0',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        res_post = self.client.post(f'/admin/api/item/{self.lost_item.id}/change/', post_data)
        self.assertEqual(res_post.status_code, 302)

        self.lost_item.refresh_from_db()
        self.assertEqual(self.lost_item.title, 'Lost Apple Watch Series 9')
        self.assertEqual(float(self.lost_item.reward), 1200.00)

    def test_media_preview_exact_item_isolation_across_multiple_reports(self):
        """
        Verify exact Item image relationship isolation across multiple reports in the same category:
        Owner1 -> Lost Laptop -> Image A
        Finder1 -> Found Laptop -> Image B
        Owner2 -> Lost Laptop -> Image C
        Finder2 -> Found Laptop -> Image D
        No image item -> No photo uploaded message
        """
        owner2 = User.objects.create_user(username='owner2_user', email='owner2@example.com', password='Password123!', role='owner', is_verified=True)
        finder2 = User.objects.create_user(username='finder2_user', email='finder2@example.com', password='Password123!', role='finder', is_verified=True)

        img_a = SimpleUploadedFile("laptop_owner1.jpg", b"image_a_bytes", content_type="image/jpeg")
        img_b = SimpleUploadedFile("laptop_finder1.jpg", b"image_b_bytes", content_type="image/jpeg")
        img_c = SimpleUploadedFile("laptop_owner2.jpg", b"image_c_bytes", content_type="image/jpeg")
        img_d = SimpleUploadedFile("laptop_finder2.jpg", b"image_d_bytes", content_type="image/jpeg")

        item_owner1 = Item.objects.create(user=self.owner, type='lost', title='Dell XPS', category='electronics', image=img_a, status='pending')
        ItemImage.objects.create(item=item_owner1, image=img_a)

        item_finder1 = Item.objects.create(user=self.finder, type='found', title='Dell XPS', category='electronics', image=img_b, status='pending')
        ItemImage.objects.create(item=item_finder1, image=img_b)

        item_owner2 = Item.objects.create(user=owner2, type='lost', title='ThinkPad', category='electronics', image=img_c, status='pending')
        ItemImage.objects.create(item=item_owner2, image=img_c)

        item_finder2 = Item.objects.create(user=finder2, type='found', title='ThinkPad', category='electronics', image=img_d, status='pending')
        ItemImage.objects.create(item=item_finder2, image=img_d)

        item_no_img = Item.objects.create(user=self.owner, type='lost', title='Lost USB Drive', category='electronics', status='pending')

        # 1. Inspect media_preview for each item
        html_o1 = self.item_admin.media_preview(item_owner1)
        self.assertIn('laptop_owner1', html_o1)
        self.assertNotIn('laptop_finder1', html_o1)
        self.assertNotIn('laptop_owner2', html_o1)
        self.assertNotIn('laptop_finder2', html_o1)

        html_f1 = self.item_admin.media_preview(item_finder1)
        self.assertIn('laptop_finder1', html_f1)
        self.assertNotIn('laptop_owner1', html_f1)
        self.assertNotIn('laptop_owner2', html_f1)
        self.assertNotIn('laptop_finder2', html_f1)

        html_o2 = self.item_admin.media_preview(item_owner2)
        self.assertIn('laptop_owner2', html_o2)
        self.assertNotIn('laptop_owner1', html_o2)
        self.assertNotIn('laptop_finder1', html_o2)
        self.assertNotIn('laptop_finder2', html_o2)

        html_f2 = self.item_admin.media_preview(item_finder2)
        self.assertIn('laptop_finder2', html_f2)
        self.assertNotIn('laptop_owner1', html_f2)
        self.assertNotIn('laptop_finder1', html_f2)
        self.assertNotIn('laptop_owner2', html_f2)

        html_no_img = self.item_admin.media_preview(item_no_img)
        self.assertIn('No photo was uploaded', html_no_img)
        self.assertNotIn('laptop_owner1', html_no_img)
        self.assertNotIn('laptop_finder1', html_no_img)

        # 2. Check Django Admin change page GET requests
        self.client.login(username='super_admin', password='Password123!')

        res_o1 = self.client.get(f'/admin/api/item/{item_owner1.id}/change/')
        self.assertEqual(res_o1.status_code, 200)
        c_o1 = res_o1.content.decode('utf-8')
        self.assertIn('laptop_owner1', c_o1)
        self.assertNotIn('laptop_finder1', c_o1)

        res_f1 = self.client.get(f'/admin/api/item/{item_finder1.id}/change/')
        self.assertEqual(res_f1.status_code, 200)
        c_f1 = res_f1.content.decode('utf-8')
        self.assertIn('laptop_finder1', c_f1)
        self.assertNotIn('laptop_owner1', c_f1)

        res_no_img = self.client.get(f'/admin/api/item/{item_no_img.id}/change/')
        self.assertEqual(res_no_img.status_code, 200)
        c_no_img = res_no_img.content.decode('utf-8')
        self.assertIn('No photo was uploaded', c_no_img)
        self.assertNotIn('laptop_owner1', c_no_img)

    def test_owner_new_image_upload_and_admin_preview_200(self):
        """
        Owner reports lost item with image:
        - Uploaded image file is stored properly.
        - Image URL returns HTTP 200 (never 404).
        - Admin Change Item page previews the image.
        """
        import io
        from PIL import Image as PILImage
        from rest_framework.test import APIClient

        file = io.BytesIO()
        pil_img = PILImage.new('RGB', (100, 100), color=(100, 150, 200))
        pil_img.save(file, 'JPEG')
        file.seek(0)
        img = SimpleUploadedFile("new_lost_wallet.jpg", file.read(), content_type="image/jpeg")

        api_client = APIClient()
        api_client.force_authenticate(user=self.owner)

        data = {
            'type': 'lost',
            'title': 'Lost Brown Leather Wallet',
            'description': 'Lost in Kathmandu mall',
            'category': 'wallet',
            'reward': '500.00',
            'location': 'Kathmandu Mall',
            'image': img,
        }
        res = api_client.post('/api/items/', data, format='multipart')
        self.assertEqual(res.status_code, 201)
        item_id = res.data['id']

        item = Item.objects.get(id=item_id)
        self.assertTrue(bool(item.image))

        # Check media URL returns HTTP 200
        media_url = item.image.url
        res_media = self.client.get(media_url)
        self.assertEqual(res_media.status_code, 200)

        # Check Admin Change Item page
        self.client.login(username='super_admin', password='Password123!')
        res_admin = self.client.get(f'/admin/api/item/{item_id}/change/')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn('new_lost_wallet', res_admin.content.decode('utf-8'))

    def test_finder_new_image_upload_and_admin_preview_200(self):
        """
        Finder reports found item with image:
        - Uploaded image file is stored properly.
        - Image URL returns HTTP 200 (never 404).
        - Admin Change Item page previews the image.
        """
        import io
        from PIL import Image as PILImage
        from rest_framework.test import APIClient

        file = io.BytesIO()
        pil_img = PILImage.new('RGB', (100, 100), color=(200, 150, 100))
        pil_img.save(file, 'JPEG')
        file.seek(0)
        img = SimpleUploadedFile("new_found_keys.jpg", file.read(), content_type="image/jpeg")

        api_client = APIClient()
        api_client.force_authenticate(user=self.finder)

        data = {
            'type': 'found',
            'title': 'Found Set of Keys',
            'description': 'Found near bus park',
            'category': 'keys',
            'location': 'New Bus Park',
            'image': img,
        }
        res = api_client.post('/api/items/', data, format='multipart')
        self.assertEqual(res.status_code, 201)
        item_id = res.data['id']

        item = Item.objects.get(id=item_id)
        self.assertTrue(bool(item.image))

        # Check media URL returns HTTP 200
        media_url = item.image.url
        res_media = self.client.get(media_url)
        self.assertEqual(res_media.status_code, 200)

        # Check Admin Change Item page
        self.client.login(username='super_admin', password='Password123!')
        res_admin = self.client.get(f'/admin/api/item/{item_id}/change/')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn('new_found_keys', res_admin.content.decode('utf-8'))



    def test_missing_file_graceful_admin_handling(self):
        """
        When a legacy or ephemeral item record references a file not present on disk,
        Admin displays an informative warning instead of a broken layout.
        """
        missing_item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Old Camera',
            category='electronics',
            image='items/compressed_1788103970735_p6NPOKP.jpg',
            status='pending'
        )

        preview_html = self.item_admin.media_preview(missing_item)
        self.assertIn('File missing on server disk', preview_html)
        self.assertIn('compressed_1788103970735_p6NPOKP.jpg', preview_html)










