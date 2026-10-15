# Progress log (autonomous run from 2026-10-15)

Nadine asked for the remaining phases (5 → 8) to run without stopping, merging each phase into `main`. This file records what was done per phase and every decision taken without her, with the reason. The checklist is `docs/DEFINITION_OF_DONE.md`.

## Phase 5 (continued) — CV analysis in the console

Done (merged into `main` 2026-10-15):
- Every extraction now returns a **layout**: page sizes and one entry per text line with its box and confidence (1.0 for a PDF text layer, the recogniser score per segment for OCR). Stored on the document (migration e5c3f4a7b8c9). Word/DOC/RTF CVs get a LibreOffice PDF preview so they can be shown as pages too.
- New engine endpoints: `GET /v1/candidates/{ref}/cv?include_raw=true` (layout, before/after pairs), `GET …/cv/file` (original), `GET …/cv/pages/{n}` (page image in the layout's pixel space); `/v1/documents/inspect` returns layout and page images without storing anything; screening output maps each CV quote to its boxes (`cv.quote_boxes`).
- Console: «تحليل السيرة» (original page with boxes coloured by confidence, extracted lines with confidence, CV evidence that highlights in the text and on the page, redaction before/after) and «جرّب ملف» (same view for any uploaded file, nothing stored). Render-tested in headless Chrome for a scan, a PDF and a Word CV: no JS errors.

Decisions taken alone:
- **Redaction keeps line breaks** when collapsing repeated tokens, so the before/after view can pair lines one to one.
- **Layout in display pixels** (110 dpi for PDFs, native pixels for images): the UI scales one SVG over the page image; no client-side PDF rendering library needed.
- Known limit: redaction removes the word «السعودي» also inside «الهلال الأحمر السعودي» (nationality words are removed everywhere). Privacy-safe, sometimes loses meaning in a quote.
