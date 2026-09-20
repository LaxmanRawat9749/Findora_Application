from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create admin user"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser(
                username="admin",
                email="admin@findora.com",
                password="admin123"
            )
            admin_user.role = 'admin'
            admin_user.is_verified = True
            admin_user.save(update_fields=['role', 'is_verified'])

            self.stdout.write(
                self.style.SUCCESS("Admin created successfully")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Admin already exists")
            )