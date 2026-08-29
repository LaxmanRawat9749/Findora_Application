from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from api.models import (
    User, Item, FinderReputation, PointTransaction, FinderRating,
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
    ConversationInitView, ChatListView
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



