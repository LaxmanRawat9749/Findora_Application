"""
Service layer for Findora Reputation and Points System.

Provides atomic, idempotent operations for:
  - Point awards (found reports, returns, ratings, admin adjustments)
  - Duplicate protection at the transaction level
  - Badge evaluations and unlocks
  - Owner ratings and reputation updates
  - Notification dispatches
"""

import logging
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Conversation,
    FinderRating,
    FinderReputation,
    Item,
    Notification,
    PointTransaction,
    User,
    UserBadge,
)
from .reputation_constants import (
    BADGES,
    POINTS_FOUND_REPORT,
    POINTS_POSITIVE_RATING,
    POINTS_SUCCESSFUL_RETURN,
    TX_ADMIN_ADJUSTMENT,
    TX_FOUND_REPORT,
    TX_POSITIVE_RATING,
    TX_SUCCESSFUL_RETURN,
)

logger = logging.getLogger(__name__)


def get_or_create_reputation(user):
    """
    Get or create FinderReputation for a user with accurate default fields.
    """
    rep, _ = FinderReputation.objects.get_or_create(user=user)
    return rep


@transaction.atomic
def award_found_report_points(finder, item):
    """
    Awards +5 points to the Finder when they create a valid Found Item report.
    Guarded against duplicate points (idempotent per item).
    Only users with role='finder' receive points.
    """
    if not finder or getattr(finder, 'role', '') != 'finder' or not item:
        return False

    # Check if reward was already processed for this item report
    already_awarded = PointTransaction.objects.filter(
        user=finder,
        related_item=item,
        transaction_type=TX_FOUND_REPORT,
    ).exists()

    if already_awarded:
        return False

    PointTransaction.objects.create(
        user=finder,
        points=POINTS_FOUND_REPORT,
        transaction_type=TX_FOUND_REPORT,
        description=f'Found item report: "{item.title}"',
        related_item=item,
    )

    rep = get_or_create_reputation(finder)
    rep.total_points += POINTS_FOUND_REPORT
    rep.save(update_fields=['total_points', 'updated_at'])

    Notification.objects.create(
        user=finder,
        type='reputation',
        message=(
            f'🎉 You earned {POINTS_FOUND_REPORT} Findora Points for reporting '
            f'found item "{item.title}".\nTotal Points: {rep.total_points}'
        ),
        related_item=item,
    )

    return True


@transaction.atomic
def process_successful_return_reward(finder, owner, item):
    """
    Awards +100 points, increments successful returns count, evaluates badges,
    and sends notifications upon confirmed return completion.
    Strictly idempotent to prevent duplicate points.
    Points, returns, and badges belong ONLY to Finders (role='finder').
    """
    if not finder or getattr(finder, 'role', '') != 'finder' or not item:
        return False

    # Check if return reward was already processed for this item
    already_awarded = PointTransaction.objects.filter(
        user=finder,
        related_item=item,
        transaction_type=TX_SUCCESSFUL_RETURN,
    ).exists()

    if already_awarded:
        logger.warning(
            f"Attempted duplicate return points award for user {finder.id} and item {item.id}"
        )
        return False

    # 1. Create Point Transaction (+100)
    PointTransaction.objects.create(
        user=finder,
        points=POINTS_SUCCESSFUL_RETURN,
        transaction_type=TX_SUCCESSFUL_RETURN,
        description=f'Successful return of "{item.title}"',
        related_item=item,
    )

    # 2. Update Finder Reputation
    rep = get_or_create_reputation(finder)
    rep.total_points += POINTS_SUCCESSFUL_RETURN
    rep.successful_returns += 1
    rep.save(update_fields=['total_points', 'successful_returns', 'updated_at'])

    # 3. Evaluate Badges
    check_and_award_badges(finder, rep)

    # 4. Notify Finder
    Notification.objects.create(
        user=finder,
        type='reputation',
        message=(
            f"🎉 You earned {POINTS_SUCCESSFUL_RETURN} Findora Points!\n\n"
            f"Your successful return of '{item.title}' has been confirmed.\n\n"
            f"Total Points: {rep.total_points}"
        ),
        related_item=item,
    )

    # 5. Notify Owner to Rate the Finder (Owner receives NO points or reputation)
    if owner:
        Notification.objects.create(
            user=owner,
            type='rating',
            message=(
                f"⭐ Rate your Finder\n\n"
                f"Your item '{item.title}' has been successfully returned."
            ),
            related_item=item,
        )

    return True


def check_and_award_badges(user, rep=None):
    """
    Checks if the user has reached thresholds for any badges and awards them.
    Guarantees no duplicate badge awards.
    Badges belong ONLY to Finders (role='finder').
    """
    if not user or getattr(user, 'role', '') != 'finder':
        return []

    if rep is None:
        rep = get_or_create_reputation(user)

    returns_count = rep.successful_returns
    newly_awarded = []

    for badge in BADGES:
        if returns_count >= badge['required_returns']:
            obj, created = UserBadge.objects.get_or_create(
                user=user,
                badge_key=badge['key'],
                defaults={
                    'name': badge['name'],
                    'description': badge['description'],
                    'required_returns': badge['required_returns'],
                    'icon': badge['icon'],
                },
            )
            if created:
                newly_awarded.append(obj)
                Notification.objects.create(
                    user=user,
                    type='badge',
                    message=(
                        f"🏆 New Achievement!\n\n"
                        f"You earned the {badge['name']} badge.\n"
                        f"{badge['required_returns']} successful returns completed."
                    ),
                )

    return newly_awarded


