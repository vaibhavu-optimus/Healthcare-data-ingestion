import logging
from domain.models import Chunk, DocumentRecord, IngestionStatus, StoredImage
from domain.ports import (
    ChunkingPort,
    EmbeddingPort,
    ObjectStorePort,
    StructuredStorePort,
    TextExtractorPort,
    VectorStorePort,
)

logger = logging.getLogger(__name__)

class IngestDocumentUseCase:
    def __init__(
        self,
        object_store: ObjectStorePort,
        text_extractor: TextExtractorPort,
        chunker: ChunkingPort,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        structured_store: StructuredStorePort,
    ):
        self._object_store = object_store
        self._text_extractor = text_extractor
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._structured_store = structured_store

    def execute(self, doc_id: str, user_id: str, blob_path: str, filename: str) -> None:
        store = self._structured_store

        record = store.get_document(doc_id)
        if record is None:
            record = DocumentRecord(doc_id=doc_id, user_id=user_id, filename=filename, blob_path=blob_path)
            store.save_document(record)

        store.update_status(doc_id, IngestionStatus.PROCESSING)

        try:
            self._vector_store.delete_document(doc_id)

            pdf_bytes = self._object_store.download(blob_path)
            extracted = self._text_extractor.extract(pdf_bytes)
            logger.info(
                "doc=%s extracted %d paragraphs, %d tables, %d figures",
                doc_id, len(extracted.paragraphs), len(extracted.tables), len(extracted.figures),
            )

            text_chunks = self._chunker.chunk_text(extracted.paragraphs)
            table_chunks = self._chunker.chunk_tables(extracted.tables)

            # We'll skip processing images in document right now since we require a vision model for that
            """
            stored_images: list[StoredImage] = []
            figure_chunks: list[Chunk] = []
            for i, figure in enumerate(extracted.figures):
                image_id = f"{doc_id}:fig:{i}"
                image_blob_path = f"extracted-images/{user_id}/{doc_id}/{image_id}.png"
                self._object_store.upload(image_blob_path, figure.image_bytes, figure.content_type)

                nearby_paragraphs = [p for p in extracted.paragraphs if p.page_number == figure.page_number]
                caption = self._image_captioner.caption(figure, nearby_paragraphs)

                stored_images.append(
                    StoredImage(
                        image_id=image_id,
                        doc_id=doc_id,
                        page_number=figure.page_number,
                        blob_path=image_blob_path,
                        caption=caption,
                    )
                )
                figure_chunks.append(
                    Chunk(
                        text=caption,
                        section="IMAGE",
                        page_start=figure.page_number,
                        page_end=figure.page_number,
                        low_confidence=False,
                        source_type="figure_caption",
                        image_id=image_id,
                    )
                )

            logger.info("doc=%s extracted %d figures", doc_id, len(stored_images))
            """

            # We are only chunking texts and tables data at the current
            all_chunks = text_chunks + table_chunks
            vectors = self._embedder.embed([c.text for c in all_chunks])
            self._vector_store.upsert_chunks(doc_id, user_id, all_chunks, vectors)

            # store.replace_lab_values(doc_id, lab_values)
            # store.replace_images(doc_id, stored_images)

            store.update_status(doc_id, IngestionStatus.INDEXED)
            logger.info("doc=%s status=indexed", doc_id)

        except Exception as exc:
            store.update_status(doc_id, IngestionStatus.FAILED, error_message=str(exc))
            logger.exception("doc=%s ingestion failed", doc_id)
            raise