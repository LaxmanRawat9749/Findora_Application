from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from api.models import User, Item
from api.serializers import ItemSerializer
from api.views import ItemListCreateView, ItemDetailView


class ItemRoleAndRewardTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='test_owner',
            email='owner@example.com',
            password='Password123!',
            role='owner',
            is_verified=True
        )
        self.finder = User.objects.create_user(
            username='test_finder',
            email='finder@example.com',
            password='Password123!',
            role='finder',
            is_verified=True
        )

    def test_finder_can_report_found_item_without_reward(self):
        """Finder can report a found item, default reward is 0.00."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.finder)
        request.user = self.finder
        
        data = {
            'type': 'found',
            'title': 'Found Black Wallet',
            'description': 'Found near cafeteria',
            'category': 'wallet',
            'location': 'Cafeteria Floor 1'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(user=self.finder)
        self.assertEqual(item.type, 'found')
        self.assertEqual(float(item.reward), 0.0)

    def test_finder_cannot_set_reward(self):
        """Finder attempting to submit a reward > 0 must fail validation."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.finder)
        request.user = self.finder
        
        data = {
            'type': 'found',
            'title': 'Found Watch',
            'description': 'Found near library',
            'category': 'other',
            'location': 'Library',
            'reward': '500'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('reward', serializer.errors)

    def test_finder_cannot_report_lost_item(self):
        """Finder cannot report a lost item."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.finder)
        request.user = self.finder
        
        data = {
            'type': 'lost',
            'title': 'Lost Keys',
            'description': 'Lost my keys',
            'category': 'keys',
            'location': 'Main Gate'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)

    def test_owner_can_report_lost_item_with_reward(self):
        """Owner can report a lost item with a reward amount."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.owner)
        request.user = self.owner
        
        data = {
            'type': 'lost',
            'title': 'Lost iPhone 13',
            'description': 'Lost blue iPhone in lecture hall',
            'category': 'phone',
            'location': 'Hall 3',
            'reward': '1500.00'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(user=self.owner)
        self.assertEqual(item.type, 'lost')
        self.assertEqual(float(item.reward), 1500.0)

    def test_owner_can_report_lost_item_without_reward(self):
        """Owner can report a lost item without setting a reward (defaults to 0.00)."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.owner)
        request.user = self.owner
        
        data = {
            'type': 'lost',
            'title': 'Lost ID Card',
            'description': 'Lost student ID card',
            'category': 'id_card',
            'location': 'Ground Floor'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(user=self.owner)
        self.assertEqual(item.type, 'lost')
        self.assertEqual(float(item.reward), 0.0)

    def test_owner_cannot_report_found_item(self):
        """Owner cannot report a found item."""
        request = self.factory.post('/api/items/')
        force_authenticate(request, user=self.owner)
        request.user = self.owner
        
        data = {
            'type': 'found',
            'title': 'Found Backpack',
            'description': 'Found backpack',
            'category': 'bag',
            'location': 'Auditorium'
        }
        
        serializer = ItemSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)

    def test_view_finder_post_rejection_with_reward(self):
        """POST /api/items/ by finder with reward fails with 400 Bad Request."""
        view = ItemListCreateView.as_view()
        request = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Ring',
            'description': 'Gold ring',
            'category': 'other',
            'location': 'Park',
            'reward': '200'
        })
        force_authenticate(request, user=self.finder)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('reward', response.data)

    def test_view_finder_post_success_without_reward(self):
        """POST /api/items/ by finder without reward succeeds with 201 Created."""
        view = ItemListCreateView.as_view()
        request = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Ring',
            'description': 'Gold ring',
            'category': 'other',
            'location': 'Park'
        })
        force_authenticate(request, user=self.finder)
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(float(response.data['reward']), 0.0)

    def test_view_owner_post_success_with_reward(self):
        """POST /api/items/ by owner with reward succeeds with 201 Created."""
        view = ItemListCreateView.as_view()
        request = self.factory.post('/api/items/', {
            'type': 'lost',
            'title': 'Lost Laptop',
            'description': 'Dell XPS 15',
            'category': 'electronics',
            'location': 'Lab 2',
            'reward': '5000'
        })
        force_authenticate(request, user=self.owner)
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(float(response.data['reward']), 5000.0)


class ReputationAndPointsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username='owner_alice',
            email='alice@example.com',
            password='Password123!',
            role='owner',
            is_verified=True,
        )
        self.finder = User.objects.create_user(
            username='finder_bob',
            email='bob@example.com',
            password='Password123!',
            role='finder',
            is_verified=True,
        )

    def test_1_finder_initial_state(self):
        """TEST 1: Finder starts with 0 points, 0 returns, and 'New Finder' reputation."""
        from api.reputation_service import get_or_create_reputation
        rep = get_or_create_reputation(self.finder)
        self.assertEqual(rep.total_points, 0)
        self.assertEqual(rep.successful_returns, 0)
        self.assertEqual(rep.reputation_display, "New Finder")

    def test_1b_owner_has_no_reputation_or_points_access(self):
        """TEST 1b: Owner cannot access reputation or point history endpoints."""
        from api.views import ReputationProfileView, PointHistoryView, RateFinderView
        from api.serializers import UserSerializer, PublicProfileSerializer

        # 1. /api/reputation/me/ returns 403 for Owner
        view_rep = ReputationProfileView.as_view()
        req_rep = self.factory.get('/api/reputation/me/')
        force_authenticate(req_rep, user=self.owner)
        res_rep = view_rep(req_rep)
        self.assertEqual(res_rep.status_code, 403)

        # 2. /api/reputation/history/ returns 403 for Owner
        view_hist = PointHistoryView.as_view()
        req_hist = self.factory.get('/api/reputation/history/')
        force_authenticate(req_hist, user=self.owner)
        res_hist = view_hist(req_hist)
        self.assertEqual(res_hist.status_code, 403)

        # 3. Serializers return None for Owner points/reputation
        user_data = UserSerializer(self.owner).data
        self.assertIsNone(user_data['total_points'])
        self.assertIsNone(user_data['reputation_display'])

        pub_data = PublicProfileSerializer(self.owner).data
        self.assertIsNone(pub_data['total_points'])
        self.assertIsNone(pub_data['reputation_display'])
        self.assertEqual(pub_data['badges'], [])

    def test_1c_finder_with_returns_no_rating_displays_not_rated_yet(self):
        """TEST 1c: Finder with completed returns but no rating shows 'Not rated yet'."""
        from api.reputation_service import get_or_create_reputation
        rep = get_or_create_reputation(self.finder)
        rep.successful_returns = 2
        rep.rating_count = 0
        rep.save()
        self.assertEqual(rep.reputation_display, "Not rated yet")

    def test_1d_finder_cannot_call_rate_endpoint(self):
        """TEST 1d: Finder cannot rate anyone via /api/reputation/rate/."""
        from api.views import RateFinderView
        view = RateFinderView.as_view()
        req = self.factory.post('/api/reputation/rate/', {
            'item_id': 1,
            'rating': 5,
        })
        force_authenticate(req, user=self.finder)
        res = view(req)
        self.assertEqual(res.status_code, 403)

    def test_2_found_report_awards_5_points(self):
        """TEST 2: Finder creates a valid Found Item report -> +5 Points."""
        view = ItemListCreateView.as_view()
        request = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Wallet',
            'description': 'Black leather wallet',
            'category': 'wallet',
            'location': 'Cafeteria',
        })
        force_authenticate(request, user=self.finder)
        response = view(request)
        self.assertEqual(response.status_code, 201)

        from api.models import PointTransaction, FinderReputation
        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 5)

        tx = PointTransaction.objects.filter(user=self.finder, transaction_type='FOUND_REPORT').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.points, 5)

    def test_3_duplicate_found_report_points_prevented(self):
        """TEST 3: Same Found report reward is not awarded twice."""
        from api.models import Item
        from api.reputation_service import award_found_report_points, get_or_create_reputation

        item = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Umbrella',
            category='other',
            status='approved',
        )

        first_award = award_found_report_points(self.finder, item)
        self.assertTrue(first_award)

        second_award = award_found_report_points(self.finder, item)
        self.assertFalse(second_award)

        rep = get_or_create_reputation(self.finder)
        self.assertEqual(rep.total_points, 5)

    def test_4_chat_does_not_award_return_points(self):
        """TEST 4: Communication between Finder and Owner does not award return points."""
        from api.models import Conversation, ChatMessage, Item, PointTransaction
        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost iPhone 15',
            category='phone',
            status='approved',
        )
        conv = Conversation.objects.create(item=item, owner=self.owner, finder=self.finder)
        ChatMessage.objects.create(conversation=conv, sender=self.finder, message="I found your phone!")

        tx_count = PointTransaction.objects.filter(user=self.finder, transaction_type='SUCCESSFUL_RETURN').count()
        self.assertEqual(tx_count, 0)

    def test_5_return_pending_does_not_award_points(self):
        """TEST 5: Marking return as pending by owner does not award return points yet."""
        from api.models import Item, PointTransaction
        from api.views import MarkItemReturnedView

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Passport',
            category='documents',
            status='approved',
        )

        view = MarkItemReturnedView.as_view()
        request = self.factory.post(f'/api/items/{item.id}/mark-returned/')
        force_authenticate(request, user=self.owner)
        response = view(request, pk=item.id)
        self.assertEqual(response.status_code, 200)

        tx_count = PointTransaction.objects.filter(user=self.finder, transaction_type='SUCCESSFUL_RETURN').count()
        self.assertEqual(tx_count, 0)

    def test_6_confirmed_return_awards_100_points_and_increments_return_count(self):
        """TEST 6: Confirmed successful return awards +100 Points and +1 Successful Return."""
        from api.models import Item, FinderReputation
        from api.views import ConfirmItemReturnView

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost iPhone 15',
            category='phone',
            status='approved',
            owner_returned_confirm=True,
        )

        view = ConfirmItemReturnView.as_view()
        request = self.factory.post(f'/api/items/{item.id}/confirm-return/')
        force_authenticate(request, user=self.finder)
        response = view(request, pk=item.id)
        self.assertEqual(response.status_code, 200)

        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 100)
        self.assertEqual(rep.successful_returns, 1)

    def test_7_duplicate_return_reward_prevented(self):
        """TEST 7: Same return confirmed again does not duplicate +100 points."""
        from api.models import Item, FinderReputation
        from api.reputation_service import process_successful_return_reward

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Gold Ring',
            category='other',
            status='resolved',
            owner_returned_confirm=True,
            finder_returned_confirm=True,
        )

        first_res = process_successful_return_reward(self.finder, self.owner, item)
        self.assertTrue(first_res)

        second_res = process_successful_return_reward(self.finder, self.owner, item)
        self.assertFalse(second_res)

        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 100)
        self.assertEqual(rep.successful_returns, 1)

    def test_8_owner_submits_5_star_rating(self):
        """TEST 8: Owner submits 5-star rating -> Rating saved & +10 positive-rating points."""
        from api.models import Item, FinderRating, FinderReputation, PointTransaction
        from api.views import RateFinderView
        from api.reputation_service import process_successful_return_reward

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Camera',
            category='electronics',
            status='resolved',
            owner_returned_confirm=True,
            finder_returned_confirm=True,
        )
        process_successful_return_reward(self.finder, self.owner, item)

        view = RateFinderView.as_view()
        request = self.factory.post('/api/reputation/rate/', {
            'item_id': item.id,
            'rating': 5,
            'review': 'Super quick and honest finder!',
        }, format='json')
        force_authenticate(request, user=self.owner)
        response = view(request)
        self.assertEqual(response.status_code, 201)

        rating = FinderRating.objects.get(owner=self.owner, item=item)
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.finder, self.finder)

        rep = FinderReputation.objects.get(user=self.finder)
        # 100 (return) + 10 (positive rating) = 110 points
        self.assertEqual(rep.total_points, 110)
        self.assertEqual(rep.average_rating, 5.0)
        self.assertEqual(rep.reputation_display, "5.0")

    def test_9_duplicate_rating_rejected(self):
        """TEST 9: Owner cannot submit multiple ratings for the same item return."""
        from api.models import Item
        from api.views import RateFinderView
        from api.reputation_service import process_successful_return_reward

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Headset',
            category='electronics',
            status='resolved',
            owner_returned_confirm=True,
            finder_returned_confirm=True,
        )
        process_successful_return_reward(self.finder, self.owner, item)

        view = RateFinderView.as_view()
        request1 = self.factory.post('/api/reputation/rate/', {
            'item_id': item.id,
            'rating': 5,
            'review': 'Great!',
        }, format='json')
        force_authenticate(request1, user=self.owner)
        res1 = view(request1)
        self.assertEqual(res1.status_code, 201)

        request2 = self.factory.post('/api/reputation/rate/', {
            'item_id': item.id,
            'rating': 4,
            'review': 'Another review',
        }, format='json')
        force_authenticate(request2, user=self.owner)
        res2 = view(request2)
        self.assertEqual(res2.status_code, 400)
        self.assertIn('Rating already submitted', res2.data['error'])

    def test_10_badge_first_return(self):
        """TEST 10: 1 successful return unlocks 'First Return' badge."""
        from api.models import UserBadge
        from api.reputation_service import get_or_create_reputation, check_and_award_badges

        rep = get_or_create_reputation(self.finder)
        rep.successful_returns = 1
        rep.save()

        check_and_award_badges(self.finder, rep)
        self.assertTrue(UserBadge.objects.filter(user=self.finder, badge_key='FIRST_RETURN').exists())

    def test_11_badge_helpful_finder(self):
        """TEST 11: 5 successful returns unlocks 'Helpful Finder' badge."""
        from api.models import UserBadge
        from api.reputation_service import get_or_create_reputation, check_and_award_badges

        rep = get_or_create_reputation(self.finder)
        rep.successful_returns = 5
        rep.save()

        check_and_award_badges(self.finder, rep)
        self.assertTrue(UserBadge.objects.filter(user=self.finder, badge_key='HELPFUL_FINDER').exists())

    def test_12_badge_trusted_finder(self):
        """TEST 12: 10 successful returns unlocks 'Trusted Finder' badge."""
        from api.models import UserBadge
        from api.reputation_service import get_or_create_reputation, check_and_award_badges

        rep = get_or_create_reputation(self.finder)
        rep.successful_returns = 10
        rep.save()

        check_and_award_badges(self.finder, rep)
        self.assertTrue(UserBadge.objects.filter(user=self.finder, badge_key='TRUSTED_FINDER').exists())

    def test_13_monetary_reward_remains_independent(self):
        """TEST 13: Owner offering Rs. 500 reward works independently from points/reputation."""
        from api.models import Item, FinderReputation
        from api.reputation_service import process_successful_return_reward

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Gold Chain',
            reward=500.00,
            status='resolved',
            owner_returned_confirm=True,
            finder_returned_confirm=True,
        )

        process_successful_return_reward(self.finder, self.owner, item)

        self.assertEqual(float(item.reward), 500.00)
        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 100)
        self.assertEqual(rep.successful_returns, 1)

    def test_14_no_reward_still_gives_points_and_reputation(self):
        """TEST 14: Owner offering no reward (0.00) still awards points and reputation."""
        from api.models import Item, FinderReputation
        from api.reputation_service import process_successful_return_reward

        item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Lost Notebook',
            reward=0.00,
            status='resolved',
            owner_returned_confirm=True,
            finder_returned_confirm=True,
        )

        process_successful_return_reward(self.finder, self.owner, item)

        self.assertEqual(float(item.reward), 0.00)
        rep = FinderReputation.objects.get(user=self.finder)
        self.assertEqual(rep.total_points, 100)

    def test_15_client_cannot_arbitrarily_set_points(self):
        """TEST 15: Client sending arbitrary point parameters in item/profile is ignored/rejected."""
        from api.views import ItemListCreateView, ProfileView
        from api.models import FinderReputation

        # Try injecting points into item creation
        view = ItemListCreateView.as_view()
        request = self.factory.post('/api/items/', {
            'type': 'found',
            'title': 'Found Backpack',
            'category': 'bag',
            'points': 9999,
        })
        force_authenticate(request, user=self.finder)
        response = view(request)
        self.assertEqual(response.status_code, 201)

        rep = FinderReputation.objects.get(user=self.finder)
        # Should only get the standard +5 points, not 9999
        self.assertEqual(rep.total_points, 5)

    def test_16_public_profile_includes_reputation(self):
        """TEST 16: PublicProfileView includes reputation, points, returns, and badges."""
        from api.views import PublicProfileView
        from api.reputation_service import get_or_create_reputation

        rep = get_or_create_reputation(self.finder)
        rep.total_points = 250
        rep.successful_returns = 3
        rep.rating_count = 2
        rep.rating_sum = 10
        rep.average_rating = 5.0
        rep.save()

        view = PublicProfileView.as_view()
        request = self.factory.get(f'/api/users/{self.finder.id}/public-profile/')
        force_authenticate(request, user=self.owner)
        response = view(request, pk=self.finder.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_points'], 250)
        self.assertEqual(response.data['successful_returns'], 3)
        self.assertEqual(response.data['reputation_display'], "5.0")


class OwnerFoundMatchingVisibilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner_milan = User.objects.create_user(
            username='milan_owner',
            email='milan@example.com',
            password='Password123!',
            role='owner',
            is_verified=True,
        )
        self.owner_dave = User.objects.create_user(
            username='dave_owner',
            email='dave@example.com',
            password='Password123!',
            role='owner',
            is_verified=True,
        )
        self.finder_hari = User.objects.create_user(
            username='hari_finder',
            email='hari@example.com',
            password='Password123!',
            role='finder',
            is_verified=True,
        )
        self.finder_john = User.objects.create_user(
            username='john_finder',
            email='john@example.com',
            password='Password123!',
            role='finder',
            is_verified=True,
        )

    def test_1_owner_with_no_lost_items_sees_empty_found_section(self):
        """Case 1: Owner has no lost items -> Found section is empty."""
        # Hari reported a found phone
        Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='Found iPhone 15 Pro',
            category='phone',
            status='approved',
        )

        view = ItemListCreateView.as_view()
        request = self.factory.get('/api/items/?type=found')
        force_authenticate(request, user=self.owner_milan)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_2_owner_with_lost_item_no_matching_found_items(self):
        """Case 2: Owner has lost item but no matching found item exists -> Found section is empty."""
        # Milan lost passport (documents)
        Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='Lost Passport',
            category='documents',
            status='approved',
        )
        # Hari found a phone, John found keys
        Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='Found iPhone 15',
            category='phone',
            status='approved',
        )
        Item.objects.create(
            user=self.finder_john,
            type='found',
            title='Found Honda Keys',
            category='keys',
            status='approved',
        )

        view = ItemListCreateView.as_view()
        request = self.factory.get('/api/items/?type=found')
        force_authenticate(request, user=self.owner_milan)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_3_owner_with_lost_item_and_matching_found_item(self):
        """Case 3: Owner has lost item and matching found item exists -> Found item appears."""
        # Milan lost iPhone 15
        Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='Lost iPhone 15',
            category='phone',
            status='approved',
        )
        # Hari found iPhone 15
        found_iphone = Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='Found iPhone 15 Black',
            category='phone',
            status='approved',
        )

        view = ItemListCreateView.as_view()
        request = self.factory.get('/api/items/?type=found')
        force_authenticate(request, user=self.owner_milan)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], found_iphone.id)
        self.assertEqual(response.data[0]['title'], 'Found iPhone 15 Black')

    def test_4_owner_does_not_see_unrelated_found_items_of_other_owners(self):
        """Case 4: Owner Milan does not see Found items matching other owners' lost items."""
        # Milan lost iPhone 15 (phone)
        Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='iPhone 15',
            category='phone',
            status='approved',
        )
        # Dave lost Car Keys (keys)
        Item.objects.create(
            user=self.owner_dave,
            type='lost',
            title='Toyota Car Keys',
            category='keys',
            status='approved',
        )
        # Hari found iPhone 15
        found_phone = Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='iPhone 15',
            category='phone',
            status='approved',
        )
        # John found Toyota Keys
        found_keys = Item.objects.create(
            user=self.finder_john,
            type='found',
            title='Toyota Car Keys',
            category='keys',
            status='approved',
        )

        view = ItemListCreateView.as_view()

        # Milan checks Found tab
        req_milan = self.factory.get('/api/items/?type=found')
        force_authenticate(req_milan, user=self.owner_milan)
        res_milan = view(req_milan)
        self.assertEqual(res_milan.status_code, 200)
        self.assertEqual(len(res_milan.data), 1)
        self.assertEqual(res_milan.data[0]['id'], found_phone.id)

        # Dave checks Found tab
        req_dave = self.factory.get('/api/items/?type=found')
        force_authenticate(req_dave, user=self.owner_dave)
        res_dave = view(req_dave)
        self.assertEqual(res_dave.status_code, 200)
        self.assertEqual(len(res_dave.data), 1)
        self.assertEqual(res_dave.data[0]['id'], found_keys.id)

    def test_5_owner_detail_view_permissions(self):
        """Case 5: Owner can view matched found item detail; unrelated found item returns 403."""
        # Milan lost iPhone 15
        Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='iPhone 15',
            category='phone',
            status='approved',
        )
        # Hari found iPhone 15
        matched_found = Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='iPhone 15',
            category='phone',
            status='approved',
        )
        # John found gold watch (unrelated)
        unrelated_found = Item.objects.create(
            user=self.finder_john,
            type='found',
            title='Gold Watch',
            category='other',
            status='approved',
        )

        view = ItemDetailView.as_view()

        # Matched found item detail -> 200 OK
        req1 = self.factory.get(f'/api/items/{matched_found.id}/')
        force_authenticate(req1, user=self.owner_milan)
        res1 = view(req1, pk=matched_found.id)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.data['id'], matched_found.id)

        # Unrelated found item detail -> 403 Forbidden
        req2 = self.factory.get(f'/api/items/{unrelated_found.id}/')
        force_authenticate(req2, user=self.owner_milan)
        res2 = view(req2, pk=unrelated_found.id)
        self.assertEqual(res2.status_code, 403)

    def test_6_owner_all_tab_shows_own_lost_and_matched_found(self):
        """Case 6: Owner 'All' tab returns owner's lost items + matched found items."""
        lost_item = Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='Lost iPhone 15',
            category='phone',
            status='approved',
        )
        found_item = Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='Found iPhone 15',
            category='phone',
            status='approved',
        )
        # Unrelated found item
        Item.objects.create(
            user=self.finder_john,
            type='found',
            title='Found Bag',
            category='bag',
            status='approved',
        )

        view = ItemListCreateView.as_view()
        request = self.factory.get('/api/items/')
        force_authenticate(request, user=self.owner_milan)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        item_ids = [it['id'] for it in response.data]
        self.assertIn(lost_item.id, item_ids)
        self.assertIn(found_item.id, item_ids)
        self.assertEqual(len(item_ids), 2)

    def test_7_finder_visibility_rules_intact(self):
        """Case 7: Finder continues to see all approved lost items and own found items."""
        lost_1 = Item.objects.create(
            user=self.owner_milan,
            type='lost',
            title='Lost iPhone 15',
            category='phone',
            status='approved',
        )
        lost_2 = Item.objects.create(
            user=self.owner_dave,
            type='lost',
            title='Lost Keys',
            category='keys',
            status='approved',
        )
        own_found = Item.objects.create(
            user=self.finder_hari,
            type='found',
            title='Found iPhone 15',
            category='phone',
            status='approved',
        )
        other_found = Item.objects.create(
            user=self.finder_john,
            type='found',
            title='Found Keys',
            category='keys',
            status='approved',
        )

        view = ItemListCreateView.as_view()

        # Finder queries ?type=lost -> Sees all approved lost items
        req_lost = self.factory.get('/api/items/?type=lost')
        force_authenticate(req_lost, user=self.finder_hari)
        res_lost = view(req_lost)
        self.assertEqual(res_lost.status_code, 200)
        lost_ids = [it['id'] for it in res_lost.data]
        self.assertIn(lost_1.id, lost_ids)
        self.assertIn(lost_2.id, lost_ids)

        # Finder queries ?type=found -> Sees only own found items
        req_found = self.factory.get('/api/items/?type=found')
        force_authenticate(req_found, user=self.finder_hari)
        res_found = view(req_found)
        self.assertEqual(res_found.status_code, 200)
        found_ids = [it['id'] for it in res_found.data]
        self.assertIn(own_found.id, found_ids)
        self.assertNotIn(other_found.id, found_ids)


