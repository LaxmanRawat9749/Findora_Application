from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Q


class Command(BaseCommand):
    help = "Mark a user as verified (is_verified=True) by username or email"

    def add_arguments(self, parser):
        parser.add_argument('identifier', type=str, help='Username or Email of the user to verify')

    def handle(self, *args, **options):
        User = get_user_model()
        identifier = options['identifier']

        users = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        if not users.exists():
            raise CommandError(f"No user found matching username or email '{identifier}'")

        for user in users:
            user.is_verified = True
            user.is_active = True
            user.is_locked = False
            user.failed_login_attempts = 0
            user.save(update_fields=['is_verified', 'is_active', 'is_locked', 'failed_login_attempts'])
            self.stdout.write(
                self.style.SUCCESS(f"User '{user.username}' (email: {user.email}, role: {user.role}) is now verified and active.")
            )
