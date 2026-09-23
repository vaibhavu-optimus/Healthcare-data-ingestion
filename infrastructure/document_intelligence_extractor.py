from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeOutputOption,
    AnalyzeResult,
)
from azure.core.credentials import AzureKeyCredential

from domain.models import ExtractedDocument, Figure, Paragraph, Table, TableCell

_LOW_CONFIDENCE_THRESHOLD = 0.70

class DocumentIntelligenceTextExtractor:
    """Implements TextExtractorPort"""

    def __init__(self, endpoint: str, api_key: str, model_id: str = "prebuilt-layout"):
        self._client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
        self._model_id = model_id

    def _paragraph_confidence(self, result: AnalyzeResult, paragraph) -> float | None:
        """
        Average the per-word confidence of words whose spans fall inside
        this paragraph's span, so low_confidence reflects genuine OCR
        uncertainty on THIS paragraph rather than a fixed value.
        """
        if not paragraph.spans:
            return None
        span = paragraph.spans[0]
        start, end = span.offset, span.offset + span.length
        confidences = []
        for page in result.pages or []:
            for word in page.words or []:
                w_start = word.span.offset
                w_end = w_start + word.span.length
                if w_start >= start and w_end <= end:
                    confidences.append(word.confidence)
        return sum(confidences) / len(confidences) if confidences else None
    
    def extract(self, pdf_bytes: bytes) -> ExtractedDocument:
        poller = self._client.begin_analyze_document(
            self._model_id,
            AnalyzeDocumentRequest(bytes_source=pdf_bytes),
            output=[AnalyzeOutputOption.FIGURES]
        )
        result: AnalyzeResult = poller.result()
        operation_id = poller.details["operation_id"]

        return ExtractedDocument(
            paragraphs=self._map_paragraphs(result),
            tables=self._map_tables(result),
            figures=self._map_figures(result, operation_id),
        )

    def _map_paragraphs(self, result: AnalyzeResult) -> list[Paragraph]:
        paragraphs = []
        for p in result.paragraphs or []:
            page_number = p.bounding_regions[0].page_number if p.bounding_regions else 1
            confidence = self._paragraph_confidence(result, p)
            paragraphs.append(
                Paragraph(
                    text=p.content,
                    role=p.role,
                    page_number=page_number,
                    low_confidence=(confidence is not None and confidence < _LOW_CONFIDENCE_THRESHOLD),
                )
            )

        return paragraphs

    def _map_tables(self, result: AnalyzeResult) -> list[Table]:
        tables = []
        for t in result.tables or []:
            page_number = t.bounding_regions[0].page_number if t.bounding_regions else 1
            cells = [
                TableCell(
                    row_index=c.row_index,
                    column_index=c.column_index,
                    text=c.content,
                    is_header=(getattr(c, "kind", None) == "columnHeader"),
                )
                for c in t.cells
            ]
            tables.append(
                Table(cells=cells, row_count=t.row_count, column_count=t.column_count, page_number=page_number)
            )

        return tables

    def _map_figures(self, result: AnalyzeResult, operation_id: str) -> list[Figure]:
        """
        DI detects figures as bounding regions but doesn't hand back image
        bytes directly -- get_analyze_result_figure() is a separate call
        that returns the already-cropped PNG for one figure ID.
        """
        figures = []
        for fig in getattr(result, "figures", None) or []:
            if not fig.id:
                continue
            page_number = fig.bounding_regions[0].page_number if fig.bounding_regions else 1
            image_bytes = b"".join(
                self._client.get_analyze_result_figure(
                    model_id=result.model_id, result_id=operation_id, figure_id=fig.id
                )
            )
            figures.append(Figure(page_number=page_number, image_bytes=image_bytes, content_type="image/png"))
            
        return figures