@transaction.atomic
def submit_finder_rating(owner, item, rating_value, review_text=''):
    """
    Submits a rating for a Finder by an Owner on a resolved item.
    - Available ONLY after successful return (item.status == 'resolved')
    - Only Owner can rate Finder
    - Ensures valid rating (1-5)
    - Prevents self-rating and duplicate rating
    - Updates Finder's average rating
    - Awards +10 points to Finder if rating is 4 or 5 stars
    - Owner receives NO points and NO reputation
    """
    try:
        rating_value = int(rating_value)
    except (ValueError, TypeError):
        raise ValueError("Rating must be an integer between 1 and 5.")

    if rating_value < 1 or rating_value > 5:
        raise ValueError("Rating must be between 1 and 5.")

    if item.status != 'resolved':
        raise ValueError("Cannot rate before the item return is completed.")

    # Determine Finder
    finder = None
    if item.type == 'lost':
        # For a lost item: Owner is item.user, Finder is the return partner
        if item.user != owner and getattr(owner, 'role', '') != 'owner':
            raise ValueError("Only the owner who lost the item can rate the finder.")
        return_tx = PointTransaction.objects.filter(
            related_item=item,
            transaction_type=TX_SUCCESSFUL_RETURN,
        ).first()
        if return_tx:
            finder = return_tx.user
        else:
            conv = Conversation.objects.filter(item=item).first()
            if conv:
                finder = conv.finder
    else:
        # For a found item: Reporter is the Finder, Owner is the claim/conversation partner
        finder = item.user

    if not finder:
        raise ValueError("Could not determine the finder for this item.")

    if getattr(finder, 'role', '') != 'finder':
        raise ValueError("Ratings can only be submitted for Finders.")

    if owner.id == finder.id:
        raise ValueError("You cannot rate yourself.")

    # Prevent duplicate rating
    if FinderRating.objects.filter(owner=owner, item=item).exists():
        raise ValueError("Rating already submitted.")

    # 1. Create FinderRating
    rating_obj = FinderRating.objects.create(
        owner=owner,
        finder=finder,
        item=item,
        rating=rating_value,
        review=review_text.strip() if review_text else '',
    )

    # 2. Update Finder's Reputation Stats
    rep = get_or_create_reputation(finder)
    rep.rating_count += 1
    rep.rating_sum += rating_value
    rep.average_rating = round(rep.rating_sum / rep.rating_count, 1)
    rep.save(update_fields=['rating_count', 'rating_sum', 'average_rating', 'updated_at'])

    # 3. Positive rating bonus (+10 points for 4 or 5 stars awarded to Finder)
    if rating_value >= 4:
        already_has_rating_bonus = PointTransaction.objects.filter(
            user=finder,
            related_item=item,
            transaction_type=TX_POSITIVE_RATING,
        ).exists()

        if not already_has_rating_bonus:
            PointTransaction.objects.create(
                user=finder,
                points=POINTS_POSITIVE_RATING,
                transaction_type=TX_POSITIVE_RATING,
                description=f'Positive {rating_value}-star rating for "{item.title}"',
                related_item=item,
            )
            rep.total_points += POINTS_POSITIVE_RATING
            rep.save(update_fields=['total_points', 'updated_at'])

    # 4. Notify Finder
    bonus_text = f" (+{POINTS_POSITIVE_RATING} Points)" if rating_value >= 4 else ""
    owner_display = owner.get_full_name() or owner.username
    Notification.objects.create(
        user=finder,
        type='rating',
        message=(
            f"⭐ You received a {rating_value}-star rating from {owner_display} "
            f"for '{item.title}'!{bonus_text}"
        ),
        related_item=item,
    )

    return rating_obj


def get_badge_progress_list(user):
    """
    Returns full badge catalog with user's earned status and progress details.
    Badges belong ONLY to Finders.
    """
    if not user or getattr(user, 'role', '') != 'finder':
        return []

    rep = get_or_create_reputation(user)
    earned_badge_keys = set(
        UserBadge.objects.filter(user=user).values_list('badge_key', flat=True)
    )

    badges_data = []
    for b in BADGES:
        is_earned = b['key'] in earned_badge_keys
        req = b['required_returns']
        cur = min(rep.successful_returns, req)
        progress_text = f"{cur} / {req}" if not is_earned else "Completed ✓"
        progress_percent = int((cur / req) * 100) if req > 0 else 100

        badges_data.append({
            'badge_key': b['key'],
            'name': b['name'],
            'description': b['description'],
            'icon': b['icon'],
            'required_returns': req,
            'is_earned': is_earned,
            'current_progress': cur,
            'progress_text': progress_text,
            'progress_percent': progress_percent,
        })

    return badges_data


@transaction.atomic
def admin_adjust_points(user, points, reason, admin_user=None):
    """
    Performs an administrative point adjustment with mandatory audit reason.
    Points belong ONLY to Finders.
    """
    if getattr(user, 'role', '') != 'finder':
        raise ValueError("Points can only be adjusted for Finders.")

    if not reason or not reason.strip():
        raise ValueError("A reason is required for administrative point adjustments.")

    points = int(points)
    admin_name = admin_user.username if admin_user else "Admin"

    tx = PointTransaction.objects.create(
        user=user,
        points=points,
        transaction_type=TX_ADMIN_ADJUSTMENT,
        description=f"Admin adjustment by {admin_name}: {reason.strip()}",
    )

    rep = get_or_create_reputation(user)
    rep.total_points += points
    rep.save(update_fields=['total_points', 'updated_at'])

    sign = "+" if points > 0 else ""
    Notification.objects.create(
        user=user,
        type='reputation',
        message=f"Findora Points adjusted: {sign}{points} Points.\nReason: {reason.strip()}",
    )

    return tx
