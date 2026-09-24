import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import dotenv_values

from infrastructure.azure_ai_search_vector_store import create_index_if_not_exists
from infrastructure.azure_blob_object_store import create_container_if_not_exists

_DEFAULT_VECTOR_DIMENSIONS = 3072

def _load_dotenv_into_environ() -> None:
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for key, value in dotenv_values(path).items():
        if value is not None:
            os.environ.setdefault(key, value)

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required setting '{name}' is not set (checked os.environ and .env)")
    return value


def main() -> None:
    _load_dotenv_into_environ()

    print("Provisioning Blob container...")
    create_container_if_not_exists(
        connection_string=_require_env("BLOB_CONNECTION_STRING"),
        container_name=_require_env("BLOB_CONTAINER_NAME"),
    )
    print("  done.")

    print("Provisioning Azure AI Search index...")
    vector_dimensions = int(os.environ.get("AZURE_OPENAI_EMBEDDING_DIMENSIONS", _DEFAULT_VECTOR_DIMENSIONS))
    create_index_if_not_exists(
        endpoint=_require_env("AZURE_SEARCH_ENDPOINT"),
        api_key=_require_env("AZURE_SEARCH_KEY"),
        index_name=_require_env("AZURE_SEARCH_INDEX_NAME"),
        vector_dimensions=vector_dimensions,
    )
    print(f"  done (vector_dimensions={vector_dimensions}).")

    print("\nAll resources provisioned (or already existed -- this script is safe to re-run).")

if __name__ == "__main__":
    main()