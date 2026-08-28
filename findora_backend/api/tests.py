from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
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
    RateFinderView, RatingStatusView, MyReportsView, RegisterView,
    ChatProfileView
)
from api.reputation_service import (
    award_found_report_points, process_successful_return_reward,
    submit_finder_rating, get_or_create_reputation, get_badge_progress_list,
    check_and_award_badges
)
from api.reputation_constants import BADGES


class ActionBasedRoleAndItemTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.milan = User.objects.create_user(
            username='milan',
            email='milan@example.com',
            password='Password123!',
            role='user',
            is_verified=True
        )
        self.hari = User.objects.create_user(
            username='hari',
            email='hari@example.com',
            password='Password123!',
            role='user',
            is_verified=True
        )

    def test_single_user_can_report_both_lost_and_found_items(self):
        """Milan as a normal user can report a lost item (as Owner) and a found item (as Finder)."""
        view = ItemListCreateView.as_view()

        # 1. Milan reports a lost phone
        req_lost = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost iPhone 15',
            'description': 'Blue iPhone 15 lost in library',
            'category': 'phone',
            'location': 'Library 2nd Floor',
            'reward': '1000.00'
        })
        force_authenticate(req_lost, user=self.milan)
        res_lost = view(req_lost)
        self.assertEqual(res_lost.status_code, 201)
        self.assertEqual(res_lost.data['type'], 'lost')
        self.assertEqual(float(res_lost.data['reward']), 1000.0)
        self.assertEqual(res_lost.data['user_role'], 'owner')

        # 2. Milan reports a found wallet
        req_found = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Black Wallet',
            'description': 'Found brown leather wallet',
            'category': 'wallet',
            'location': 'Cafeteria'
        })
        force_authenticate(req_found, user=self.milan)
        res_found = view(req_found)
        self.assertEqual(res_found.status_code, 201)
        self.assertEqual(res_found.data['type'], 'found')
        self.assertEqual(float(res_found.data['reward']), 0.0)
        self.assertEqual(res_found.data['user_role'], 'finder')

        # Milan has 1 lost report and 1 found report
        self.assertEqual(Item.objects.filter(user=self.milan, type='lost').count(), 1)
        self.assertEqual(Item.objects.filter(user=self.milan, type='found').count(), 1)

    def test_found_item_cannot_have_reward(self):
        """Found item report with reward > 0 must fail validation."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.milan)
        request.user = self.milan
        
        data = {
            'type': 'found',
            'title': 'Found Watch',
            'description': 'Found silver watch',
            'category': 'other',
            'location': 'Park',
            'reward': '500'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('reward', serializer.errors)

    def test_lost_item_can_have_optional_reward(self):
        """Lost item report can specify a monetary reward."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.milan)
        request.user = self.milan
        
        data = {
            'type': 'lost',
            'title': 'Lost Keys',
            'description': 'House keys with red keychain',
            'category': 'keys',
            'location': 'Bus Stop',
            'reward': '300.00'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(user=self.milan)
        self.assertEqual(item.type, 'lost')
        self.assertEqual(float(item.reward), 300.0)

    def test_registration_creates_normal_user_without_permanent_owner_finder(self):
        """Registration creates a normal user with role='user'."""
        view = RegisterView.as_view()
        req = self.factory.post('/api/register/', {
            'username': 'sita_sharma',
            'email': 'sita@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'first_name': 'Sita',
            'last_name': 'Sharma',
            'phone': '9800000001'
        })
        res = view(req)
        self.assertEqual(res.status_code, 201)
        created_user = User.objects.get(username='sita_sharma')
        self.assertEqual(created_user.role, 'user')


class RoleSwitchingAndReturnWorkflowTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.milan = User.objects.create_user(
            username='milan', email='milan@example.com', password='Password123!', role='user', is_verified=True
        )
        self.hari = User.objects.create_user(
            username='hari', email='hari@example.com', password='Password123!', role='user', is_verified=True
        )

    def test_user_switches_roles_across_multiple_reports(self):
        """Milan reports 2 Lost items (Owner) and 2 Found items (Finder)."""
        lost1 = Item.objects.create(user=self.milan, type='lost', title='Lost iPhone', category='phone', status='approved')
        found1 = Item.objects.create(user=self.milan, type='found', title='Found Watch', category='other', status='approved')
        lost2 = Item.objects.create(user=self.milan, type='lost', title='Lost Wallet', category='wallet', status='approved')
        found2 = Item.objects.create(user=self.milan, type='found', title='Found Keys', category='keys', status='approved')

        # Serializer reports correct contextual role
        self.assertEqual(ItemSerializer(lost1).data['user_role'], 'owner')
        self.assertEqual(ItemSerializer(found1).data['user_role'], 'finder')
        self.assertEqual(ItemSerializer(lost2).data['user_role'], 'owner')
        self.assertEqual(ItemSerializer(found2).data['user_role'], 'finder')

        # Milan's profile aggregates both counts
        user_data = UserSerializer(self.milan).data
        self.assertEqual(user_data['lost_reports_count'], 2)
        self.assertEqual(user_data['found_reports_count'], 2)

    def test_complete_return_workflow_and_finder_points(self):
        """Milan lost phone (Owner). Hari found phone (Finder). Return completed -> Hari gets +100 points, Milan rates Hari."""
        # 1. Milan reports lost phone
        lost_item = Item.objects.create(
            user=self.milan, type='lost', title='Milan Lost Phone', category='phone', status='approved'
        )

        # 2. Conversation between Milan (Owner) and Hari (Finder)
        conv = Conversation.objects.create(item=lost_item, owner=self.milan, finder=self.hari)

        # 3. Milan marks returned
        mark_view = MarkItemReturnedView.as_view()
        req_mark = self.factory.post(f'/api/items/{lost_item.id}/mark-returned/')
        force_authenticate(req_mark, user=self.milan)
        res_mark = mark_view(req_mark, pk=lost_item.id)
        self.assertEqual(res_mark.status_code, 200)

        # 4. Hari confirms return
        confirm_view = ConfirmItemReturnView.as_view()
        req_confirm = self.factory.post(f'/api/items/{lost_item.id}/confirm-return/')
        force_authenticate(req_confirm, user=self.hari)
        res_confirm = confirm_view(req_confirm, pk=lost_item.id)
        self.assertEqual(res_confirm.status_code, 200)

        # Hari receives +100 Points and +1 Successful Return
        rep_hari = FinderReputation.objects.get(user=self.hari)
        self.assertEqual(rep_hari.total_points, 100)
        self.assertEqual(rep_hari.successful_returns, 1)

        # Milan (Owner) rates Hari (Finder) with 5 stars -> Hari receives +10 bonus points
        rate_view = RateFinderView.as_view()
        req_rate = self.factory.post('/api/reputation/rate/', {
            'item_id': lost_item.id,
            'rating': 5,
            'review': 'Great finder, returned immediately!'
        })
        force_authenticate(req_rate, user=self.milan)
        res_rate = rate_view(req_rate)
        self.assertEqual(res_rate.status_code, 201)

        rep_hari.refresh_from_db()
        self.assertEqual(rep_hari.total_points, 110)
        self.assertEqual(rep_hari.average_rating, 5.0)

    def test_non_owner_cannot_rate_finder(self):
        """A user who is not the owner for that item cannot rate the finder."""
        lost_item = Item.objects.create(
            user=self.milan, type='lost', title='Milan Lost Phone', category='phone', status='resolved'
        )
        PointTransaction.objects.create(
            user=self.hari, points=100, transaction_type='SUCCESSFUL_RETURN', related_item=lost_item
        )

        third_user = User.objects.create_user(
            username='random_user', email='random@example.com', password='Password123!', role='user', is_verified=True
        )

        rate_view = RateFinderView.as_view()
        req_rate = self.factory.post('/api/reputation/rate/', {
            'item_id': lost_item.id,
            'rating': 5
        })
        force_authenticate(req_rate, user=third_user)
        res_rate = rate_view(req_rate)
        self.assertEqual(res_rate.status_code, 400)

    def test_conversation_and_chat_profile_contextual_roles(self):
        """ChatProfileView returns contextual role 'finder' or 'owner' for the conversation partner."""
        lost_item = Item.objects.create(
            user=self.milan, type='lost', title='Milan Lost Watch', category='other', status='approved'
        )
        conv = Conversation.objects.create(item=lost_item, owner=self.milan, finder=self.hari)

        chat_prof_view = ChatProfileView.as_view()

        # Milan viewing chat profile of Hari -> Hari is Finder
        req_milan = self.factory.get(f'/api/chat/profile/?conversation_id={conv.id}')
        force_authenticate(req_milan, user=self.milan)
        res_milan = chat_prof_view(req_milan)
        self.assertEqual(res_milan.status_code, 200)
        self.assertEqual(res_milan.data['id'], self.hari.id)
        self.assertEqual(res_milan.data['role'], 'finder')

        # Hari viewing chat profile of Milan -> Milan is Owner
        req_hari = self.factory.get(f'/api/chat/profile/?conversation_id={conv.id}')
        force_authenticate(req_hari, user=self.hari)
        res_hari = chat_prof_view(req_hari)
        self.assertEqual(res_hari.status_code, 200)
        self.assertEqual(res_hari.data['id'], self.milan.id)
        self.assertEqual(res_hari.data['role'], 'owner')


class ReputationAndBadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user', email='test@example.com', password='Password123!', role='user', is_verified=True
        )
        self.other_user = User.objects.create_user(
            username='other_user', email='other@example.com', password='Password123!', role='user', is_verified=True
        )
        self.factory = APIRequestFactory()

    def test_reputation_me_and_history_accessible_to_normal_user(self):
        """Any normal user can access /api/reputation/me/ and /api/reputation/history/."""
        view_rep = ReputationProfileView.as_view()
        req_rep = self.factory.get('/api/reputation/me/')
        force_authenticate(req_rep, user=self.user)
        res_rep = view_rep(req_rep)
        self.assertEqual(res_rep.status_code, 200)
        self.assertEqual(res_rep.data['total_points'], 0)

        view_hist = PointHistoryView.as_view()
        req_hist = self.factory.get('/api/reputation/history/')
        force_authenticate(req_hist, user=self.user)
        res_hist = view_hist(req_hist)
        self.assertEqual(res_hist.status_code, 200)

    def test_found_report_awards_5_points_to_normal_user(self):
        """Reporting a found item awards +5 points."""
        item = Item.objects.create(
            user=self.user, type='found', title='Found Glasses', category='other', status='approved'
        )
        awarded = award_found_report_points(self.user, item)
        self.assertTrue(awarded)

        rep = get_or_create_reputation(self.user)
        self.assertEqual(rep.total_points, 5)

        # Duplicate award prevented
        awarded_again = award_found_report_points(self.user, item)
        self.assertFalse(awarded_again)
        rep.refresh_from_db()
        self.assertEqual(rep.total_points, 5)

    def test_badge_unlock_progression(self):
        """User unlocks First Return badge after 1 return, Helpful Finder after 5, Trusted Finder after 10."""
        rep = get_or_create_reputation(self.user)
        rep.successful_returns = 1
        rep.save()
        badges1 = check_and_award_badges(self.user, rep)
        self.assertEqual(len(badges1), 1)
        self.assertEqual(badges1[0].badge_key, 'FIRST_RETURN')

        rep.successful_returns = 5
        rep.save()
        badges2 = check_and_award_badges(self.user, rep)
        self.assertEqual(len(badges2), 1)
        self.assertEqual(badges2[0].badge_key, 'HELPFUL_FINDER')

        rep.successful_returns = 10
        rep.save()
        badges3 = check_and_award_badges(self.user, rep)
        self.assertEqual(len(badges3), 1)
        self.assertEqual(badges3[0].badge_key, 'TRUSTED_FINDER')


class MatchingAndVisibilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.alice = User.objects.create_user(
            username='alice', email='alice@example.com', password='Password123!', role='user', is_verified=True
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@example.com', password='Password123!', role='user', is_verified=True
        )

        # Alice lost a blue iPhone
        self.alice_lost_phone = Item.objects.create(
            user=self.alice, type='lost', title='Blue iPhone 13', category='phone', status='approved'
        )
        # Bob found an iPhone
        self.bob_found_phone = Item.objects.create(
            user=self.bob, type='found', title='Found iPhone 13 in Park', category='phone', status='approved'
        )
        # Bob found an unrelated keys
        self.bob_found_keys = Item.objects.create(
            user=self.bob, type='found', title='Found Car Keys', category='keys', status='approved'
        )

    def test_public_lost_items_visible_to_all(self):
        """Any user browsing lost items sees approved lost items."""
        view = ItemListCreateView.as_view()
        req = self.factory.get('/api/items/?type=lost')
        force_authenticate(req, user=self.bob)
        res = view(req)
        self.assertEqual(res.status_code, 200)
        item_ids = [item['id'] for item in res.data]
        self.assertIn(self.alice_lost_phone.id, item_ids)

    def test_matched_found_items_visible_to_owner(self):
        """Alice sees Bob's found iPhone because it matches her lost iPhone category and keywords."""
        view = ItemListCreateView.as_view()
        req = self.factory.get('/api/items/?type=found')
        force_authenticate(req, user=self.alice)
        res = view(req)
        self.assertEqual(res.status_code, 200)
        item_ids = [item['id'] for item in res.data]
        self.assertIn(self.bob_found_phone.id, item_ids)
        self.assertNotIn(self.bob_found_keys.id, item_ids)
