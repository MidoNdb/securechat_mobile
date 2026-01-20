from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from authentification.models import User
import uuid


class Contact(models.Model):
    """
    Contact book entry (E2EE compatible).
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        related_name='contacts',
        on_delete=models.CASCADE
    )
    
    contact_user = models.ForeignKey(
        User,
        related_name='added_by_contacts',
        on_delete=models.CASCADE
    )
    
    nickname = models.CharField(
        max_length=100,
        blank=True,
        default="",  # ✅ Chaîne vide par défaut
        help_text="Custom nickname for this contact"
    )
    
    notes = models.TextField(
        blank=True,
        default="",  # ✅ CORRECTION ICI
        help_text="Private notes about this contact"
    )
    
    is_blocked = models.BooleanField(
        default=False,
        db_index=True
    )
    
    is_favorite = models.BooleanField(
        default=False,
        db_index=True
    )
    
    is_deleted = models.BooleanField(
        default=False
    )
    
    added_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    blocked_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'contacts'
        unique_together = ('user', 'contact_user')
        ordering = ['-is_favorite', '-added_at']
        indexes = [
            models.Index(fields=['user', 'is_blocked']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['user', 'added_at']),
        ]
    
    def clean(self):
        if self.user_id and self.contact_user_id:
            if self.user_id == self.contact_user_id:
                raise ValidationError("Cannot add yourself as contact")
        
        if self.contact_user_id and not self.contact_user.is_active:
            raise ValidationError("Cannot add inactive user")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.display_name} → {self.display_name}"
    
    @property
    def display_name(self):
        return (
            self.nickname or
            self.contact_user.display_name or
            self.contact_user.phone_number
        )
    
    @property
    def phone_number(self):
        return self.contact_user.phone_number
    
    @property
    def is_online(self):
        return self.contact_user.is_online
    
    def block(self):
        if not self.is_blocked:
            self.is_blocked = True
            self.blocked_at = timezone.now()
            self.save()
    
    def unblock(self):
        if self.is_blocked:
            self.is_blocked = False
            self.blocked_at = None
            self.save()
    
    def toggle_favorite(self):
        self.is_favorite = not self.is_favorite
        self.save()
    
    def soft_delete(self):
        self.is_deleted = True
        self.save()