from dataclasses import dataclass
from enum import Enum

class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

@dataclass
class PageExtraction:
    page_number: int
    text: str
    method: str
    confidence: float
    low_confidence: bool

@dataclass
class Chunk:
    text: str
    section: str
    page_start: int
    page_end: int
    low_confidence: bool

@dataclass
class LabValue:
    test_name: str
    value: float
    unit: str | None
    reference_low: float | None
    reference_high: float | None
    flag: str | None     # "H", "L", or None
    page_number: int

@dataclass
class DocumentRecord:
    doc_id: str
    user_id: str
    filename: str
    blob_path: str
    status: IngestionStatus = IngestionStatus.PENDING
    error_message: str | None = None