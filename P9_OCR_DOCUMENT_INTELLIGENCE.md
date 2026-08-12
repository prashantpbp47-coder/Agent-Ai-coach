# P9 — OCR / Document Intelligence

P9 adds a provider-neutral document pipeline around the existing P6 customer-document intake.

## Flow
1. Agent/customer submits RC, policy or supported document metadata.
2. Document is persisted with `ocr_status=pending`.
3. A configured OCR/document provider can write an extraction result through the P9 extraction API.
4. RC extraction populates `vehicle_intelligence` fields such as registration number, owner, make/model, fuel and policy expiry.
5. A human/user explicitly verifies the extracted data.
6. Only verified RC data can reach the `quote-ready` boundary.

## Important boundary
P9 does not claim that OCR is live until a real OCR provider is configured. `POST /api/p9/documents/<id>/extractions` is the provider-neutral adapter boundary.

## APIs
- `POST /api/p9/documents`
- `GET /api/p9/documents/<document_id>`
- `POST /api/p9/documents/<document_id>/extractions`
- `POST /api/p9/documents/<document_id>/verify`
- `POST /api/p9/documents/<document_id>/quote-ready`

Critical quote/issuance decisions must continue to use an approved provider after human verification.
