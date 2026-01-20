from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class Media(models.Model):
    """
    Encrypted media attachment (E2EE).
    """
    
    class Type(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        VIDEO = "VIDEO", "Video"
        AUDIO = "AUDIO", "Audio"
        VOICE = "VOICE", "Voice Note"
        FILE = "FILE", "File"
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    message = models.ForeignKey(
        'messagerie.Message',
        related_name='media_attachments',
        on_delete=models.CASCADE
    )
    
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True
    )
    
    encrypted_file_url = models.TextField(
        help_text="URL to encrypted file blob"
    )
    
    encrypted_thumbnail_url = models.TextField(
        blank=True,
        default="",
        help_text="URL to encrypted thumbnail"
    )
    
    encrypted_filename = models.TextField(
        blank=True,
        default="",  # ✅ CORRECTION
        help_text="Original filename (encrypted)"
    )
    
    file_size = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        help_text="File size in bytes"
    )
    
    duration = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Duration in seconds (audio/video only)"
    )
    
    width = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Width in pixels"
    )
    
    height = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Height in pixels"
    )
    
    encrypted_metadata = models.TextField(
        blank=True,
        default="",
        help_text="Additional encrypted metadata"
    )
    
    is_uploaded = models.BooleanField(
        default=False
    )
    
    upload_progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    
    uploaded_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'media'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message', 'type']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['is_uploaded']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.message_id}"
    
    @property
    def size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def duration_formatted(self):
        if not self.duration:
            return None
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def mark_uploaded(self):
        self.is_uploaded = True
        self.upload_progress = 100
        self.uploaded_at = timezone.now()
        self.save()
    
    def update_progress(self, progress):
        if 0 <= progress <= 100:
            self.upload_progress = progress
            self.save()