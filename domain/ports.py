from typing import Protocol

from domain.models import (
    Chunk,
    DocumentRecord,
    ExtractedDocument,
    Figure,
    IngestionStatus,
    LabValue,
    Paragraph,
    StoredImage,
    Table,
)


class ObjectStorePort(Protocol):
    """Fetches raw PDF bytes, and stores extracted images."""

    def download(self, blob_path: str) -> bytes: ...

    def upload(self, blob_path: str, data: bytes, content_type: str) -> None: ...


class TextExtractorPort(Protocol):
    """
    Turns raw PDF bytes into a fully structured ExtractedDocument:
    paragraphs (tagged with a semantic role), tables (as real cells), and
    figures (as image bytes).
    """

    def extract(self, pdf_bytes: bytes) -> ExtractedDocument: ...


class ChunkingPort(Protocol):
    """
    Produces vector-store chunks from a document's structured content.
    Text and tables are handled separately -- a table's cells never enter
    the prose sliding-window, which is what avoids a table silently
    bleeding into whatever narrative section happened to precede it.
    """

    def chunk_text(self, paragraphs: list[Paragraph]) -> list[Chunk]: ...

    def chunk_tables(self, tables: list[Table]) -> list[Chunk]: ...


class LabValueParserPort(Protocol):
    """
    Maps table cells directly to structured LabValue rows.
    """

    def parse(self, tables: list[Table]) -> list[LabValue]: ...


class ImageCaptionPort(Protocol):
    """
    Produces a short, searchable caption for an extracted figure --
    descriptive only ("frontal chest X-ray with an annotation marking the
    right lower lobe"), never a diagnostic interpretation of what's shown.
    A cheap adapter might reuse nearby paragraph text; a stronger one sends
    the image to a vision-capable model at ingestion time.
    """

    def caption(self, figure: Figure, nearby_paragraphs: list[Paragraph]) -> str: ...


class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStorePort(Protocol):
    def upsert_chunks(
        self, doc_id: str, user_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None: ...

    def delete_document(self, doc_id: str) -> None: ...

    def query(self, query_vector: list[float], user_id: str, top_k: int) -> dict: ...


class StructuredStorePort(Protocol):
    """Document status tracking, structured lab values, and stored image references."""

    def get_document(self, doc_id: str) -> DocumentRecord | None: ...

    def save_document(self, record: DocumentRecord) -> None: ...

    def update_status(
        self, doc_id: str, status: IngestionStatus, error_message: str | None = None
    ) -> None: ...

    def replace_lab_values(self, doc_id: str, lab_values: list[LabValue]) -> None: ...

    def replace_images(self, doc_id: str, images: list[StoredImage]) -> None: ...

    def get_images(self, doc_id: str) -> list[StoredImage]: ...