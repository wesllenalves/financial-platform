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
        # Just mock a result
        items = [{
            "transaction_date": "2026-09-01",
            "amount": "150.00",
            "description": f"Parsed {file_type.value} document",
            "merchant": "Dummy Merchant"
        }]
        return ParserResult(items=items, metadata={"parser": "dummy"}, confidence=0.85)

# Registry
PARSER_REGISTRY: dict[DocumentType, DocumentParser] = {
    DocumentType.pdf: DummyParser(),
    DocumentType.xml: DummyParser(),
    DocumentType.json: DummyParser(),
    DocumentType.png: DummyParser(),
    DocumentType.jpeg: DummyParser(),
}
