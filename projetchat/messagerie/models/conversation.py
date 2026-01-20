from django.db import models
from django.utils import timezone
from authentification.models import User
import uuid


class Conversation(models.Model):
    """
    Représente une conversation chiffrée (E2EE).
    Le serveur ne voit jamais le contenu des messages.
    """

    class Type(models.TextChoices):
        DIRECT = "DIRECT", "Direct"
        GROUP = "GROUP", "Group"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        db_index=True
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ========================================
    # ✅ AJOUT : Référence au dernier message
    # ========================================
    last_message = models.ForeignKey(
        'Message',  # ⚠️ String reference (Message sera défini après)
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_last_message',
        help_text="Dernier message envoyé dans cette conversation"
    )

    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["last_message_at"]),
        ]

    def __str__(self):
        if self.type == self.Type.GROUP:
            return self.name or f"Groupe {self.id}"
        return f"Conversation directe {self.id}"


class ConversationParticipant(models.Model):
    """
    Lien entre un utilisateur et une conversation.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversation_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("conversation", "user")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["conversation"]),
        ]

    def __str__(self):
        return f"{self.user.display_name} ({self.role})"


# from django.db import models
# from django.utils import timezone
# from authentification.models import User
# import uuid


# class Conversation(models.Model):
#     """
#     Représente une conversation chiffrée (E2EE).
#     Le serveur ne voit jamais le contenu des messages.
#     """

#     class Type(models.TextChoices):
#         DIRECT = "DIRECT", "Direct"
#         GROUP = "GROUP", "Group"

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )

#     type = models.CharField(
#         max_length=10,
#         choices=Type.choices,
#         db_index=True
#     )

#     name = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True
#     )

#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name="created_conversations"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)

#     last_message_at = models.DateTimeField(
#         null=True,
#         blank=True,
#         db_index=True
#     )

#     class Meta:
#         ordering = ["-last_message_at", "-created_at"]
#         indexes = [
#             models.Index(fields=["type"]),
#             models.Index(fields=["last_message_at"]),
#         ]

#     def __str__(self):
#         if self.type == self.Type.GROUP:
#             return self.name or f"Groupe {self.id}"
#         return f"Conversation directe {self.id}"


# class ConversationParticipant(models.Model):
#     """
#     Lien entre un utilisateur et une conversation.
#     """

#     class Role(models.TextChoices):
#         ADMIN = "ADMIN", "Admin"
#         MEMBER = "MEMBER", "Member"

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )

#     conversation = models.ForeignKey(
#         Conversation,
#         on_delete=models.CASCADE,
#         related_name="participants"
#     )

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="conversation_memberships"
#     )

#     role = models.CharField(
#         max_length=20,
#         choices=Role.choices,
#         default=Role.MEMBER
#     )

#     joined_at = models.DateTimeField(auto_now_add=True)

#     is_muted = models.BooleanField(default=False)
#     is_archived = models.BooleanField(default=False)

#     class Meta:
#         unique_together = ("conversation", "user")
#         indexes = [
#             models.Index(fields=["user"]),
#             models.Index(fields=["conversation"]),
#         ]

#     def __str__(self):
#         return f"{self.user.display_name} ({self.role})"
