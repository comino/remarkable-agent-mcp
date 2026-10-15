"""Durable reply delivery, separate from executing or acknowledging a request."""

from __future__ import annotations

import json
import uuid

from remarkable_mcp.workflows import cloud
from remarkable_mcp.workflows.inbox.inbox import replies_markdown
from remarkable_mcp.workflows.state import Store, now_iso

REPLIES_FOLDER = "/Agent/Replies"


def pending(record: dict) -> list[dict]:
    return [d for d in record.get("deliveries", {}).values() if d["status"] == "pending"]


def queue(record: dict, answers: list[dict]) -> str:
    """Queue one immutable reply batch inside the caller's atomic inbox update.

    The same answers to the same request revisions produce the same document
    UUID, including after a lost upload response or a process restart.
    """
    identity = json.dumps(
        {"inbox": record.get("doc_id", record["name"]), "answers": answers},
        sort_keys=True,
        ensure_ascii=False,
    )
    delivery_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "remarkable-inbox:" + identity))
    deliveries = record.setdefault("deliveries", {})
    deliveries.setdefault(
        delivery_id,
        {
            "id": delivery_id,
            "status": "pending",
            "document_id": delivery_id,
            "title": "Replies " + now_iso().replace("T", " ")[:16],
            "answers": answers,
            "created_at": now_iso(),
        },
    )
    for answer in answers:
        record["entries"][answer["id"]]["reply_delivery"] = delivery_id
    return delivery_id


def deliver_pending(name: str) -> list[str]:
    """Deliver saved replies without running their tasks again.

    A separate cross-process lock serializes delivery without holding the inbox
    record lock across network calls. Each success is committed independently.
    Failures leave the remaining batches pending for the next attempt.
    """
    from remarkable_mcp.core.write_tools import write_enabled
    from remarkable_mcp.documents.markdown_pdf import render_markdown_pdf

    if not write_enabled():
        raise RuntimeError("Reply delivery is disabled in read-only mode.")
    if not cloud.is_cloud():
        raise RuntimeError("Reply delivery requires cloud mode.")
    store = Store("inbox")
    documents = []
    with Store("reply-delivery").locked():
        record = store.get(name)
        if record is None:
            return []
        for batch in pending(record):
            with cloud.MUPDF_LOCK:
                pdf = render_markdown_pdf(replies_markdown(batch["answers"]))
            cloud.upload_pdf(pdf, batch["title"], REPLIES_FOLDER, document_id=batch["document_id"])
            path = f"{REPLIES_FOLDER}/{batch['title']}"

            def delivered(current):
                if current and batch["id"] in current.get("deliveries", {}):
                    current["deliveries"][batch["id"]].update(
                        status="delivered", delivered_at=now_iso(), document=path
                    )
                return current

            store.update(name, delivered)
            documents.append(path)
    return documents


def retry_all() -> None:
    """Retry every inbox's outbox; one failed inbox must not block another."""
    import logging

    for record in Store("inbox").all():
        if pending(record):
            try:
                deliver_pending(record["name"])
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "Reply delivery remains pending (%s).", type(exc).__name__
                )
