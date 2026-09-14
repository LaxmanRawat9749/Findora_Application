"""
Findora Universal Matching & Strong Ownership Verification Engine.

Implements:
  1. Stage 1: Multi-Attribute Candidate Matching Engine (Finds Potential Matches)
  2. Stage 2: Category-Specific Blind Discriminative Ownership Verification Evaluator
  3. Multi-Owner Ambiguity Resolution & Privacy Protection
"""

import math
import re
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone

from .models import (
    Item,
    Notification,
    PotentialMatch,
    VerificationEvidence,
    VerificationRequest,
)
from .verification_constants import (
    CATEGORY_VERIFICATION_SCHEMAS,
    DISCRIMINATIVE_WEIGHTS,
)


# ─── Text & Proximity Helpers ────────────────────────────────────────────────

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
    'from', 'of', 'my', 'i', 'is', 'it', 'was', 'this', 'that', 'near', 'lost',
    'found', 'item', 'please', 'help', 'contact', 'color', 'brand', 'black', 'white'
}


def _clean_tokens(text):
    """Tokenize and remove common stop words from a string."""
    if not text:
        return set()
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
    tokens = {w for w in cleaned.split() if len(w) > 2 and w not in STOPWORDS}
    return tokens


def _token_similarity(text1, text2):
    """Jaccard similarity between two texts."""
    t1 = _clean_tokens(text1)
    t2 = _clean_tokens(text2)
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0


