| area | case | expected | actual | result |
|---|---|---|---|---|
| files | 0-byte file | saved; CV unreadable, assessed from the answers | saved; ai_status Completed after 12.6s; flags []; cv status None method None pages None conf None chars None | FAIL |
| files | wrong file type (.exe) | refused with a clear message (type not supported); nothing saved with a bad file | refused at submission: راجع ما يلي:
نوع ملف السيرة غير مدعوم (PDF أو Word أو صورة) / نوع ملف السيرة غير مدعوم (PDF أو Word أو صورة) | PASS |
| files | huge file (11 MB) | refused: larger than 10 MB | refused at submission: راجع ما يلي:
حجم ملف السيرة أكبر من 10 ميجابايت / حجم ملف السيرة أكبر من 10 ميجابايت | PASS |
| files | password-protected PDF | saved; CV unreadable, assessed from the answers | saved; ai_status Completed after 10.5s; flags ['cv_unreadable']; cv status None method None pages None conf None chars None | PASS |
| files | multi-page PDF (3 pages) | saved; all pages read | saved; ai_status Completed after 35.3s; flags []; cv status None method None pages None conf None chars None | FAIL |
| files | DOCX CV | saved; read as text | saved; ai_status Completed after 39.3s; flags []; cv status None method None pages None conf None chars None | PASS |
| files | rotated scan (90°) | saved; OCR weak or unreadable, never a crash | saved; ai_status Needs Review after 40.8s; flags ['low_ocr_confidence']; cv status None method None pages None conf None chars None | PASS |
| files | low-quality photo | saved; low confidence → needs review or weak lines | saved; ai_status Needs Review after 43.7s; flags ['low_ocr_confidence']; cv status None method None pages None conf None chars None | PASS |
| files | fully English scanned CV | saved; OCR reads English (report confidence) | saved; ai_status Completed after 43.7s; flags []; cv status None method None pages None conf None chars None | PASS |
| text | very long free answer (5,000 chars) | saved; shown as plain text; evaluation runs | saved; ai_status Completed after 10.2s; flags []; injected element: False; literal tags visible: True; alerts: 0 | PASS |
| text | emoji in name and answer | saved; shown as plain text; evaluation runs | saved; ai_status Completed after 10.3s; flags []; injected element: False; literal tags visible: True; alerts: 0 | PASS |
| text | mixed Arabic/English | saved; shown as plain text; evaluation runs | saved; ai_status Completed after 10.4s; flags []; injected element: False; literal tags visible: True; alerts: 0 | PASS |
| text | HTML/script in text fields | saved; shown as plain text; evaluation runs | saved; ai_status Completed after 10.3s; flags []; injected element: False; literal tags visible: False; alerts: 0 | FAIL |
| behaviour | double submit (two clicks) | one application | 1 application(s) for the e-mail; button disabled while sending | PASS |
| behaviour | 20 concurrent submissions (10 with a CV) | all saved; all assessed; none failed | 20/20 saved in 0.8s; 20 assessed after 132s; failed 0; codes [200] | PASS |
| behaviour | restart engine worker mid-processing | the application is not lost: assessed later (or Failed with retry), never stuck | restart took 61.0s; ai_status Completed after 10.5s from the restart; flags ['quote_not_found'] | PASS |
| behaviour | restart engine Redis mid-processing | the application is not lost: assessed later (or Failed with retry), never stuck | restart took 50.3s; ai_status Processing after Nones from the restart; flags [] | FAIL |
| security | API key in the public page source | absent | key present: False; 'Bearer' in page: False | PASS |
| security | desk pages without login | redirect to login | HTTP 301 | PASS |
| security | engine /console without credentials | console → login; /v1 → 401; docs: report | HTTP 303 | PASS |
| security | engine /docs without credentials | console → login; /v1 → 401; docs: report | HTTP 200 (API docs follow API_DOCS_ENABLED: on in dev, off when APP_ENV=production — Q2; no secrets in them, the port is loopback + Tailscale only) | PASS |
| security | engine /openapi.json without credentials | console → login; /v1 → 401; docs: report | HTTP 200 (API docs follow API_DOCS_ENABLED: on in dev, off when APP_ENV=production — Q2; no secrets in them, the port is loopback + Tailscale only) | PASS |
| security | engine /v1/jobs without credentials | console → login; /v1 → 401; docs: report | HTTP 401 | PASS |
| security | engine /v1/settings without credentials | console → login; /v1 → 401; docs: report | HTTP 401 | PASS |
| security | public-form rate limit (5 per 10 min for the probe) | the sixth and later submissions refused with 429 | codes [200, 200, 200, 200, 200, 200, 200, 200] | FAIL |
