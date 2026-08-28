from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from api.models import (
    User, Item, FinderReputation, PointTransaction, FinderRating,
    UserBadge, Conversation, ChatMessage, Notification
)
from api.serializers import (
    ItemSerializer, UserSerializer, PublicProfileSerializer,
    RegisterSerializer, ConversationSerializer, ChatMessageSerializer
)
from api.views import (
    ItemListCreateView, ItemDetailView, MarkItemReturnedView,
    ConfirmItemReturnView, ReputationProfileView, PointHistoryView,
    RateFinderView, RatingStatusView, MyReportsView, RegisterView,
    ConversationInitView, ConversationListView, ChatListView
)
from api.reputation_service import (
    award_found_report_points, process_successful_return_reward,
    submit_finder_rating, get_or_create_reputation
)


class DynamicRoleSystemTests(TestCase):
    """
    Test suite verifying the 12 dynamic role scenarios from the specification.
    """

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_scenario_1_registration_creates_normal_user(self):
        """TEST 1: Hari registers without role selection -> Hari = Normal User ('user')."""
        view = RegisterView.as_view()
        req = self.factory.post('/api/register/', {
            'username': 'hari',
            'email': 'hari@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'first_name': 'Hari',
            'last_name': 'Sharma',
            'phone': '9800000001',
        })
        res = view(req)
        self.assertEqual(res.status_code, 201)
        hari = User.objects.get(username='hari')
        self.assertEqual(hari.role, 'user')

    def test_scenario_2_and_3_hari_lost_and_found_reports(self):
        """
        TEST 2 & 3:
        Hari reports 'I Lost Something' -> Lost Item created, Hari = Owner for that report.
        Hari reports 'I Found Something' -> Found Item created, Hari = Finder for that report (+5 pts).
        Account remains Normal User.
        """
        hari = User.objects.create_user(
            username='hari', email='hari@example.com', password='Password123!', role='user', is_verified=True
        )

        # 1. Report Lost Phone
        view = ItemListCreateView.as_view()
        req_lost = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost iPhone 15',
            'description': 'Black iPhone 15 lost near cafe',
            'category': 'phone',
            'location': 'Kathmandu Cafe',
            'reward': '1000.00'
        })
        force_authenticate(req_lost, user=hari)
        res_lost = view(req_lost)
        self.assertEqual(res_lost.status_code, 201)
        self.assertEqual(res_lost.data['type'], 'lost')
        self.assertEqual(res_lost.data['user_role'], 'Owner')
        self.assertEqual(float(res_lost.data['reward']), 1000.00)

        # Account remains normal user
        hari.refresh_from_db()
        self.assertEqual(hari.role, 'user')

        # 2. Report Found Wallet
        req_found = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Brown Leather Wallet',
            'description': 'Found brown leather wallet with keys',
            'category': 'wallet',
            'location': 'City Bus Park',
            'reward': '0.00'
        })
        force_authenticate(req_found, user=hari)
        res_found = view(req_found)
        self.assertEqual(res_found.status_code, 201)
        self.assertEqual(res_found.data['type'], 'found')
        self.assertEqual(res_found.data['user_role'], 'Finder')
        self.assertEqual(float(res_found.data['reward']), 0.00)

        # Hari earned +5 points for reporting found item
        rep = FinderReputation.objects.get(user=hari)
        self.assertEqual(rep.total_points, 5)

        # Previous Lost Item remains Owner
        lost_item = Item.objects.get(title='Lost iPhone 15')
        serializer_lost = ItemSerializer(lost_item, context={'request': req_lost})
        self.assertEqual(serializer_lost.data['user_role'], 'Owner')

    def test_scenario_4_to_8_milan_and_hari_dual_roles(self):
        """
        TEST 4 to 8:
        Milan registers and reports Found Phone (Milan = Finder).
        Hari reports Lost Phone (Hari = Owner) -> Chat: Hari (Owner) ↔ Milan (Finder).
        Later Milan reports Lost Wallet (Milan = Owner), Hari reports Found Wallet (Hari = Finder).
        Chat: Milan (Owner) ↔ Hari (Finder).
        Hari has 2 Lost reports & 2 Found reports under ONE unified account.
        """
        hari = User.objects.create_user(
            username='hari', email='hari@example.com', password='Password123!', role='user', is_verified=True
        )
        milan = User.objects.create_user(
            username='milan', email='milan@example.com', password='Password123!', role='user', is_verified=True
        )

        # Phone transaction
        lost_phone = Item.objects.create(
            user=hari, type='lost', title='Lost iPhone 15', category='phone', status='approved'
        )
        found_phone = Item.objects.create(
            user=milan, type='found', title='Found iPhone 15', category='phone', status='approved'
        )

        # Hari (Owner) initiates chat on found_phone
        init_view = ConversationInitView.as_view()
        req_conv1 = self.factory.post('/api/conversations/init/', {'item_id': found_phone.id})
        force_authenticate(req_conv1, user=hari)
        res_conv1 = init_view(req_conv1)
        self.assertEqual(res_conv1.status_code, 200)
        conv_phone_id = res_conv1.data['conversation_id']
        conv_phone = Conversation.objects.get(id=conv_phone_id)
        self.assertEqual(conv_phone.owner, hari)
        self.assertEqual(conv_phone.finder, milan)

        # Wallet transaction (Roles reversed!)
        lost_wallet = Item.objects.create(
            user=milan, type='lost', title='Lost Leather Wallet', category='wallet', status='approved'
        )
        found_wallet = Item.objects.create(
            user=hari, type='found', title='Found Leather Wallet', category='wallet', status='approved'
        )

        # Milan (Owner) initiates chat on found_wallet
        req_conv2 = self.factory.post('/api/conversations/init/', {'item_id': found_wallet.id})
        force_authenticate(req_conv2, user=milan)
        res_conv2 = init_view(req_conv2)
        self.assertEqual(res_conv2.status_code, 200)
        conv_wallet_id = res_conv2.data['conversation_id']
        conv_wallet = Conversation.objects.get(id=conv_wallet_id)
        self.assertEqual(conv_wallet.owner, milan)
        self.assertEqual(conv_wallet.finder, hari)

        # Verify conversation roles from Hari's perspective
        conv_list_view = ConversationListView.as_view()
        req_list = self.factory.get('/api/conversations/')
        force_authenticate(req_list, user=hari)
        res_list = conv_list_view(req_list)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.data), 2)

        # Hari adds 2 more items: Lost Laptop, Found Watch
        lost_laptop = Item.objects.create(user=hari, type='lost', title='Lost Laptop', category='electronics', status='approved')
        found_watch = Item.objects.create(user=hari, type='found', title='Found Watch', category='other', status='approved')

        # Hari's Profile check (TEST 8)
        profile_serializer = UserSerializer(hari)
        self.assertEqual(profile_serializer.data['lost_reports'], 2)
        self.assertEqual(profile_serializer.data['found_reports'], 2)

        # My Reports check
        my_reports_view = MyReportsView.as_view()
        req_my_reports = self.factory.get('/api/items/my-reports/')
        force_authenticate(req_my_reports, user=hari)
        res_my_reports = my_reports_view(req_my_reports)
        self.assertEqual(res_my_reports.status_code, 200)
        self.assertEqual(len(res_my_reports.data), 4)

    def test_scenario_9_and_10_successful_returns_and_ratings(self):
        """
        TEST 9 & 10:
        Phone return: Milan receives +100 Finder points, Hari rates Milan 5 stars (+10 bonus pts).
        Wallet return: Hari receives +100 Finder points, Milan rates Hari 5 stars (+10 bonus pts).
        """
        hari = User.objects.create_user(username='hari', email='hari@test.com', password='Password123!', role='user', is_verified=True)
        milan = User.objects.create_user(username='milan', email='milan@test.com', password='Password123!', role='user', is_verified=True)

        # --- 1. Phone Return: Lost Phone (Owner=Hari), Return Partner (Finder=Milan) ---
        lost_phone = Item.objects.create(user=hari, type='lost', title='Lost Phone', category='phone', status='approved')
        conv_phone = Conversation.objects.create(item=lost_phone, owner=hari, finder=milan)

        # Hari marks returned
        mark_view = MarkItemReturnedView.as_view()
        req_mark = self.factory.post(f'/api/items/{lost_phone.id}/mark-returned/')
        force_authenticate(req_mark, user=hari)
        mark_view(req_mark, pk=lost_phone.id)

        # Milan confirms return
        confirm_view = ConfirmItemReturnView.as_view()
        req_confirm = self.factory.post(f'/api/items/{lost_phone.id}/confirm-return/')
        force_authenticate(req_confirm, user=milan)
        res_confirm = confirm_view(req_confirm, pk=lost_phone.id)
        self.assertEqual(res_confirm.status_code, 200)

        # Milan received +100 points
        milan_rep = FinderReputation.objects.get(user=milan)
        self.assertEqual(milan_rep.total_points, 100)
        self.assertEqual(milan_rep.successful_returns, 1)

        # Hari rates Milan 5 stars
        rate_view = RateFinderView.as_view()
        req_rate = self.factory.post('/api/reputation/rate/', {'item_id': lost_phone.id, 'rating': 5, 'review': 'Great!'})
        force_authenticate(req_rate, user=hari)
        res_rate = rate_view(req_rate)
        self.assertEqual(res_rate.status_code, 201)

        milan_rep.refresh_from_db()
        self.assertEqual(milan_rep.total_points, 110)
        self.assertEqual(milan_rep.average_rating, 5.0)

        # --- 2. Wallet Return: Lost Wallet (Owner=Milan), Return Partner (Finder=Hari) ---
        lost_wallet = Item.objects.create(user=milan, type='lost', title='Lost Wallet', category='wallet', status='approved')
        conv_wallet = Conversation.objects.create(item=lost_wallet, owner=milan, finder=hari)

        # Milan marks returned
        req_mark2 = self.factory.post(f'/api/items/{lost_wallet.id}/mark-returned/')
        force_authenticate(req_mark2, user=milan)
        mark_view(req_mark2, pk=lost_wallet.id)

        # Hari confirms return
        req_confirm2 = self.factory.post(f'/api/items/{lost_wallet.id}/confirm-return/')
        force_authenticate(req_confirm2, user=hari)
        res_confirm2 = confirm_view(req_confirm2, pk=lost_wallet.id)
        self.assertEqual(res_confirm2.status_code, 200)

        # Hari received +100 points
        hari_rep = FinderReputation.objects.get(user=hari)
        self.assertEqual(hari_rep.total_points, 100)
        self.assertEqual(hari_rep.successful_returns, 1)

        # Milan rates Hari 5 stars
        req_rate2 = self.factory.post('/api/reputation/rate/', {'item_id': lost_wallet.id, 'rating': 5, 'review': 'Thanks Hari!'})
        force_authenticate(req_rate2, user=milan)
        res_rate2 = rate_view(req_rate2)
        self.assertEqual(res_rate2.status_code, 201)

        hari_rep.refresh_from_db()
        self.assertEqual(hari_rep.total_points, 110)
        self.assertEqual(hari_rep.average_rating, 5.0)

    def test_scenario_11_and_12_chat_independent_conversations(self):
        """
        TEST 11 & 12:
        Chat messages can be exchanged in Phone conversation and Wallet conversation
        independently between the same users.
        """
        hari = User.objects.create_user(username='hari', email='hari@test.com', password='Password123!', role='user', is_verified=True)
        milan = User.objects.create_user(username='milan', email='milan@test.com', password='Password123!', role='user', is_verified=True)

        phone_item = Item.objects.create(user=hari, type='lost', title='Lost Phone', category='phone', status='approved')
        wallet_item = Item.objects.create(user=milan, type='lost', title='Lost Wallet', category='wallet', status='approved')

        conv_phone = Conversation.objects.create(item=phone_item, owner=hari, finder=milan)
        conv_wallet = Conversation.objects.create(item=wallet_item, owner=milan, finder=hari)

        chat_view = ChatListView.as_view()

        # Hari sends message in Phone chat (Hari = Owner)
        req_msg1 = self.factory.post('/api/chat/', {
            'conversation_id': conv_phone.id,
            'message': 'Hi Milan, did you find my phone?',
            'message_type': 'text'
        })
        force_authenticate(req_msg1, user=hari)
        res_msg1 = chat_view(req_msg1)
        self.assertEqual(res_msg1.status_code, 201)
        self.assertEqual(res_msg1.data['sender_role'], 'Owner')

        # Hari sends message in Wallet chat (Hari = Finder)
        req_msg2 = self.factory.post('/api/chat/', {
            'conversation_id': conv_wallet.id,
            'message': 'Hi Milan, I have your wallet safe!',
            'message_type': 'text'
        })
        force_authenticate(req_msg2, user=hari)
        res_msg2 = chat_view(req_msg2)
        self.assertEqual(res_msg2.status_code, 201)
        self.assertEqual(res_msg2.data['sender_role'], 'Finder')

        # Milan views Phone chat
        req_get1 = self.factory.get(f'/api/chat/?conversation_id={conv_phone.id}')
        force_authenticate(req_get1, user=milan)
        res_get1 = chat_view(req_get1)
        self.assertEqual(res_get1.status_code, 200)
        self.assertEqual(len(res_get1.data), 1)
        self.assertEqual(res_get1.data[0]['message'], 'Hi Milan, did you find my phone?')

        # Milan views Wallet chat
        req_get2 = self.factory.get(f'/api/chat/?conversation_id={conv_wallet.id}')
        force_authenticate(req_get2, user=milan)
        res_get2 = chat_view(req_get2)
        self.assertEqual(res_get2.status_code, 200)
        self.assertEqual(len(res_get2.data), 1)
        self.assertEqual(res_get2.data[0]['message'], 'Hi Milan, I have your wallet safe!')
