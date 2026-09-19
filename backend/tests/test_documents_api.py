import io
import uuid
import pytest

from app.documents.models import DocumentType, ProcessingStatus, ExtractedItemStatus


@pytest.fixture
def account(client, auth_headers) -> dict:
    return client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={"name": "DocTest Account", "type": "checking", "opening_balance": "0.00"},
    ).json()


def test_upload_valid_document(client, auth_headers):
    file_content = b"%PDF-1.4 mock pdf content"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

    res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert res.status_code == 201

    data = res.json()
    assert data["file_type"] == DocumentType.pdf.value
    assert data["processing_status"] == ProcessingStatus.awaiting_confirmation.value
    assert data["filename"] == "test.pdf"


def test_upload_invalid_magic_bytes(client, auth_headers):
    file_content = b"invalid content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

    res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert res.status_code == 422
    assert "Unsupported file type" in res.json()["error"]["message"]


def test_upload_duplicate_hash(client, auth_headers):
    file_content = b"<?xml version='1.0'?>\n<test>duplicate</test>"

    # First upload
    files1 = {"file": ("test1.xml", io.BytesIO(file_content), "application/xml")}
    res1 = client.post("/api/v1/documents/upload", headers=auth_headers, files=files1)
    assert res1.status_code == 201

    # Second upload with identical content
    files2 = {"file": ("test2.xml", io.BytesIO(file_content), "application/xml")}
    res2 = client.post("/api/v1/documents/upload", headers=auth_headers, files=files2)
    assert res2.status_code == 422
    assert "identical content" in res2.json()["error"]["message"]


def test_confirm_extraction(client, auth_headers, account):
    # 1. Upload file
    file_content = b'{"mock": "json"}'
    files = {"file": ("test.json", io.BytesIO(file_content), "application/json")}
    upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. Get extracted items
    items_res = client.get(f"/api/v1/documents/{doc_id}/items", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0
    item_id = items[0]["id"]

    # 3. Confirm
    payload = {
        "transaction_override": {
            "account_id": account["id"],
            "transaction_type": "expense",
            "description": "Confirmed transaction",
            "amount": "150.00",
            "transaction_date": "2026-09-01",
            "status": "paid"
        }
    }
    confirm_res = client.post(f"/api/v1/documents/items/{item_id}/confirm", headers=auth_headers, json=payload)
    assert confirm_res.status_code == 200

    data = confirm_res.json()
    assert data["status"] == ExtractedItemStatus.edited_confirmed.value
    assert data["created_transaction_id"] is not None


def test_duplicate_item_warning(client, auth_headers, account):
    # 1. Create a manual transaction first
    payload = {
        "account_id": account["id"],
        "transaction_type": "expense",
        "description": "Dummy Merchant",
        "amount": "150.00",
        "transaction_date": "2026-09-01",
    }
    res = client.post("/api/v1/transactions", headers=auth_headers, json=payload)
    assert res.status_code == 201

    # 2. Upload file that parses to the same details
    file_content = b'{"mock": "duplicate-test"}'
    files = {"file": ("test.json", io.BytesIO(file_content), "application/json")}
    upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 3. Get extracted items and check for duplicate warning
    items_res = client.get(f"/api/v1/documents/{doc_id}/items", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0
    assert items[0]["duplicate_reason"] is not None
    assert "Date, amount, and merchant match" in items[0]["duplicate_reason"]

def test_reject_extraction(client, auth_headers):
    # 1. Upload file
    file_content = b'\x89PNG\r\n\x1a\n...mock image...'
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. Get extracted items
    items_res = client.get(f"/api/v1/documents/{doc_id}/items", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0
    item_id = items[0]["id"]

    # 3. Reject
    reject_res = client.post(f"/api/v1/documents/items/{item_id}/reject", headers=auth_headers)
    assert reject_res.status_code == 200

    data = reject_res.json()
    assert data["status"] == ExtractedItemStatus.rejected.value
