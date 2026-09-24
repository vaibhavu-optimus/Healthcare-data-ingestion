import os

from application.ingest_document import IngestDocumentUseCase
from infrastructure.azure_ai_search_vector_store import AzureAISearchVectorStore
from infrastructure.azure_blob_object_store import AzureBlobObjectStore
from infrastructure.azure_openai_embedder import AzureOpenAIEmbedder
from infrastructure.document_intelligence_extractor import DocumentIntelligenceTextExtractor
from infrastructure.paragraph_role_chunker import ParagraphRoleChunker
from infrastructure.sql_structured_store import SqlStructuredStore


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required application setting '{name}' is not set")
    return value


def build_ingest_use_case() -> IngestDocumentUseCase:
    object_store = AzureBlobObjectStore(
        connection_string=_require_env("BLOB_CONNECTION_STRING"),
        container_name=_require_env("BLOB_CONTAINER_NAME"),
    )
    text_extractor = DocumentIntelligenceTextExtractor(
        endpoint=_require_env("DOCUMENT_INTELLIGENCE_ENDPOINT"),
        api_key=_require_env("DOCUMENT_INTELLIGENCE_KEY"),
    )
    chunker = ParagraphRoleChunker()
    embedder = AzureOpenAIEmbedder(
        endpoint=_require_env("AZURE_OPENAI_ENDPOINT"),
        api_key=_require_env("AZURE_OPENAI_KEY"),
        deployment_name=_require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=_require_env("AZURE_OPENAI_API_VERSION"),
    )
    vector_store = AzureAISearchVectorStore(
        endpoint=_require_env("AZURE_SEARCH_ENDPOINT"),
        api_key=_require_env("AZURE_SEARCH_KEY"),
        index_name=_require_env("AZURE_SEARCH_INDEX_NAME"),
    )
    structured_store = SqlStructuredStore(db_url=_require_env("SQL_DB_URL"))

    return IngestDocumentUseCase(
        object_store=object_store,
        text_extractor=text_extractor,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        structured_store=structured_store,
    )