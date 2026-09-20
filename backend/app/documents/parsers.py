from typing import Protocol, BinaryIO

from app.documents.models import DocumentType


class ParserResult:
    def __init__(self, items: list[dict], metadata: dict, confidence: float):
        self.items = items
        self.metadata = metadata
        self.confidence = confidence


class DocumentParser(Protocol):
    def parse(self, file: BinaryIO, file_type: DocumentType) -> ParserResult:
        ...


class DummyParser:
    """A dummy parser that mocks extraction for MVP/testing purposes without real LLM/OCR."""

    def parse(self, file: BinaryIO, file_type: DocumentType) -> ParserResult:
        content = file.read()

        # If it's a PDF and it explicitly says it's scanned (mock for testing), route to OCR
        if file_type == DocumentType.pdf and b"SCANNED_IMAGE" in content:
            file.seek(0)
            return OcrParser().parse(file, DocumentType.png)

        # Just mock a result
        items = [{
            "transaction_date": "2026-09-01",
            "amount": "150.00",
            "description": f"Parsed {file_type.value} document",
            "merchant": "Dummy Merchant"
        }]
        return ParserResult(items=items, metadata={"parser": "dummy"}, confidence=0.85)

class OcrParser:
    def __init__(self):
        from app.documents.ocr import TesseractEngine
        self.engine = TesseractEngine()

    def parse(self, file: BinaryIO, file_type: DocumentType) -> ParserResult:
        text = self.engine.extract_text(file)

        # Mocking finding items inside the extracted OCR text
        items = [{
            "transaction_date": "2026-09-02",
            "amount": "250.00",
            "description": "OCR Extracted Receipt",
            "merchant": "OCR Merchant"
        }]
        return ParserResult(items=items, metadata={"parser": "ocr", "raw_text": text}, confidence=0.70)

# Registry
PARSER_REGISTRY: dict[DocumentType, DocumentParser] = {
    DocumentType.pdf: DummyParser(),
    DocumentType.xml: DummyParser(),
    DocumentType.json: DummyParser(),
    DocumentType.png: OcrParser(),
    DocumentType.jpeg: OcrParser(),
}
