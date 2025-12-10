from django.urls import path
from .views import FileUploadView, FileMetadataView

urlpatterns = [
    path("upload", FileUploadView.as_view(), name="file-upload"),
    path("metadata/<uuid:file_id>", FileMetadataView.as_view(), name="file-metadata"),
]

