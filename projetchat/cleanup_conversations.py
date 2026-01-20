# cleanup_conversations.py
# Exécuter avec: python manage.py shell < cleanup_conversations.py
# OU: python manage.py shell
# >>> exec(open('cleanup_conversations.py').read())

from messagerie.models import Conversation, Message, ConversationParticipant

print('🧹 Nettoyage de la base de données...')

# 1. Supprimer tous les messages
message_count = Message.objects.count()
Message.objects.all().delete()
print(f'✅ {message_count} messages supprimés')

# 2. Supprimer tous les participants
participant_count = ConversationParticipant.objects.count()
ConversationParticipant.objects.all().delete()
print(f'✅ {participant_count} participants supprimés')

# 3. Supprimer toutes les conversations
conversation_count = Conversation.objects.count()
Conversation.objects.all().delete()
print(f'✅ {conversation_count} conversations supprimées')

print('🎉 Nettoyage terminé !')