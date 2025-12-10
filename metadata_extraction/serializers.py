from rest_framework import serializers

from .models import FileMetadata
from .services import S3Service


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    author_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    expiration_date = serializers.DateField(required=False, allow_null=True)


class FileMetadataSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = FileMetadata
        fields = [
            "id",
            "file_name",
            "file_url",
            "content_type",
            "author_name",
            "expiration_date",
            "file_size",
            "page_count",
            "extracted_text",
            "lambda_processed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        return S3Service().get_file_url(obj.s3_key)
