import logging
import re
from urllib.parse import unquote, urlparse

import azure.functions as func

from settings import build_ingest_use_case

app = func.FunctionApp()

_ingest_use_case = build_ingest_use_case()

_UPLOAD_PATH_PATTERN = re.compile(r"^uploads/(?P<user_id>[^/]+)/(?P<doc_id>[^/]+)/(?P<filename>.+)$")


def _parse_blob_path(blob_url: str) -> tuple[str, str, str, str]:
    """
    (blob_path, user_id, doc_id, filename) from the full blob URL Event
    Grid reports in the event's data.url field. Returns blob_path relative
    to the container
    """
    parsed = urlparse(blob_url)
    _, _, blob_path = parsed.path.lstrip("/").partition("/")
    blob_path = unquote(blob_path)

    match = _UPLOAD_PATH_PATTERN.match(blob_path)
    if not match:
        raise ValueError(f"blob path does not match the uploads/ convention: {blob_path!r}")
    return blob_path, match.group("user_id"), match.group("doc_id"), match.group("filename")


@app.function_name(name="ingest_document_on_blob_created")
@app.event_grid_trigger(arg_name="event")
def ingest_document_on_blob_created(event: func.EventGridEvent) -> None:
    if event.event_type != "Microsoft.Storage.BlobCreated":
        logging.info("Ignoring event_type=%s (not a blob creation)", event.event_type)
        return

    data = event.get_json() or {}
    blob_url = data.get("url", "")

    try:
        blob_path, user_id, doc_id, filename = _parse_blob_path(blob_url)
    except ValueError as exc:
        logging.info("Skipping blob event: %s", exc)
        return

    logging.info("doc=%s user=%s: ingestion triggered by blob at %s", doc_id, user_id, blob_path)

    try:
        _ingest_use_case.execute(doc_id=doc_id, user_id=user_id, blob_path=blob_path, filename=filename)
    except Exception:
        logging.exception("doc=%s: ingestion failed", doc_id)
        raise