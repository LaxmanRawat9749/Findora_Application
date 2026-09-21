from .models import Item, MatchedItem


def admin_sidebar_stats(request):
    """
    Provide live count metrics for the Django admin sidebar and header navigation.
    Ensures badges (Lost, Found, Potential Matches, Resolved Matches, Pending Reviews)
    remain synchronized and accurate on every admin page.
    """
    if getattr(request, 'path', '').startswith('/admin/'):
        try:
            total_lost = Item.objects.filter(type='lost').count()
            total_found = Item.objects.filter(type='found').count()
            potential_matches = MatchedItem.objects.filter(status='pending').count()
            resolved_matches = MatchedItem.objects.filter(status='resolved').count()
            pending_reviews = Item.objects.filter(status='pending').count()

            return {
                'total_lost': total_lost,
                'total_found': total_found,
                'potential_matches_count': potential_matches,
                'resolved_matches_count': resolved_matches,
                'pending_reviews': pending_reviews,
            }
        except Exception:
            return {}
    return {}