def _haversine_km(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in km."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        r = 6371.0  # Earth radius in kilometers
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c
    except (ValueError, TypeError):
        return None


def are_categories_compatible(cat1, cat2):
    """Check if two category codes are compatible."""
    if not cat1 or not cat2:
        return False
    cat1, cat2 = cat1.lower().strip(), cat2.lower().strip()
    if cat1 == cat2:
        return True
    # Compatible category mappings
    aliases = {
        'documents': {'id_card', 'documents'},
        'id_card': {'id_card', 'documents'},
        'phone': {'phone', 'electronics'},
        'laptop': {'laptop', 'electronics'},
        'headphones': {'headphones', 'electronics'},
    }
    return cat2 in aliases.get(cat1, set()) or cat1 in aliases.get(cat2, set())


# ─── Stage 1: Multi-Attribute Candidate Matching Engine ──────────────────────

def compute_candidate_match_score(lost_item, found_item):
    """
    Computes a candidate similarity score (0.0 to 100.0) between a Lost Item and a Found Item.
    Produces match reasons and classifies candidate strength.
    """
    if not are_categories_compatible(lost_item.category, found_item.category):
        return 0.0, 'low', [], 'generic_candidate'

    score = 0.0
    match_reasons = []
    has_distinctive = False
    has_strong_id = False

    # 1. Category Match (Base weight: 20 pts)
    if lost_item.category == found_item.category:
        score += 20.0
        cat_label = lost_item.get_category_display() if hasattr(lost_item, 'get_category_display') else lost_item.category
        match_reasons.append(f"Category matched: {cat_label}")
    else:
        score += 12.0
        match_reasons.append(f"Compatible category: {lost_item.category} ↔ {found_item.category}")

    # 2. Brand & Model Match (Weight: up to 25 pts)
    lost_brand = (lost_item.brand or '').strip().lower()
    found_brand = (found_item.brand or '').strip().lower()
    lost_model = (lost_item.model_name or '').strip().lower()
    found_model = (found_item.model_name or '').strip().lower()

    if lost_brand and found_brand and (lost_brand in found_brand or found_brand in lost_brand):
        score += 15.0
        match_reasons.append(f"Brand matched: {lost_item.brand.title()}")
        if lost_model and found_model and (lost_model in found_model or found_model in lost_model):
            score += 10.0
            match_reasons.append(f"Model matched: {lost_item.model_name}")
            has_distinctive = True
    else:
        # Check brand in titles/descriptions
        title_tokens_lost = _clean_tokens(lost_item.title)
        title_tokens_found = _clean_tokens(found_item.title)
        common_title = title_tokens_lost & title_tokens_found
        if common_title:
            score += min(15.0, len(common_title) * 6.0)
            match_reasons.append(f"Matching title keywords: {', '.join(list(common_title)[:3])}")

    # 3. Color Matching (Weight: up to 15 pts)
    lost_p_color = (lost_item.primary_color or '').strip().lower()
    found_p_color = (found_item.primary_color or '').strip().lower()
    if lost_p_color and found_p_color:
        if lost_p_color == found_p_color:
            score += 10.0
            match_reasons.append(f"Primary color matched: {lost_p_color.title()}")
            lost_s_color = (lost_item.secondary_color or '').strip().lower()
            found_s_color = (found_item.secondary_color or '').strip().lower()
            if lost_s_color and found_s_color and lost_s_color == found_s_color:
                score += 5.0
                match_reasons.append(f"Secondary color matched: {lost_s_color.title()}")
                has_distinctive = True
    else:
        desc_sim = _token_similarity(lost_item.description, found_item.description)
        if desc_sim > 0.15:
            score += min(10.0, desc_sim * 20.0)

    # 4. Location Proximity (Weight: up to 20 pts)
    if lost_item.latitude and lost_item.longitude and found_item.latitude and found_item.longitude:
        dist_km = _haversine_km(lost_item.latitude, lost_item.longitude, found_item.latitude, found_item.longitude)
        if dist_km is not None:
            if dist_km <= 0.5:
                score += 20.0
                match_reasons.append(f"Exact location proximity (< 500m)")
                has_distinctive = True
            elif dist_km <= 2.0:
                score += 15.0
                match_reasons.append(f"Close location proximity ({dist_km:.1f} km)")
            elif dist_km <= 5.0:
                score += 10.0
                match_reasons.append(f"Nearby location ({dist_km:.1f} km)")
            elif dist_km <= 15.0:
                score += 5.0
                match_reasons.append(f"Same area ({dist_km:.1f} km)")
    elif lost_item.location and found_item.location:
        loc_sim = _token_similarity(lost_item.location, found_item.location)
        if loc_sim > 0.2:
            score += min(15.0, loc_sim * 20.0)
            match_reasons.append(f"Location text match: {lost_item.location}")

    # 5. Incident Date / Time Proximity (Weight: up to 15 pts)
    lost_time = lost_item.item_date or lost_item.reported_at
    found_time = found_item.item_date or found_item.reported_at
    if lost_time and found_time:
        time_diff = abs(found_time - lost_time)
        if time_diff <= timedelta(hours=6):
            score += 15.0
            match_reasons.append("Reported within 6 hours of incident")
        elif time_diff <= timedelta(days=1):
            score += 12.0
            match_reasons.append("Reported within 24 hours of incident")
        elif time_diff <= timedelta(days=3):
            score += 8.0
            match_reasons.append("Reported within 3 days")
        elif time_diff <= timedelta(days=7):
            score += 5.0
            match_reasons.append("Reported within 1 week")

    # 6. Direct Parent Item Linkage (Finder directly linked report)
    if found_item.parent_item_id == lost_item.id:
        score = max(score, 60.0) + 20.0
        match_reasons.insert(0, "Direct Finder report on this Owner listing")
        has_distinctive = True

    # 7. Optional Identifier Hash Overlap (Strong proof bonus)
    if lost_item.identifier_hash and found_item.identifier_hash:
        if lost_item.identifier_hash == found_item.identifier_hash:
            score += 25.0
            match_reasons.append("Exact Unique Identifier Hash Matched")
            has_strong_id = True

    # Final Score Normalization (0 - 100)
    final_score = min(100.0, max(0.0, score))

    if final_score >= 70.0:
        confidence = 'high'
    elif final_score >= 45.0:
        confidence = 'medium'
    else:
        confidence = 'low'

    if has_strong_id:
        strength = 'strong_identifier'
    elif has_distinctive or final_score >= 65.0:
        strength = 'distinctive_features'
    else:
        strength = 'generic_candidate'

    return final_score, confidence, match_reasons, strength


def run_candidate_matching_for_item(item):
    """
    Executes Stage 1 matching for an Item against all approved opposite-type items.
    Creates or updates PotentialMatch records.
    """
    if item.status not in ['approved', 'pending']:
        return []

    if item.type == 'lost':
        opposite_items = Item.objects.filter(type='found', status='approved').exclude(user=item.user)
    else:
        opposite_items = Item.objects.filter(type='lost', status='approved').exclude(user=item.user)

    potential_matches_created = []

    for opp_item in opposite_items:
        lost_item = item if item.type == 'lost' else opp_item
        found_item = opp_item if item.type == 'lost' else item

        score, confidence, reasons, strength = compute_candidate_match_score(lost_item, found_item)

        # Candidate threshold: minimum 35% similarity or direct parent link
        if score >= 35.0 or found_item.parent_item_id == lost_item.id:
            pm, created = PotentialMatch.objects.update_or_create(
                lost_item=lost_item,
                found_item=found_item,
                defaults={
                    'similarity_score': round(score, 1),
                    'confidence_level': confidence,
                    'match_reasons': reasons,
                    'evidence_strength': strength,
                    'status': 'potential_match',
                }
            )
            potential_matches_created.append(pm)

            # Update item verification_status to potential_match if currently unverified
            if lost_item.verification_status == 'unverified':
                lost_item.verification_status = 'potential_match'
                lost_item.save(update_fields=['verification_status'])
            if found_item.verification_status == 'unverified':
                found_item.verification_status = 'potential_match'
                found_item.save(update_fields=['verification_status'])

            # Send system notification to both users if new potential match is high/medium
            if created and confidence in ['high', 'medium']:
                target_user = found_item.user if item.type == 'lost' else lost_item.user
                Notification.objects.get_or_create(
                    user=target_user,
                    type='match',
                    related_item=opp_item,
                    message=f"Possible match found for your item '{target_user.username}'! Strong verification required."
                )

    return potential_matches_created


# ─── Stage 2: Strong Blind Discriminative Ownership Verification ─────────────

def get_category_schema_for_item(category_key):
    """Retrieve category verification schema with fallback to 'other'."""
    normalized_key = category_key.lower().strip() if category_key else 'other'
    if normalized_key == 'id_card':
        normalized_key = 'documents'
    return CATEGORY_VERIFICATION_SCHEMAS.get(normalized_key, CATEGORY_VERIFICATION_SCHEMAS['other'])


def evaluate_verification_session(verification_request):
    """
    Stage 2 Discriminative Verification Engine.
    Evaluates submitted blind evidence, compares against Owner private attributes,
    calculates discriminative confidence, checks for multiple-owner ambiguity,
    and updates the session status.
    """
    lost_item = verification_request.lost_item
    found_item = verification_request.found_item
    owner = verification_request.owner
    finder = verification_request.finder

    evidence_list = list(verification_request.evidence_submissions.all())
    owner_evidence = [e for e in evidence_list if e.submitted_by_id == owner.id]
    finder_evidence = [e for e in evidence_list if e.submitted_by_id == finder.id]

    category = lost_item.category.lower().strip() if lost_item.category else 'other'
    if category == 'id_card':
        category = 'documents'

    category_schema = get_category_schema_for_item(category)

    # 1. Candidate Baseline: Candidate matching attributes (category, brand, model, color, proximity)
    candidate_score, _, _, _ = compute_candidate_match_score(lost_item, found_item)
    baseline_pts = min(35.0, candidate_score * 0.4)
    score = baseline_pts
    summary_points = []
    if baseline_pts > 0:
        summary_points.append(f"Candidate matching baseline (+{baseline_pts:.0f} pts)")

    has_strong_discriminator = False
    has_severe_contradiction = False

    # 2. Check Owner Private Attributes stored at lost-report creation
    private_attrs = lost_item.private_attributes or {}

    # Map finder submitted evidence by key
    finder_by_key = {e.evidence_key: e for e in finder_evidence}
    owner_by_key = {e.evidence_key: e for e in owner_evidence}

    # Evaluate each schema prompt
    for prompt in category_schema.get('blind_prompts', []):
        key = prompt['key']
        finder_sub = finder_by_key.get(key)
        owner_sub = owner_by_key.get(key)
        stored_private_val = private_attrs.get(key)

        owner_text = (owner_sub.submitted_value if owner_sub else '') or str(stored_private_val or '')
        finder_text = finder_sub.submitted_value if finder_sub else ''

        if finder_text and owner_text:
            sim = _token_similarity(owner_text, finder_text)
            weight_type = prompt.get('weight', 'unique_damage')
            weight_val = DISCRIMINATIVE_WEIGHTS.get(weight_type, 30.0)

            if key == 'key_count_and_types':
                # Special numeric check for keys
                finder_nums = re.findall(r'\b\d+\b', finder_text)
                owner_nums = re.findall(r'\b\d+\b', owner_text)
                if finder_nums and owner_nums and finder_nums[0] == owner_nums[0]:
                    score += 40.0
                    summary_points.append(f"Exact key count matched: {finder_nums[0]} keys (+40 pts)")
                    has_strong_discriminator = True
                    if finder_sub: finder_sub.match_result = 'matched'; finder_sub.save(update_fields=['match_result'])
                    if owner_sub: owner_sub.match_result = 'matched'; owner_sub.save(update_fields=['match_result'])
                elif finder_nums and owner_nums and finder_nums[0] != owner_nums[0]:
                    score += DISCRIMINATIVE_WEIGHTS['contradiction_penalty']
                    summary_points.append(f"Contradictory key count: Finder stated {finder_nums[0]}, Owner stated {owner_nums[0]}")
                    has_severe_contradiction = True
                    if finder_sub: finder_sub.match_result = 'mismatched'; finder_sub.save(update_fields=['match_result'])
            elif sim >= 0.20:
                earned = max(35.0, weight_val * min(1.2, sim * 2.0))
                score += earned
                summary_points.append(f"Blind answer matched on {key.replace('_', ' ')} (+{earned:.0f} pts)")
                has_strong_discriminator = True
                if finder_sub: finder_sub.match_result = 'matched'; finder_sub.save(update_fields=['match_result'])
                if owner_sub: owner_sub.match_result = 'matched'; owner_sub.save(update_fields=['match_result'])
            elif sim < 0.05 and len(_clean_tokens(finder_text)) >= 3 and len(_clean_tokens(owner_text)) >= 3:
                # Contradiction
                score -= 20.0
                summary_points.append(f"Divergent descriptions on {key.replace('_', ' ')}")
                if finder_sub: finder_sub.match_result = 'mismatched'; finder_sub.save(update_fields=['match_result'])
            else:
                score += 5.0
                if finder_sub: finder_sub.match_result = 'inconclusive'; finder_sub.save(update_fields=['match_result'])

    # 3. Check Photo Proof or Purchase Receipt submissions
    photo_receipt_evidence = [
        e for e in owner_evidence
        if e.evidence_type in ['photo_proof', 'purchase_receipt'] or e.submitted_image
    ]
    if photo_receipt_evidence:
        score += 35.0
        summary_points.append("Owner provided verified previous photo / purchase receipt (+35 pts)")
        has_strong_discriminator = True
        for e in photo_receipt_evidence:
            e.match_result = 'matched'
            e.save(update_fields=['match_result'])

    # 4. Check Identifier Overlap (if applicable)
    id_evidence = [e for e in owner_evidence if e.evidence_type == 'identifier_check']
    if id_evidence:
        for e in id_evidence:
            owner_val = (e.submitted_value or '').strip().lower()
            finder_val = (found_item.identifier_masked or '').strip().lower()
            if owner_val and (owner_val == finder_val or (lost_item.identifier_hash and lost_item.identifier_hash == found_item.identifier_hash)):
                score += 50.0
                summary_points.append("Exact identifier / serial number confirmed (+50 pts)")
                has_strong_discriminator = True
                e.match_result = 'matched'
                e.save(update_fields=['match_result'])

    # 5. Check Multiple Owner Ambiguity
    competing_lost_items = PotentialMatch.objects.filter(
        found_item=found_item,
        status__in=['potential_match', 'under_verification']
    ).exclude(lost_item=lost_item)

    is_ambiguous_multiple = False
    if competing_lost_items.count() >= 1 and not has_strong_discriminator and score < 65.0:
        is_ambiguous_multiple = True

    final_confidence = min(100.0, max(0.0, score))
    verification_request.overall_confidence = round(final_confidence, 1)

    # 6. Lifecycle Decision Logic
    if has_severe_contradiction and final_confidence < 30.0:
        new_status = 'verification_failed'
        verification_request.is_contact_allowed = False
        summary_points.insert(0, "Ownership Verification Failed: Contradicting evidence submitted.")
    elif is_ambiguous_multiple:
        new_status = 'multiple_possible_owners'
        verification_request.is_contact_allowed = False
        summary_points.insert(0, "Multiple Candidate Owners Detected: Additional ownership proof required.")
    elif final_confidence >= 65.0 and has_strong_discriminator:
        new_status = 'verified_match'
        verification_request.is_contact_allowed = True
        verification_request.verified_at = timezone.now()
        summary_points.insert(0, "Ownership Verified Successfully! Contact and return handoff unlocked.")

        # Update associated items and potential match
        lost_item.verification_status = 'verified_match'
        lost_item.save(update_fields=['verification_status'])
        found_item.verification_status = 'verified_match'
        found_item.save(update_fields=['verification_status'])
        if verification_request.potential_match:
            verification_request.potential_match.status = 'verified'
            verification_request.potential_match.save(update_fields=['status'])

        # Notify both users
        Notification.objects.create(
            user=owner,
            type='verification',
            related_item=lost_item,
            message=f"Ownership verified for '{lost_item.title}'! You can now contact the finder to arrange return."
        )
        Notification.objects.create(
            user=finder,
            type='verification',
            related_item=found_item,
            message=f"Ownership verified for '{found_item.title}' with owner {owner.username}. Chat is now unlocked."
        )
    else:
        new_status = 'additional_proof_required'
        verification_request.is_contact_allowed = False
        summary_points.insert(0, "Additional Ownership Proof Required: Evidence is not sufficiently discriminative.")

    verification_request.status = new_status
    verification_request.verification_summary = "\n• " + "\n• ".join(summary_points)
    verification_request.save(update_fields=['status', 'overall_confidence', 'verification_summary', 'is_contact_allowed', 'verified_at', 'updated_at'])

    return verification_request
