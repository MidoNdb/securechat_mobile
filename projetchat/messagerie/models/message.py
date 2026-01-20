


# messagerie/models/message.py
# ✅ REMPLACE TON FICHIER message.py AVEC CE CODE COMPLET

from django.db import models
from django.utils import timezone
from authentification.models import User
from .conversation import Conversation
import uuid


class Message(models.Model):
    """
    Message chiffré de bout en bout (E2EE).
    Le serveur ne peut JAMAIS lire le contenu.
    
    Architecture E2EE:
    - encrypted_content: Ciphertext AES-256-GCM
    - nonce: Nombre unique pour chaque chiffrement
    - auth_tag: Tag d'authentification GCM
    - signature: Signature Ed25519 pour authenticité
    """

    class Type(models.TextChoices):
        TEXT = "TEXT", "Text"
        IMAGE = "IMAGE", "Image"
        VIDEO = "VIDEO", "Video"
        VOICE = "VOICE", "Voice"
        FILE = "FILE", "File"
        SYSTEM = "SYSTEM", "System"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE
    )

    from_user = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.CASCADE
    )
    recipient_user = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User pour qui le message a été chiffré (utilisé pour déchiffrement)"
    )

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.TEXT
    )

    # ========================================
    # ✅ CHAMPS E2EE COMPLETS (4 champs)
    # ========================================
    
    encrypted_content = models.TextField(
        help_text="Ciphertext AES-256-GCM (Base64)"
    )
    
    nonce = models.CharField(
        max_length=255,
        default='',
        help_text="Nonce AES-GCM (Base64) - 12 bytes"
    )
    
    auth_tag = models.CharField(
        max_length=255,
        default='',
        help_text="Authentication tag AES-GCM (Base64) - 16 bytes"
    )
    
    signature = models.TextField(
        default='',
        help_text="Signature Ed25519 du hash du ciphertext (Base64)"
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Métadonnées non sensibles (file_name, size, etc.)"
    )

    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies"
    )

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        db_table = 'messages'
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["from_user"]),
        ]
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        name = self.from_user.display_name or self.from_user.phone_number
        return f"{name} - {self.type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    


    # from django.db import models
# from django.utils import timezone
# from authentification.models import User
# from .conversation import Conversation
# import uuid


# class Message(models.Model):
#     """
#     Message chiffré de bout en bout (E2EE).
#     Le serveur ne peut JAMAIS lire le contenu.
#     """

#     class Type(models.TextChoices):
#         TEXT = "TEXT", "Text"
#         IMAGE = "IMAGE", "Image"
#         VIDEO = "VIDEO", "Video"
#         VOICE = "VOICE", "Voice"
#         FILE = "FILE", "File"
#         SYSTEM = "SYSTEM", "System"

#     class Status(models.TextChoices):
#         SENT = "SENT", "Sent"
#         DELIVERED = "DELIVERED", "Delivered"
#         READ = "READ", "Read"

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )

#     conversation = models.ForeignKey(
#         Conversation,
#         related_name="messages",
#         on_delete=models.CASCADE
#     )

#     from_user = models.ForeignKey(
#         User,
#         related_name="sent_messages",
#         on_delete=models.CASCADE
#     )

#     type = models.CharField(
#         max_length=20,
#         choices=Type.choices,
#         default=Type.TEXT
#     )

#     encrypted_content = models.TextField()
#     """
#     Contenu chiffré (texte, URL média chiffré, etc.)
#     """

#     metadata = models.JSONField(
#         blank=True,
#         null=True
#     )
#     """
#     Exemple:
#     {
#       "file_name": "test.pdf",
#       "size": 234234,
#       "duration": 12
#     }
#     """

#     reply_to = models.ForeignKey(
#         "self",
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         related_name="replies"
#     )

#     is_deleted = models.BooleanField(default=False)

#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         db_index=True
#     )

#     class Meta:
#         ordering = ["created_at"]
#         indexes = [
#             models.Index(fields=["conversation", "created_at"]),
#             models.Index(fields=["from_user"]),
#         ]

#     def __str__(self):
#         return f"{self.from_user.display_name} - {self.type}"
    
    
# class MessageKey(models.Model):
#     """
#     Clé de message chiffrée pour chaque participant.
#     """

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )

#     message = models.ForeignKey(
#         Message,
#         related_name="keys",
#         on_delete=models.CASCADE
#     )

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE
#     )

#     encrypted_key = models.TextField()

#     class Meta:
#         unique_together = ("message", "user")
#         indexes = [
#             models.Index(fields=["user"]),
#             models.Index(fields=["message"]),
#         ]

# def __str__(self):
#     name = self.from_user.display_name or self.from_user.phone_number
#     return f"{name} - {self.type}"
