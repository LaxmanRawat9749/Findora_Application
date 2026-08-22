"""
Constants and configurations for Findora Reputation and Points System.
"""

# ─── Point Values ─────────────────────────────────────────────────────────────
POINTS_FOUND_REPORT = 5
POINTS_SUCCESSFUL_RETURN = 100
POINTS_POSITIVE_RATING = 10

# ─── Point Transaction Types ──────────────────────────────────────────────────
TX_FOUND_REPORT = 'FOUND_REPORT'
TX_SUCCESSFUL_RETURN = 'SUCCESSFUL_RETURN'
TX_POSITIVE_RATING = 'POSITIVE_RATING'
TX_MILESTONE_BONUS = 'MILESTONE_BONUS'
TX_ADMIN_ADJUSTMENT = 'ADMIN_ADJUSTMENT'
TX_PENALTY = 'PENALTY'

TRANSACTION_TYPE_CHOICES = [
    (TX_FOUND_REPORT, 'Found Item Report'),
    (TX_SUCCESSFUL_RETURN, 'Successful Return'),
    (TX_POSITIVE_RATING, 'Positive Owner Rating'),
    (TX_MILESTONE_BONUS, 'Milestone Bonus'),
    (TX_ADMIN_ADJUSTMENT, 'Admin Adjustment'),
    (TX_PENALTY, 'Penalty'),
]

# ─── Badges / Achievements ────────────────────────────────────────────────────
# Evaluated primarily on successful return counts
BADGES = [
    {
        'key': 'FIRST_RETURN',
        'name': 'First Return',
        'description': 'Completed your first successful return',
        'required_returns': 1,
        'icon': '🌱',
    },
    {
        'key': 'HELPFUL_FINDER',
        'name': 'Helpful Finder',
        'description': 'Completed 5 successful returns',
        'required_returns': 5,
        'icon': '🤝',
    },
    {
        'key': 'TRUSTED_FINDER',
        'name': 'Trusted Finder',
        'description': 'Completed 10 successful returns',
        'required_returns': 10,
        'icon': '⭐',
    },
    {
        'key': 'COMMUNITY_HERO',
        'name': 'Community Hero',
        'description': 'Completed 25 successful returns',
        'required_returns': 25,
        'icon': '🏆',
    },
    {
        'key': 'FINDORA_HERO',
        'name': 'Findora Hero',
        'description': 'Completed 50 successful returns',
        'required_returns': 50,
        'icon': '👑',
    },
]
