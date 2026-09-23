from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings


class AzureBlobObjectStore:
    """Implements ObjectStorePort."""

    def __init__(self, connection_string: str, container_name: str):
        self._service_client = BlobServiceClient.from_connection_string(connection_string)
        self._container_name = container_name
        try:
            self._service_client.create_container(container_name)
        except ResourceExistsError:
            pass

    def download(self, blob_path: str) -> bytes:
        blob_client = self._service_client.get_blob_client(container=self._container_name, blob=blob_path)
        try:
            return blob_client.download_blob().readall()
        except ResourceNotFoundError as exc:
            raise FileNotFoundError(f"Blob not found: {blob_path}") from exc

    def upload(self, blob_path: str, data: bytes, content_type: str) -> None:
        blob_client = self._service_client.get_blob_client(container=self._container_name, blob=blob_path)
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )