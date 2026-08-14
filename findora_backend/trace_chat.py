import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findora_backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Item, Conversation, ChatMessage

print("=== STARTING TRACE ===")

# 1. Owner creates ONE lost item: Phone
owner, _ = User.objects.get_or_create(username='owner_user', defaults={'email': 'owner@test.com', 'role': 'owner'})
finder, _ = User.objects.get_or_create(username='finder_user', defaults={'email': 'finder@test.com', 'role': 'finder'})

phone_lost = Item.objects.create(user=owner, type='lost', title='Lost Phone', status='approved', category='phone')
print(f"1. Owner created Phone. Item ID: {phone_lost.id}, Type: {phone_lost.type}, Poster: {phone_lost.user.username}")

# 3. Finder goes: Lost -> Phone -> Contact Owner
# 4. Finder sends: "Hi!"
conv_lost, _ = Conversation.objects.get_or_create(item_id=phone_lost.id, owner_id=owner.id, finder_id=finder.id)
msg = ChatMessage.objects.create(conversation=conv_lost, sender=finder, message='Hi!')
print(f"2. Finder contacted Owner. Conversation ID: {conv_lost.id}. Message ID: {msg.id}")

print("=== STEP 1 - VERIFY DATABASE ===")
print(f"Message ID: {msg.id}")
print(f"Sender ID: {msg.sender.id} ({msg.sender.username})")
# receiver is whoever is the other user in conversation
receiver_id = conv_lost.owner_id if msg.sender.id == conv_lost.finder_id else conv_lost.finder_id
print(f"Receiver ID: {receiver_id} ({User.objects.get(id=receiver_id).username})")
print(f"Item ID: {conv_lost.item_id}")
print(f"Conversation ID: {conv_lost.id}")
print(f"Message Text: {msg.message}")

print("=== VERIFY OWNER CONTACT FINDER ===")
# "8. Owner then goes DIRECTLY to: Found -> Phone -> Contact Finder"
# Wait, if Owner goes to "Found -> Phone", they MUST be opening a DIFFERENT item that has type='found'.
# Let's verify if an item with type='lost' can even be shown under "Found".
# No, we already know the query filters by type='found'. 
# So there MUST be a second item that the Finder posted, or the Owner is opening a completely different item.
# But let's assume the user means: The Finder ALSO posted a Found Phone.
phone_found = Item.objects.create(user=finder, type='found', title='Found Phone', status='approved', category='phone')
print(f"Assumption: Finder posted Found Phone. Item ID: {phone_found.id}")

# Owner clicks "Contact Finder" on phone_found
print(f"Owner clicks Contact Finder on Item ID: {phone_found.id}")

# In ConversationInitView, it will check for phone_found.id
# Let's call the logic:
item = phone_found
request_user = owner

if item.type == 'lost':
    owner_user = item.user
    finder_user = request_user
else:
    owner_user = request_user
    finder_user = item.user

from django.db.models import Q
conversation = Conversation.objects.filter(
    Q(item_id=item.id) & (
        (Q(owner_id=owner_user.id) & Q(finder_id=finder_user.id)) |
        (Q(owner_id=finder_user.id) & Q(finder_id=owner_user.id))
    )
).first()

if not conversation:
    conversation = Conversation.objects.create(
        item_id=item.id,
        owner_id=owner_user.id,
        finder_id=finder_user.id
    )

print(f"ConversationInitView returned Conversation ID: {conversation.id} for Item ID: {phone_found.id}")

# Now ChatActivity calls getMessages(conversationId)
messages = ChatMessage.objects.filter(conversation=conversation)
print(f"Messages returned for Conversation {conversation.id}: {messages.count()}")
for m in messages:
    print(f"- {m.message}")

print("=== SUMMARY ===")
print(f"Message 'Hi!' is stored in Conversation {conv_lost.id} (Item {conv_lost.item_id})")
print(f"Contact Finder passes Item ID {phone_found.id}")
print(f"ConversationInitView returns Conversation {conversation.id}")
print(f"ChatListView returns {messages.count()} messages.")

