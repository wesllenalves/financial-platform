# Document Processing

Status: proposed

## 1. Pipeline

```
Upload → Validate → Classify → Parse/OCR → Extract → Normalize → Validate → Detect duplicates
       → Stage as extracted_items (status: awaiting_confirmation)
       → User confirms / edits / rejects → Create transactions
```

Each stage is a pure-ish function over an explicit context object, so any stage can be
tested with a fixture and replaced without touching the others. The pipeline runs
synchronously inside the upload request in the MVP; the stage boundary makes moving it to
a worker a change of caller, not of logic.

**Nothing in this pipeline writes to `transactions`.** Only the confirmation endpoint
does. This is the spec's critical document rule enforced by structure rather than by
discipline.

## 2. Upload and validation

Rejected before anything is read into memory:

- size over 10 MB
- extension not in the allowlist (`pdf`, `xml`, `json`, `png`, `jpg`, `jpeg`)
- content-type mismatch with sniffed magic bytes — the sniffed type wins and the
  extension is ignored from then on

Other safety measures:

- Stored under a generated UUID path; the original filename is only metadata and is
  sanitized before display. No user-controlled path segment ever reaches the filesystem.
- PDFs are parsed with JavaScript execution and external resource loading disabled;
  encrypted PDFs are rejected with a clear message.
- XML is parsed with `defusedxml`: no DTDs, no external entities, no entity expansion
  (XXE and billion-laughs).
- JSON parsing has a depth and element-count limit.
- Images are re-encoded through Pillow before OCR, which strips embedded payloads; decompression-bomb limits are enabled.
- SHA-256 of the bytes is computed at upload and unique per user, so identical re-uploads
  are refused immediately.

## 3. Classification

Cheap deterministic rules first:

- magic bytes → format
- for XML: root element (`nfeProc`/`NFe`/`CFe` → Brazilian electronic invoice)
- for PDF: does it have a text layer? (text-PDF vs scanned-image-PDF)
- text heuristics → boleto (presence of a 47-digit `linha digitável`), card statement,
  receipt, invoice

Only when the document remains unclassified does an LLM classification step run. The
outcome selects the parser and the extraction profile.

## 4. Parsers

All parsers implement:

```python
class DocumentParser(Protocol):
    def supports(self, doc: ClassifiedDocument) -> bool: ...
    def parse(self, doc: ClassifiedDocument) -> ParseResult: ...   # text + structured fragments + per-field confidence
```

Registered in a registry and selected by `supports`, so adding a format is adding a file.

**PDF** — `pypdf` for the text layer; `pdfplumber` for table-shaped statements. Extracts
vendor, amount, due date, issue date, document/invoice number, barcode line, description.
If the text layer is empty, the document is routed to the image path.

**XML** — a generic structured-XML reader plus a dedicated NF-e/NFC-e profile. The NF-e
profile maps `infNFe/emit/xNome` → merchant, `ICMSTot/vNF` → amount, `ide/dhEmi` → date,
`infNFe/@Id` → document identifier, and item lines when present. Brazilian invoice
support is isolated in one module (`parsers/nfe/`) so other layouts do not leak into it.

**JSON** — an explicit import schema (documented and versioned) plus a tolerant mode that
maps common field names. Unknown fields are preserved in `raw_payload`, never silently
dropped.

**Image (PNG/JPEG) and scanned PDF** — OCR behind an interface:

```python
class OcrEngine(Protocol):
    def extract_text(self, image: bytes, *, languages: list[str]) -> OcrResult: ...
```

`TesseractOcrEngine` first (`por`+`eng`); `LlmVisionOcrEngine` behind the same interface
for hard documents. Pre-processing: deskew, grayscale, contrast normalization. OCR
confidence per block flows into field confidence.

## 5. Extraction

Two-tier, deterministic first:

1. **Rule-based extraction** — regexes and layout anchors for amounts (`R$ 1.234,56`),
   dates (`dd/mm/yyyy`, `dd/mm/yy`, written months), CNPJ/CPF, boleto digit lines,
   NF-e keys. High confidence, zero cost, fully testable.
2. **LLM extraction** — only for fields the rules did not fill, using
   `structured_output` with a strict schema. The model receives the extracted text (or
   the image, for vision), never the raw file. Every field it returns is marked
   `source: llm` and carries a lower confidence ceiling.

Field confidence is computed, not guessed: rule hit with a strong anchor = 0.95, rule hit
without anchor = 0.8, OCR-derived = OCR block confidence × 0.9, LLM-only = 0.6 capped.
Document confidence is the minimum of the required fields' confidences. The thresholds
live in one config module and are unit-tested.

## 6. Normalization

Brazilian formats are the default and the source of most bugs, so normalization is
explicit and heavily tested:

- **Amounts**: `1.234,56` → `Decimal("1234.56")`; handle `R$`, thin spaces, trailing
  `-`/`CR`/`D`. Never `float`.
- **Dates**: day-first parsing; two-digit years resolved against the document context; a
  date with no year stays `null` rather than being guessed.
- **Merchant**: uppercase-strip, remove legal suffixes (LTDA, ME, EIRELI, S/A), collapse
  card-statement noise (`*`, store numbers, city codes) → `merchant_normalized`.
- **Documents**: CNPJ/CPF validated by check digits; invalid ones are kept as text but
  not used as identifiers.
- **Category**: merchant rules table first (`IFOOD` → Delivery); LLM suggestion only for
  the remainder; always a suggestion, never a silent assignment.
- **Direction**: income vs expense from the document type and sign conventions, defaulting
  to expense for invoices/boletos/receipts.

## 7. Duplicate detection

Runs before staging, produces **warnings only** — nothing is deleted or merged
automatically.

| Signal | Strength |
| --- | --- |
| identical file hash for this user | exact — upload rejected at step 1 |
| same NF-e key / invoice number / boleto line | exact — flagged as certain duplicate |
| same `merchant_normalized` + same amount + date within ±3 days | strong |
| same amount + same due date + same account | moderate |
| recurring series already containing this month's occurrence | weak, informational |

Each candidate carries `duplicate_of_transaction_id` and a human-readable reason shown in
the confirmation UI ("looks like the R$ 89,90 Netflix charge already recorded on 03/10").
The user decides.

## 8. Confirmation UI contract

After processing, the API returns per extracted item:

```
merchant, amount, transaction_date, due_date, suggested_category,
payment_method, per-field confidence, overall confidence,
duplicate warning (if any), source (rule | ocr | llm) per field
```

The UI shows low-confidence fields (< 0.8) highlighted and requires a look before
confirming. Actions: **Confirm**, **Edit and confirm**, **Reject**. Rejecting keeps the
document and the extraction for audit; it creates nothing.

Confirmation creates the transaction in one database transaction, links it back to the
`extracted_item` and the `document`, and writes an audit-log entry. Every user edit at
this step is recorded — that data is the training signal for improving extraction later.

## 9. Testing

Fixtures are **synthetic documents only** — generated boletos, NF-e XMLs, receipts and
statements with fake CNPJs and invented merchants. No real personal financial documents
enter the repository.

Test layers: per-parser golden-file tests; normalization property tests (amount and date
round-trips); duplicate-detection matrix tests; an end-to-end test per format
(upload → confirm → transaction exists with the right `Decimal`); and negative tests for
XXE, zip/decompression bombs, oversized files, wrong magic bytes and path traversal in
filenames.
