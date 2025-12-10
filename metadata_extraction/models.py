import uuid

from django.db import models


class FileMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=512, unique=True)
    s3_bucket = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)

    author_name = models.CharField(max_length=255, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    file_size = models.BigIntegerField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    extracted_text = models.TextField(blank=True)
    lambda_processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "file_metadata"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["s3_key"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.id})"
