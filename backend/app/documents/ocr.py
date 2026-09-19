from typing import Protocol, BinaryIO

class OcrEngine(Protocol):
    def extract_text(self, image: BinaryIO) -> str:
        ...

class TesseractEngine:
    def extract_text(self, image: BinaryIO) -> str:
        # Mocking OCR extraction for M5 MVP
        # In a real environment, this would use pytesseract
        return "MOCKED_OCR_TEXT: merchant: OCR Merchant, date: 2026-09-02, amount: 250.00"
