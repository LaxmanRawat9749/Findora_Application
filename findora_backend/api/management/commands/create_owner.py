from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create a verified Owner user"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='owner', help='Username for the owner user')
        parser.add_argument('--email', type=str, default='owner@findora.com', help='Email for the owner user')
        parser.add_argument('--password', type=str, default='Owner123!', help='Password for the owner user')
        parser.add_argument('--first_name', type=str, default='Findora', help='First name')
        parser.add_argument('--last_name', type=str, default='Owner', help='Last name')
        parser.add_argument('--phone', type=str, default='9800000000', help='Phone number')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone = options['phone']

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.role = 'owner'
            user.is_verified = True
            user.is_active = True
            user.set_password(password)
            user.email = email
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Existing user '{username}' updated to verified Owner with password '{password}'")
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role='owner',
                is_verified=True,
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Verified Owner created successfully: username='{username}', password='{password}'")
            )
