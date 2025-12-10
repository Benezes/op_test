from botocore.exceptions import ClientError
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .exceptions import FileUploadException
from .models import FileMetadata
from .serializers import FileMetadataSerializer, FileUploadSerializer
from .services import S3Service


class FileUploadView(CreateAPIView):
    serializer_class = FileUploadSerializer
    parser_classes = [MultiPartParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        author_name = serializer.validated_data.get("author_name", "")
        expiration_date = serializer.validated_data.get("expiration_date")
        content_type = uploaded_file.content_type or "application/octet-stream"

        s3_service = S3Service()

        file_metadata = FileMetadata(
            file_name=uploaded_file.name,
            s3_bucket=s3_service.bucket_name,
            content_type=content_type,
            author_name=author_name,
            expiration_date=expiration_date,
            file_size=uploaded_file.size,
        )

        try:
            s3_key = s3_service.upload_file(
                file=uploaded_file.file,
                file_id=file_metadata.id,
                original_filename=uploaded_file.name,
                content_type=content_type,
            )
        except ClientError as e:
            raise FileUploadException(detail=str(e))

        file_metadata.s3_key = s3_key
        file_metadata.save()

        return Response(
            {"file_id": str(file_metadata.id)}, status=status.HTTP_201_CREATED
        )


class FileMetadataView(RetrieveAPIView):
    queryset = FileMetadata.objects.all()
    serializer_class = FileMetadataSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "file_id"
