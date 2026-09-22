from typing import Protocol
from domain.models import Chunk, DocumentRecord, IngestionStatus, LabValue, PageExtraction

class ObjectStorePort(Protocol):
    """
    Fetches raw PDF bytes for a document.
    """

    def download(self, blob_path: str) -> bytes: ...


class TextExtractorPort(Protocol):
    """
    Turns raw PDF bytes into per-page text.
    """

    def extract(self, pdf_bytes: bytes) -> list[PageExtraction]: ...


class EmbeddingPort(Protocol):
    """
    Generates embeddings for text.
    """

    def embed(self, text: list[str]) -> list[list[float]]: ...


class VectorStorePort(Protocol):
    def upsert_chunks(self, doc_id: str, user_id: str, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    def delete_document(self, doc_id: str) -> None: ...

    def query(self, query_vector: list[float], user_id: str, top_k: int) -> dict: ...


class StructuredStorePort(Protocol):
    """
    Document status tracking + structured lab values.
    """

    def get_document(self, doc_id: str) -> DocumentRecord | None: ...

    def save_document() -> None: ...

    def update_status(self, doc_id: str, status: IngestionStatus, error_message: str | None = None) -> None: ...

    def replace_lab_values(self, doc_id: str, lab_values: list[LabValue]) -> None: ...


class LabValueParserPort(Protocol):
    """
    Parses structured lab values out of a document's extracted pages.
    """

    def parse(self, pages: list[PageExtraction]) -> list[LabValue]: ...


class ChunkingPort(Protocol):
    """
    Splits a document's extracted pages into retrieval chunks.
    """

    def chunk(self, pages: list[PageExtraction]) -> list[Chunk]: ...