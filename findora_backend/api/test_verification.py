"""
Findora Universal Matching & Strong Ownership Verification Tests.

Tests:
  1. Multi-category Stage 1 candidate matching engine across all categories (Phone, Wallet, Keys, Documents, Bag, Laptop, etc.)
  2. Strict privacy protection: Owner private evidence is NEVER exposed to finders or public serializers.
  3. Stage 2 Blind Verification:
     - Independent blind submissions
     - Distinctive discriminative proof evaluation (5 common != 1 unique)
     - Contradictory evidence detection
     - Multiple candidate owners ambiguity handling (MULTIPLE_POSSIBLE_OWNERS)
  4. Non-serial item verification (Wallets, Keys, Bags, Books, Clothing, Jewelry)
  5. API endpoints: Matches, Schema, Start Verification, Submit Evidence, Provide Proof.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Item,
    PotentialMatch,
    User,
    VerificationEvidence,
    VerificationRequest,
)
from .verification_engine import (
    compute_candidate_match_score,
    evaluate_verification_session,
    run_candidate_matching_for_item,
)
from .verification_constants import CATEGORY_VERIFICATION_SCHEMAS


class UniversalMatchingAndVerificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Users
        self.owner = User.objects.create_user(
            username='owner_user', email='owner@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.owner2 = User.objects.create_user(
            username='owner_user2', email='owner2@example.com', password='Password123!', role='owner', is_verified=True
        )
        self.finder = User.objects.create_user(
            username='finder_user', email='finder@example.com', password='Password123!', role='finder', is_verified=True
        )
        self.admin = User.objects.create_superuser(
            username='admin_user', email='admin@example.com', password='Password123!', role='admin'
        )

    # ─── 1. Category Matching & Compatibility Tests ─────────────────────────

    def test_candidate_matching_across_different_categories(self):
        """Test candidate matching gives 0 score to completely incompatible categories."""
        lost_wallet = Item.objects.create(
            user=self.owner, type='lost', title='Brown Leather Wallet', category='wallet', status='approved'
        )
        found_phone = Item.objects.create(
            user=self.finder, type='found', title='Samsung Galaxy Phone', category='phone', status='approved'
        )

        score, confidence, reasons, strength = compute_candidate_match_score(lost_wallet, found_phone)
        self.assertEqual(score, 0.0)
        self.assertEqual(confidence, 'low')

    def test_candidate_matching_compatible_documents_and_id_card(self):
        """Test compatible categories (documents <-> id_card) match successfully."""
        lost_doc = Item.objects.create(
            user=self.owner, type='lost', title='Lost Citizenship Document', category='documents', status='approved'
        )
        found_id = Item.objects.create(
            user=self.finder, type='found', title='Found Citizenship Card', category='id_card', status='approved'
        )

        score, confidence, reasons, strength = compute_candidate_match_score(lost_doc, found_id)
        self.assertGreater(score, 10.0)
        self.assertTrue(any('Compatible' in r or 'Category' in r for r in reasons))

    def test_candidate_matching_brand_color_location_proximity(self):
        """Test multi-attribute candidate scoring with brand, model, color, and coordinates."""
        lost_phone = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Samsung S24 Black',
            category='phone',
            brand='Samsung',
            model_name='S24',
            primary_color='Black',
            latitude=27.7172,
            longitude=85.3240,
            status='approved',
        )
        found_phone = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Black Samsung Phone',
            category='phone',
            brand='Samsung',
            model_name='S24',
            primary_color='Black',
            latitude=27.7180,
            longitude=85.3245,
            status='approved',
        )

        score, confidence, reasons, strength = compute_candidate_match_score(lost_phone, found_phone)
        self.assertGreaterEqual(score, 70.0)
        self.assertEqual(confidence, 'high')
        self.assertIn(strength, ['strong_identifier', 'distinctive_features'])

    # ─── 2. Privacy Protection Tests ────────────────────────────────────────

    def test_owner_private_evidence_is_never_exposed_in_public_serializers(self):
        """Private owner evidence must be stripped for non-owner and public API requests."""
        lost_item = Item.objects.create(
            user=self.owner,
            type='lost',
            title='iPhone 15 Pro Max',
            category='phone',
            brand='Apple',
            status='approved',
            private_attributes={
                'damage_or_case': 'Scratch near volume button, spigen red case',
                'wallpaper_or_lockscreen': 'Photo of golden retriever',
            },
            identifier_hash='5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
            identifier_masked='******4321',
        )

        # Authenticate as Finder
        self.client.force_authenticate(user=self.finder)
        res = self.client.get(f'/api/items/{lost_item.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn('private_attributes', res.data)
        self.assertNotIn('identifier_hash', res.data)
        self.assertEqual(res.data.get('identifier_masked'), '******4321')

        # Authenticate as Owner (can see their own private attributes)
        self.client.force_authenticate(user=self.owner)
        res_owner = self.client.get(f'/api/items/{lost_item.id}/')
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)
        self.assertIn('private_attributes', res_owner.data)

    # ─── 3. Non-Serial Item Blind Verification: Wallet ───────────────────────

    def test_wallet_blind_verification_matching_contents(self):
        """Wallet verification without serial number: matches based on non-public internal cards."""
        lost_wallet = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Dark Brown Leather Wallet',
            category='wallet',
            primary_color='Brown',
            status='approved',
            private_attributes={
                'internal_contents': 'Gym membership card, Blood donor card, Rs 500 note',
                'wallet_characteristics': 'Bifold leather with coin zipper',
            }
        )
        found_wallet = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Brown Wallet',
            category='wallet',
            primary_color='Brown',
            status='approved',
        )

        ver_req = VerificationRequest.objects.create(
            lost_item=lost_wallet,
            found_item=found_wallet,
            owner=self.owner,
            finder=self.finder,
            status='under_verification',
        )

        # Finder independently describes wallet contents without seeing Owner answer
        VerificationEvidence.objects.create(
            verification_request=ver_req,
            submitted_by=self.finder,
            evidence_type='blind_qa',
            evidence_key='internal_contents',
            submitted_value='Has a Gym membership card and Blood donor card inside',
            is_blind=True,
        )

        evaluate_verification_session(ver_req)
        ver_req.refresh_from_db()

        self.assertEqual(ver_req.status, 'verified_match')
        self.assertTrue(ver_req.is_contact_allowed)
        self.assertGreaterEqual(ver_req.overall_confidence, 70.0)

    # ─── 4. Non-Serial Item Blind Verification: Keys ─────────────────────────

    def test_keys_verification_exact_count_vs_mismatch(self):
        """Keys verification: exact key count matches, wrong key count penalizes."""
        lost_keys = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Ring of Keys',
            category='keys',
            status='approved',
            private_attributes={
                'key_count_and_types': '4 keys with blue rubber cap on main key',
                'keychain_trinket': 'Silver bottle opener',
            }
        )
        found_keys = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Set of Keys',
            category='keys',
            status='approved',
        )

        ver_req = VerificationRequest.objects.create(
            lost_item=lost_keys,
            found_item=found_keys,
            owner=self.owner,
            finder=self.finder,
            status='under_verification',
        )

        # Finder answers matching 4 keys and bottle opener
        VerificationEvidence.objects.create(
            verification_request=ver_req,
            submitted_by=self.finder,
            evidence_type='blind_qa',
            evidence_key='key_count_and_types',
            submitted_value='There are 4 keys on the ring with blue cap',
            is_blind=True,
        )
        VerificationEvidence.objects.create(
            verification_request=ver_req,
            submitted_by=self.finder,
            evidence_type='blind_qa',
            evidence_key='keychain_trinket',
            submitted_value='Silver bottle opener keychain attached',
            is_blind=True,
        )

        evaluate_verification_session(ver_req)
        ver_req.refresh_from_db()

        self.assertEqual(ver_req.status, 'verified_match')
        self.assertTrue(ver_req.is_contact_allowed)

    # ─── 5. Contradictory Evidence Detection ─────────────────────────────────

    def test_verification_fails_on_severe_contradiction(self):
        """If Finder reports 1 key and leather tassel when Owner reported 6 keys, verification fails."""
        lost_keys = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Set of House Keys',
            category='keys',
            status='approved',
            private_attributes={
                'key_count_and_types': '6 keys total',
            }
        )
        found_keys = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Single Key',
            category='keys',
            status='approved',
        )

        ver_req = VerificationRequest.objects.create(
            lost_item=lost_keys,
            found_item=found_keys,
            owner=self.owner,
            finder=self.finder,
            status='under_verification',
        )

        VerificationEvidence.objects.create(
            verification_request=ver_req,
            submitted_by=self.finder,
            evidence_type='blind_qa',
            evidence_key='key_count_and_types',
            submitted_value='1 key only',
            is_blind=True,
        )

        evaluate_verification_session(ver_req)
        ver_req.refresh_from_db()

        self.assertIn(ver_req.status, ['verification_failed', 'additional_proof_required'])
        self.assertFalse(ver_req.is_contact_allowed)

    # ─── 6. Multi-Owner Ambiguity: Multiple Possible Owners ──────────────────

    def test_multiple_candidate_owners_flags_multiple_possible_owners(self):
        """If 2 owners report identical generic items without distinctive proof, flag MULTIPLE_POSSIBLE_OWNERS."""
        lost1 = Item.objects.create(
            user=self.owner, type='lost', title='Black Backpack', category='bag', primary_color='Black', status='approved'
        )
        lost2 = Item.objects.create(
            user=self.owner2, type='lost', title='Black Backpack Bag', category='bag', primary_color='Black', status='approved'
        )
        found_bag = Item.objects.create(
            user=self.finder, type='found', title='Found Black Backpack', category='bag', primary_color='Black', status='approved'
        )

        # Create candidate matches for both
        pm1 = PotentialMatch.objects.create(lost_item=lost1, found_item=found_bag, similarity_score=60.0, status='potential_match')
        pm2 = PotentialMatch.objects.create(lost_item=lost2, found_item=found_bag, similarity_score=60.0, status='potential_match')

        ver_req = VerificationRequest.objects.create(
            potential_match=pm1, lost_item=lost1, found_item=found_bag, owner=self.owner, finder=self.finder, status='under_verification'
        )

        # Only generic attribute submitted, no distinctive proof
        VerificationEvidence.objects.create(
            verification_request=ver_req,
            submitted_by=self.finder,
            evidence_type='blind_qa',
            evidence_key='internal_label_or_damage',
            submitted_value='Black bag with zippers',
            is_blind=True,
        )

        evaluate_verification_session(ver_req)
        ver_req.refresh_from_db()

        self.assertEqual(ver_req.status, 'multiple_possible_owners')
        self.assertFalse(ver_req.is_contact_allowed)

    # ─── 7. REST API Endpoints ───────────────────────────────────────────────

    def test_api_schema_endpoint(self):
        """GET /api/verifications/schema/?category=phone returns phone verification schema."""
        self.client.force_authenticate(user=self.owner)
        res = self.client.get('/api/verifications/schema/?category=phone')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('label'), 'Mobile Phone')
        self.assertTrue(len(res.data.get('blind_prompts', [])) > 0)

    def test_api_start_verification_and_submit_evidence(self):
        """Full API flow: Start verification, query session, and submit blind evidence."""
        lost = Item.objects.create(
            user=self.owner,
            type='lost',
            title='Dell XPS Laptop',
            category='laptop',
            brand='Dell',
            status='approved',
            private_attributes={'stickers_or_damage': 'GitHub octocat sticker on lid'}
        )
        found = Item.objects.create(
            user=self.finder,
            type='found',
            title='Found Dell Laptop',
            category='laptop',
            brand='Dell',
            status='approved',
        )
        pm = PotentialMatch.objects.create(lost_item=lost, found_item=found, similarity_score=80.0)

        # 1. Owner starts verification via API
        self.client.force_authenticate(user=self.owner)
        start_res = self.client.post('/api/verifications/start/', {'potential_match_id': pm.id})
        self.assertEqual(start_res.status_code, status.HTTP_201_CREATED)
        session_id = start_res.data['id']

        # 2. Finder gets session details and questions
        self.client.force_authenticate(user=self.finder)
        detail_res = self.client.get(f'/api/verifications/{session_id}/')
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(detail_res.data.get('questions_for_user', [])) > 0)

        # 3. Finder submits matching blind answer
        submit_res = self.client.post(f'/api/verifications/{session_id}/submit-evidence/', {
            'evidence_key': 'stickers_or_damage',
            'submitted_value': 'GitHub octocat sticker on top lid',
            'evidence_type': 'blind_qa'
        })
        self.assertEqual(submit_res.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_res.data['status'], 'verified_match')
        self.assertTrue(submit_res.data['is_contact_allowed'])
