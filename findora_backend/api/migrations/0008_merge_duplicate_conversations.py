from django.db import migrations

def merge_duplicate_conversations(apps, schema_editor):
    Conversation = apps.get_model('api', 'Conversation')
    ChatMessage = apps.get_model('api', 'ChatMessage')
    
    conversations = list(Conversation.objects.all())
    user_pairs = {}
    
    for conv in conversations:
        pair = tuple(sorted([conv.owner_id, conv.finder_id]))
        if pair not in user_pairs:
            user_pairs[pair] = []
        user_pairs[pair].append(conv)
        
    for pair, conv_list in user_pairs.items():
        if len(conv_list) > 1:
            conv_list.sort(key=lambda x: x.created_at)
            primary_conv = conv_list[0]
            
            for other_conv in conv_list[1:]:
                ChatMessage.objects.filter(conversation_id=other_conv.id).update(conversation_id=primary_conv.id)
                other_conv.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_chatmessage_caption_chatmessage_image_and_more'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_conversations, reverse_code=migrations.RunPython.noop),
    ]
