from rest_framework import serializers
from messagerie.models.message_status import MessageStatus

class MessageStatusSerializer(serializers.ModelSerializer):
    """
    Serializer de base pour MessageStatus
    """
    class Meta:
        model = MessageStatus
        fields = [
            'id',
            'message',
            'user',
            'status',
            'created_at',
            'delivered_at',
            'read_at',
        ]


class MessageStatusListSerializer(serializers.ModelSerializer):
    """
    Serializer pour lister les MessageStatus avec infos utilisateur
    """
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)

    class Meta:
        model = MessageStatus
        fields = [
            'id',
            'message',
            'user',
            'user_display_name',
            'status',
            'created_at',
            'delivered_at',
            'read_at',
        ]


class MessageStatusDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour un MessageStatus
    """
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)
    message_content = serializers.CharField(source='message.content', read_only=True)

    class Meta:
        model = MessageStatus
        fields = [
            'id',
            'message',
            'message_content',
            'user',
            'user_display_name',
            'status',
            'created_at',
            'delivered_at',
            'read_at',
        ]


class MessageStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour le status d'un message
    """
    class Meta:
        model = MessageStatus
        fields = ['status']
