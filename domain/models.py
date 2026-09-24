from dataclasses import dataclass
from enum import Enum

class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

@dataclass
class Paragraph:
    """One block of text as detected by the text-extraction adapter."""
    text: str
    role: str | None
    page_number: int
    low_confidence: bool = False

@dataclass
class TableCell:
    row_index: int
    column_index: int
    text: str
    is_header: bool

@dataclass
class Table:
    cells: list[TableCell]
    row_count: int
    column_count: int
    page_number: int

    def to_markdown(self) -> str:
        """
        Render as a Markdown table - used for the vector-store chunk so
        the table is still semantically retrievable.
        """
        grid = [["" for _ in range(self.column_count)] for _ in range(self.row_count)]
        for cell in self.cells:
            grid[cell.row_index][cell.column_index] = cell.text.replace("\n", " ").strip()
        lines = ["| " + " | ".join(row) + " |" for row in grid]
        if self.row_count > 0 and self.column_count > 0:
            separator = "| " + " | ".join(["---"] * self.column_count) + " |"
            lines.insert(1, separator)
        return "\n".join(lines)

@dataclass
class ExtractedDocument:
    """The complete structured output of extracting one PDF."""
    paragraphs: list[Paragraph]
    tables: list[Table]

@dataclass
class Chunk:
    """A retrievable unit for the vector store."""
    text: str
    section: str
    page_start: int
    page_end: int
    low_confidence: bool
    source_type: str = "text"

@dataclass
class RetrievedChunk:
    text: str
    section: str
    page_start: int
    page_end: int
    low_confidence: bool
    score: int
    source_type: str = "text"

@dataclass
class DocumentRecord:
    doc_id: str
    user_id: str
    filename: str
    blob_path: str
    status: IngestionStatus = IngestionStatus.PENDING
    error_message: str | None = None