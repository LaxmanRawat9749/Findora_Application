from django.db import migrations, models


def migrate_to_dynamic_roles(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.all():
        if user.role == 'admin' or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            user.role = 'admin'
        else:
            user.role = 'user'
        user.save(update_fields=['role'])


def reverse_dynamic_roles(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_restore_permanent_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('user', 'User'), ('admin', 'Admin'), ('owner', 'Owner'), ('finder', 'Finder')],
                default='user',
                max_length=10
            ),
        ),
        migrations.RunPython(migrate_to_dynamic_roles, reverse_dynamic_roles),
    ]
