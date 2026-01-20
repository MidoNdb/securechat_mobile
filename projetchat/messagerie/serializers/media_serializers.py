from rest_framework import serializers
from messagerie.models.media import Media
from messagerie.models.message import Message
from messagerie.models.conversation import ConversationParticipant


class MediaListSerializer(serializers.ModelSerializer):
    """
    Serializer optimisé pour la liste des médias
    """
    size_mb = serializers.FloatField(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = Media
        fields = [
            'id',
            'message',
            'type',
            'encrypted_file_url',
            'encrypted_thumbnail_url',
            'file_size',
            'size_mb',
            'duration',
            'duration_formatted',
            'width',
            'height',
            'is_uploaded',
            'upload_progress',
            'created_at',
            'uploaded_at'
        ]


class MediaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour un média (avec toutes les métadonnées)
    """
    size_mb = serializers.FloatField(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    message_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = [
            'id',
            'message',
            'message_info',
            'type',
            'encrypted_file_url',
            'encrypted_thumbnail_url',
            'encrypted_filename',
            'encrypted_metadata',
            'file_size',
            'size_mb',
            'duration',
            'duration_formatted',
            'width',
            'height',
            'is_uploaded',
            'upload_progress',
            'created_at',
            'uploaded_at'
        ]
    
    def get_message_info(self, obj):
        """Infos du message parent"""
        return {
            'id': str(obj.message.id),
            'conversation_id': str(obj.message.conversation.id),
            'sender_id': str(obj.message.from_user.user_id),
            'sender_name': obj.message.from_user.display_name
        }


class MediaCreateSerializer(serializers.Serializer):
    """
    Serializer pour créer un média
    
    Le client doit d'abord:
    1. Chiffrer le fichier localement
    2. Uploader sur CDN (S3, CloudFlare, etc.)
    3. Envoyer l'URL du blob chiffré + métadonnées à l'API
    """
    message_id = serializers.UUIDField(
        help_text="ID du message parent"
    )
    type = serializers.ChoiceField(
        choices=Media.Type.choices,
        help_text="Type de média"
    )
    encrypted_file_url = serializers.URLField(
        help_text="URL du fichier chiffré (depuis CDN)"
    )
    encrypted_thumbnail_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL du thumbnail chiffré (images/vidéos)"
    )
    encrypted_filename = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Nom du fichier (chiffré)"
    )
    encrypted_metadata = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Métadonnées additionnelles (chiffrées)"
    )
    file_size = serializers.IntegerField(
        min_value=1,
        help_text="Taille du fichier en bytes"
    )
    duration = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
        help_text="Durée en secondes (audio/vidéo)"
    )
    width = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Largeur en pixels (images/vidéos)"
    )
    height = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Hauteur en pixels (images/vidéos)"
    )
    
    def validate_message_id(self, value):
        """Vérifier que le message existe"""
        try:
            message = Message.objects.get(id=value)
        except Message.DoesNotExist:
            raise serializers.ValidationError("Message introuvable")
        
        # Vérifier que l'utilisateur est l'expéditeur
        request = self.context.get('request')
        if message.from_user != request.user:
            raise serializers.ValidationError(
                "Seul l'expéditeur peut ajouter des médias"
            )
        
        return value
    
    def validate_file_size(self, value):
        """Limiter la taille des fichiers"""
        # Limite: 100 MB
        MAX_SIZE = 100 * 1024 * 1024  # 100 MB en bytes
        
        if value > MAX_SIZE:
            raise serializers.ValidationError(
                f"Fichier trop volumineux. Limite: 100 MB"
            )
        
        return value
    
    def validate(self, data):
        """Validation globale"""
        media_type = data.get('type')
        
        # Validation selon le type
        if media_type in [Media.Type.IMAGE, Media.Type.VIDEO]:
            if not data.get('width') or not data.get('height'):
                raise serializers.ValidationError({
                    'width': 'Largeur requise pour images/vidéos',
                    'height': 'Hauteur requise pour images/vidéos'
                })
        
        if media_type in [Media.Type.AUDIO, Media.Type.VOICE, Media.Type.VIDEO]:
            if not data.get('duration'):
                raise serializers.ValidationError({
                    'duration': 'Durée requise pour audio/vidéo'
                })
        
        return data
    
    def create(self, validated_data):
        """Créer le média"""
        message_id = validated_data.pop('message_id')
        
        media = Media.objects.create(
            message_id=message_id,
            type=validated_data['type'],
            encrypted_file_url=validated_data['encrypted_file_url'],
            encrypted_thumbnail_url=validated_data.get('encrypted_thumbnail_url', ''),
            encrypted_filename=validated_data.get('encrypted_filename', ''),
            encrypted_metadata=validated_data.get('encrypted_metadata', ''),
            file_size=validated_data['file_size'],
            duration=validated_data.get('duration'),
            width=validated_data.get('width'),
            height=validated_data.get('height'),
            is_uploaded=True  # Déjà uploadé sur CDN
        )
        
        media.mark_uploaded()
        
        return media


class MediaProgressSerializer(serializers.Serializer):
    """
    Serializer pour mettre à jour la progression d'upload
    """
    progress = serializers.IntegerField(
        min_value=0,
        max_value=100,
        help_text="Progression en pourcentage (0-100)"
    )


class MediaBulkDownloadSerializer(serializers.Serializer):
    """
    Serializer pour télécharger plusieurs médias en batch
    """
    media_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50,
        help_text="Liste des IDs de médias (max 50)"
    )
    
    def validate_media_ids(self, value):
        """Vérifier que les médias existent et sont accessibles"""
        request = self.context.get('request')
        
        # Vérifier l'accès via les conversations
        accessible_media = Media.objects.filter(
            id__in=value,
            message__conversation__participants__user=request.user
        ).values_list('id', flat=True)
        
        inaccessible = set(str(mid) for mid in value) - set(str(mid) for mid in accessible_media)
        
        if inaccessible:
            raise serializers.ValidationError(
                f"Accès refusé pour les médias: {', '.join(inaccessible)}"
            )
        
        return value