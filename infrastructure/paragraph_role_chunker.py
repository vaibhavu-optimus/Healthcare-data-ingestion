from langchain_text_splitters import RecursiveCharacterTextSplitter

from domain.models import Chunk, Paragraph, Table

DEFAULT_SECTION = "GENERAL"
_HEADING_ROLES = {"title", "sectionHeading"}
_BOILERPLATE_ROLES = {"pageHeader", "pageFooter", "pageNumber"}


class _Line:
    __slots__ = ("page_number", "text", "low_confidence")

    def __init__(self, page_number: int, text: str, low_confidence: bool):
        self.page_number = page_number
        self.text = text
        self.low_confidence = low_confidence


class ParagraphRoleChunker:
    """Implements ChunkingPort."""

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 150):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, paragraphs: list[Paragraph]) -> list[Chunk]:
        current_section = DEFAULT_SECTION
        by_section: dict[str, list[_Line]] = {}

        for p in paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.role in _HEADING_ROLES:
                current_section = text.upper()
                continue
            if p.role in _BOILERPLATE_ROLES:
                continue
            by_section.setdefault(current_section, []).append(
                _Line(p.page_number, text, p.low_confidence)
            )

        chunks: list[Chunk] = []
        for section, lines in by_section.items():
            chunks.extend(self._chunk_one_section(section, lines))
        return chunks

    def chunk_tables(self, tables: list[Table]) -> list[Chunk]:
        """
        Each table becomes one Markdown chunk normally; split further
        (same splitter, same overlap) only if the rendered table is large
        enough to exceed the target chunk size on its own.
        """
        chunks: list[Chunk] = []
        for t in tables:
            markdown = t.to_markdown()
            if not markdown.strip():
                continue
            pieces = self._splitter.split_text(markdown)
            for piece in pieces:
                chunks.append(
                    Chunk(
                        text=piece,
                        section="TABLE",
                        page_start=t.page_number,
                        page_end=t.page_number,
                        low_confidence=False,
                        source_type="table",
                    )
                )
        return chunks

    def _chunk_one_section(self, section: str, lines: list[_Line]) -> list[Chunk]:
        """
        Join a section's lines into one string (tracking each line's exact
        character offset in it) and let RecursiveCharacterTextSplitter do
        the actual splitting.
        """
        pieces_text: list[str] = []
        offsets: list[tuple[int, int, int]] = []
        cursor = 0
        for i, line in enumerate(lines):
            piece = line.text + "\n"
            pieces_text.append(piece)
            offsets.append((cursor, cursor + len(piece), i))
            cursor += len(piece)
        full_text = "".join(pieces_text)

        if not full_text.strip():
            return []

        split_pieces = self._splitter.split_text(full_text)

        chunks: list[Chunk] = []
        search_cursor = 0
        for piece in split_pieces:
            piece_stripped = piece.strip()
            if not piece_stripped:
                continue

            pos = full_text.find(piece_stripped, search_cursor)
            if pos == -1:
                pos = full_text.find(piece_stripped)
            if pos == -1:
                source_lines = [lines[offsets[-1][2]]]
            else:
                piece_start, piece_end = pos, pos + len(piece_stripped)
                covered_idxs = [i for (o_start, o_end, i) in offsets if o_start < piece_end and o_end > piece_start]
                source_lines = [lines[i] for i in covered_idxs] if covered_idxs else [lines[offsets[0][2]]]
                search_cursor = piece_start + 1

            chunks.append(
                Chunk(
                    text=piece_stripped,
                    section=section,
                    page_start=min(l.page_number for l in source_lines),
                    page_end=max(l.page_number for l in source_lines),
                    low_confidence=any(l.low_confidence for l in source_lines),
                    source_type="text",
                )
            )

        return chunks