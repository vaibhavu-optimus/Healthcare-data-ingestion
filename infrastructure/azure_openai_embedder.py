from langchain_openai import AzureOpenAIEmbeddings

class AzureOpenAIEmbedder:
    """Implements EmbeddingPort (domain/ports.py)."""

    def __init__(self, endpoint: str, api_key: str, deployment_name: str, api_version: str):
        self._client = AzureOpenAIEmbeddings(
            azure_endpoint=endpoint,
            api_key=api_key,
            azure_deployment=deployment_name,
            openai_api_version=api_version,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._client.embed_documents(texts)