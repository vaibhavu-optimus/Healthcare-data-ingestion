import logging

from domain.models import DocumentRecord, IngestionStatus
from domain.ports import (
    ChunkingPort,
    EmbeddingPort,
    LabValueParserPort,
    ObjectStorePort,
    StructuredStorePort,
    TextExtractorPort,
    VectorStorePort
)

logger = logging.getLogger(__name__)

class IngestDocumentUseCase:
    def __init__(
            self,
            object_store: ObjectStorePort,
            text_extractor: TextExtractorPort,
            chunker: ChunkingPort,
            lab_value_parser: LabValueParserPort,
            embedder: EmbeddingPort,
            vector_store: VectorStorePort,
            structured_store: StructuredStorePort,
    ):
        self._object_store = object_store
        self._text_extractor = text_extractor
        self._chunker = chunker
        self._lab_value_parser = lab_value_parser
        self._embedder = embedder
        self._vector_store = vector_store
        self._structured_store = structured_store

    def execute(self, doc_id: str, user_id: str, blob_path: str, filename: str) -> None:
        store = self._structured_store

        record = self.get_document(doc_id)
        if record is None:
            record = DocumentRecord(doc_id=doc_id, user_id=user_id, filename=filename, blob_path=blob_path)
            store.save(record)

        store.update_status(doc_id, IngestionStatus.PROCESSING)

        try:
            self._vector_store.delete_document(doc_id)

            pdf_bytes = self._object_store.download(blob_path)
            pages = self._text_extractor.extract(pdf_bytes)
            logger.info("doc=%s extracted %d pages", doc_id, len(pages))

            chunks = self._chunker.chunk(pages)
            logger.info("doc=%s produced %d chunks", doc_id, len(chunks))

            lab_values = self._lab_value_parser.parse(pages)
            logger.info("doc=%s parsed %d lab values", doc_id, len(lab_values))

            vectors = self._embedder.embed([c.text for c in chunks])
            self._vector_store.upsert_chunks(doc_id, user_id, chunks, vectors)

            store.replace_lab_values(doc_id, lab_values)

            store.update_status(doc_id, IngestionStatus.INDEXED)
            logger.info("doc=%s status=indexed", doc_id)

        except Exception as exc:
            store.update_status(doc_id, IngestionStatus.FAILED, error_message=str(exc))
            logger.exception("doc=%s ingestion failed", doc_id)