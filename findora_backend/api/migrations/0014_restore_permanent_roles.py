from django.db import migrations, models


def restore_user_roles(apps, schema_editor):
    User = apps.get_model('api', 'User')
    Item = apps.get_model('api', 'Item')
    FinderReputation = apps.get_model('api', 'FinderReputation')

    for user in User.objects.all():
        if user.role == 'admin' or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            user.role = 'admin'
            user.save(update_fields=['role'])
            continue

        has_found = Item.objects.filter(user=user, type='found').exists()
        has_lost = Item.objects.filter(user=user, type='lost').exists()

        if has_found and not has_lost:
            user.role = 'finder'
        elif has_lost:
            user.role = 'owner'
        else:
            rep = FinderReputation.objects.filter(user=user).first()
            if rep and (rep.total_points > 0 or rep.successful_returns > 0):
                user.role = 'finder'
            else:
                user.role = 'owner'
        user.save(update_fields=['role'])


def reverse_restore_user_roles(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_convert_to_action_based_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('owner', 'Owner'), ('finder', 'Finder'), ('admin', 'Admin')], default='owner', max_length=10),
        ),
        migrations.RunPython(restore_user_roles, reverse_restore_user_roles),
    ]
