from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import FileMetadata


class FileUploadViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("file-upload")

    @patch("metadata_extraction.views.S3Service")
    def test_upload_success(self, mock_s3_class):
        mock_s3 = MagicMock()
        mock_s3.bucket_name = "test-bucket"
        mock_s3.upload_file.return_value = "uploads/test-id.pdf"
        mock_s3_class.return_value = mock_s3

        file = BytesIO(b"fake pdf content")
        file.name = "test.pdf"

        response = self.client.post(
            self.url,
            {"file": file, "author_name": "Test Author"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("file_id", response.data)
        self.assertTrue(
            FileMetadata.objects.filter(id=response.data["file_id"]).exists()
        )

    @patch("metadata_extraction.views.S3Service")
    def test_upload_with_expiration_date(self, mock_s3_class):
        mock_s3 = MagicMock()
        mock_s3.bucket_name = "test-bucket"
        mock_s3.upload_file.return_value = "uploads/test-id.pdf"
        mock_s3_class.return_value = mock_s3

        file = BytesIO(b"fake content")
        file.name = "doc.pdf"

        response = self.client.post(
            self.url,
            {"file": file, "author_name": "Author", "expiration_date": "2025-12-31"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        metadata = FileMetadata.objects.get(id=response.data["file_id"])
        self.assertEqual(str(metadata.expiration_date), "2025-12-31")

    def test_upload_without_file_returns_400(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("metadata_extraction.views.S3Service")
    def test_upload_s3_failure_returns_500(self, mock_s3_class):
        from botocore.exceptions import ClientError

        mock_s3 = MagicMock()
        mock_s3.bucket_name = "test-bucket"
        mock_s3.upload_file.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "S3 Error"}}, "upload"
        )
        mock_s3_class.return_value = mock_s3

        file = BytesIO(b"content")
        file.name = "test.pdf"

        response = self.client.post(self.url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileMetadataViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("metadata_extraction.serializers.S3Service")
    def test_get_metadata_success(self, mock_s3_class):
        mock_s3 = MagicMock()
        mock_s3.get_file_url.return_value = "https://s3.amazonaws.com/test-url"
        mock_s3_class.return_value = mock_s3

        metadata = FileMetadata.objects.create(
            file_name="test.pdf",
            s3_key="uploads/test.pdf",
            s3_bucket="test-bucket",
            content_type="application/pdf",
            author_name="Author",
            file_size=1024,
        )

        url = reverse("file-metadata", kwargs={"file_id": metadata.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(metadata.id))
        self.assertEqual(response.data["file_name"], "test.pdf")
        self.assertEqual(response.data["author_name"], "Author")
        self.assertEqual(response.data["file_url"], "https://s3.amazonaws.com/test-url")

    def test_get_metadata_not_found(self):
        fake_id = uuid4()
        url = reverse("file-metadata", kwargs={"file_id": fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("metadata_extraction.serializers.S3Service")
    def test_get_metadata_with_lambda_processed(self, mock_s3_class):
        mock_s3 = MagicMock()
        mock_s3.get_file_url.return_value = "https://s3.amazonaws.com/test-url"
        mock_s3_class.return_value = mock_s3

        metadata = FileMetadata.objects.create(
            file_name="document.pdf",
            s3_key="uploads/document.pdf",
            s3_bucket="test-bucket",
            content_type="application/pdf",
            file_size=2048,
            page_count=5,
            extracted_text="Sample text",
            lambda_processed=True,
        )

        url = reverse("file-metadata", kwargs={"file_id": metadata.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page_count"], 5)
        self.assertEqual(response.data["extracted_text"], "Sample text")
        self.assertTrue(response.data["lambda_processed"])
