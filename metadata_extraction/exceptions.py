from rest_framework.exceptions import APIException


class FileUploadException(APIException):
    status_code = 500
    default_detail = "Failed to upload file"
    default_code = "file_upload_error"

