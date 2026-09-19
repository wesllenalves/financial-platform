import io
import pytest

from app.documents.models import DocumentType


def test_ocr_synthetic_image(client, auth_headers):
    file_content = b'\x89PNG\r\n\x1a\n...synthetic receipt image...'
    files = {"file": ("receipt.png", io.BytesIO(file_content), "image/png")}

    upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    items_res = client.get(f"/api/v1/documents/{doc_id}/items", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0
    assert items[0]["normalized_payload"]["merchant"] == "OCR Merchant"
    assert items[0]["normalized_payload"]["amount"] == "250.00"

def test_scanned_pdf_routing_to_ocr(client, auth_headers):
    file_content = b"%PDF-1.4 mock pdf content SCANNED_IMAGE"
    files = {"file": ("scanned.pdf", io.BytesIO(file_content), "application/pdf")}

    upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    items_res = client.get(f"/api/v1/documents/{doc_id}/items", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0

    # It should have the OCR payload despite being uploaded as a PDF
    assert items[0]["normalized_payload"]["merchant"] == "OCR Merchant"
    assert items[0]["normalized_payload"]["amount"] == "250.00"
