from django.db import models
from django.utils import timezone
from authentification.models import User
import uuid

class MessageStatus(models.Model):
    """
    Statut de lecture par utilisateur (E2EE groupes).
    
    Exemple:
    - Message envoyé à groupe de 5 personnes
    - 5 MessageStatus créés (un par personne)
    - Chacun track indépendamment: SENT → DELIVERED → READ
    """
    
    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        READ = "READ", "Read"
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    message = models.ForeignKey(
        'messagerie.Message',  # ✅ Évite import circulaire
        related_name='statuses',
        on_delete=models.CASCADE
    )
    
    user = models.ForeignKey(
        User,
        related_name='message_read_receipts',  # ✅ Plus clair
        on_delete=models.CASCADE
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SENT,
        db_index=True
    )
    
    # 📅 Timestamps précis
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Quand le message a été envoyé"
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quand l'utilisateur a reçu le message"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Quand l'utilisateur a lu le message"
    )
    
    class Meta:
        db_table = 'message_statuses'
        unique_together = ('message', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['message', 'status']),
        ]
        verbose_name = 'Message Status'
        verbose_name_plural = 'Message Statuses'
    
    def __str__(self):
        return f"{self.user.display_name} - {self.status}"
    
    def mark_delivered(self):
        """Marquer comme livré"""
        if self.status == self.Status.SENT:
            self.status = self.Status.DELIVERED
            self.delivered_at = timezone.now()
            self.save()
    
    def mark_read(self):
        """Marquer comme lu"""
        if self.status != self.Status.READ:
            self.status = self.Status.READ
            self.read_at = timezone.now()
            if not self.delivered_at:
                self.delivered_at = timezone.now()
            self.save()