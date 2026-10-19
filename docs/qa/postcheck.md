| area | case | expected | actual | result |
|---|---|---|---|---|
| files | 0-byte file (after Q6) | refused in the form and by the endpoint with «ملف السيرة فارغ»; nothing saved | form: refused راجع ما يلي:
ملف السيرة فارغ — ارفع الملف الصحيح أو اتركه بدون سيرة / ملف السيرة فارغ — ارفع الملف الصحيح أو اتركه بدون سيرة; endpoint HTTP 422 True; saved 0 | PASS |
| text | HTML/script in the name and a free answer | no script runs; stored and shown as harmless text | stored name '<img src="x">عمر'; stored answer '<b>مشرف</b> وردية منذ 2019'; injected element False; alerts 0; ai_status Completed | PASS |
| files | multi-page PDF (3 pages) | all pages read | ai_status Completed after 33.0s; method pdf_text; pages 3; chars 1650; flags [] | PASS |
| security | public-form rate limit (5 per 10 min for the probe) | at most 5 accepted in the window, then 429 only; normal again after the limit is restored | codes [200, 200, 200, 200, 429, 429, 429, 429]; after restoring 100: HTTP 200 | PASS |
| behaviour | restart engine Redis mid-processing (with restart: on-failure) | workers back by themselves; the application not lost | restart took 44.6s; workers before 4, back after 69.3s (4 up); ai_status after 5 min: Completed (8.6s); flags ['quote_not_found'] | PASS |
| behaviour | engine Redis down when an application arrives (after Q7b) | Failed with a reason (never stuck); workers back; HR retry → assessed; no screening left «queued» | Failed after 30.4s (3/3 attempts: خطأ في محرك الذكاء 503: queue unavailable, try again); workers back 0.1s after the start; retry ok → Completed in 12.3s; engine screenings ['failed', 'failed', 'failed', 'completed'] | PASS |
