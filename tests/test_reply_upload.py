"""Cloud reply identity must survive retries without replacing annotated data."""

from unittest.mock import Mock

import pytest

from remarkable_mcp.transports.sync import Document, RemarkableClient, load_client_from_token

DOC_ID = "11111111-2222-4333-8444-555555555555"


def test_existing_reply_is_returned_without_writing(monkeypatch):
    client = RemarkableClient(user_token="synthetic")
    existing = Document(id=DOC_ID, hash="annotated", name="Reply", doc_type="DocumentType")
    monkeypatch.setattr(client, "get_meta_items", lambda: [existing])
    upload = Mock(side_effect=AssertionError("Existing reply must not be replaced"))
    monkeypatch.setattr(client, "_upload_file_blob", upload)
    assert client.upload_document(b"retry", "Reply", "pdf", document_id=DOC_ID) is existing
    upload.assert_not_called()


def test_reply_created_during_upload_is_not_duplicated(monkeypatch):
    client = RemarkableClient(user_token="synthetic")
    monkeypatch.setattr(client, "get_meta_items", lambda: [])
    monkeypatch.setattr(client, "_page_layout", lambda *args: (1, ["page"]))
    monkeypatch.setattr(client, "_upload_file_blob", lambda *args: {})
    monkeypatch.setattr(client, "_upload_doc_index", lambda *args: {"id": DOC_ID, "hash": "new"})
    # Another sync committed this reply, possibly with pen strokes, after our listing.
    entries = [{"id": DOC_ID, "hash": "annotated"}]
    committed = []
    monkeypatch.setattr(client, "_sync_root", lambda mutate: committed.extend(mutate(entries)))
    client.upload_document(b"retry", "Reply", "pdf", document_id=DOC_ID)
    assert committed == entries


def test_invalid_token_error_does_not_echo_supplied_value():
    token = "synthetic-private-token-text"
    with pytest.raises(ValueError) as exc:
        load_client_from_token(token)
    assert token not in str(exc.value)
    assert token[:20] not in str(exc.value)
