from minio import Minio
from minio.error import S3Error
import logging
import io
from config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error checking/creating bucket: {e}")

    def upload_file(self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream"):
        try:
            file_stream = io.BytesIO(file_data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_stream,
                length=len(file_data),
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to MinIO")
            return object_name
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise

    def download_file(self, object_name: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"MinIO download error: {e}")
            raise
        finally:
            if 'response' in locals():
                response.close()
                
    def delete_file(self, object_name: str):
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted {object_name} from MinIO")
        except S3Error as e:
            logger.error(f"MinIO delete error: {e}")
            raise

storage_service = StorageService()
