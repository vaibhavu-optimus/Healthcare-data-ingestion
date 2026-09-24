import datetime

from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from domain.models import DocumentRecord, IngestionStatus

Base = declarative_base()

def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class DocumentRow(Base):
    __tablename__ = "documents"
    doc_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String, nullable=False)
    blob_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

class SqlStructuredStore:
    """Implements StructuredStorePort."""

    def __init__(self, db_url: str = "sqlite:///./data/ingestion.db"):
        self._engine = create_engine(db_url)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def get_document(self, doc_id: str) -> DocumentRecord | None:
        session = self._Session()
        try:
            row = session.get(DocumentRow, doc_id)
            if row is None:
                return None
            return DocumentRecord(
                doc_id=row.doc_id,
                user_id=row.user_id,
                filename=row.filename,
                blob_path=row.blob_path,
                status=IngestionStatus(row.status),
                error_message=row.error_message,
            )
        finally:
            session.close()

    def save_document(self, record: DocumentRecord) -> None:
        session = self._Session()
        try:
            session.add(
                DocumentRow(
                    doc_id=record.doc_id,
                    user_id=record.user_id,
                    filename=record.filename,
                    blob_path=record.blob_path,
                    status=record.status.value,
                    error_message=record.error_message,
                )
            )
            session.commit()
        finally:
            session.close()

    def update_status(self, doc_id: str, status: IngestionStatus, error_message: str | None = None) -> None:
        session = self._Session()
        try:
            row = session.get(DocumentRow, doc_id)
            if row is not None:
                row.status = status.value
                row.error_message = error_message
                session.commit()
        finally:
            session.close()