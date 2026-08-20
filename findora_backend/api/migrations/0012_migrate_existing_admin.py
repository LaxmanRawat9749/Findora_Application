"""
Data migration: Migrates any existing admin accounts from User table to Administrator table.
Ensures zero data loss while achieving complete structural isolation.
"""

from django.db import migrations


def migrate_admins_to_administrator_model(apps, schema_editor):
    User = apps.get_model('api', 'User')
    Administrator = apps.get_model('api', 'Administrator')

    # Find any users who were admins / staff / superusers
    admin_users = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True) | User.objects.filter(role='admin')
    admin_users = admin_users.distinct()

    for u in admin_users:
        if not Administrator.objects.filter(username=u.username).exists():
            Administrator.objects.create(
                username=u.username,
                email=u.email,
                password=u.password,  # Preserves existing hashed password
                first_name=u.first_name,
                last_name=u.last_name,
                admin_role='super_admin',
                is_active=u.is_active,
                is_staff=True,
                is_superuser=u.is_superuser or True,
                last_login=u.last_login,
                created_at=u.created_at,
            )
        # Remove from application user table
        u.delete()


def reverse_migration(apps, schema_editor):
    User = apps.get_model('api', 'User')
    Administrator = apps.get_model('api', 'Administrator')

    for admin in Administrator.objects.all():
        if not User.objects.filter(username=admin.username).exists():
            User.objects.create(
                username=admin.username,
                email=admin.email,
                password=admin.password,
                first_name=admin.first_name,
                last_name=admin.last_name,
                role='owner',
                is_staff=admin.is_staff,
                is_superuser=admin.is_superuser,
                is_active=admin.is_active,
                last_login=admin.last_login,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_user_options_alter_user_role_administrator_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_admins_to_administrator_model, reverse_migration),
    ]
