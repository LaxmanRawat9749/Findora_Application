import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findora_backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Item, Conversation, ChatMessage

owner, _ = User.objects.get_or_create(username='owner', defaults={'email': 'owner@test.com', 'role': 'owner'})
finder, _ = User.objects.get_or_create(username='finder', defaults={'email': 'finder@test.com', 'role': 'finder'})

item_lost = Item.objects.create(user=owner, type='lost', title='Lost Phone', status='approved', category='phone')
conv1, _ = Conversation.objects.get_or_create(item_id=item_lost.id, owner_id=owner.id, finder_id=finder.id)
msg1 = ChatMessage.objects.create(conversation=conv1, sender=finder, message='Hi!')
print(f"Conversation 1 created: {conv1.id}, Messages: {ChatMessage.objects.filter(conversation=conv1).count()}")
