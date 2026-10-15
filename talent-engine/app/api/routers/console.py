from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["console"])

PLACEHOLDER = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>Talent Console</title><style>body{font-family:sans-serif;max-width:720px;margin:48px auto;padding:0 16px;line-height:1.8}</style></head>
<body><h1>Talent Console</h1>
<p>واجهة الاختبار الكاملة تُبنى في المرحلة 5. حاليًا استخدمي واجهة الـ API:</p>
<ul><li><a href="/docs">/docs</a> (OpenAPI)</li><li><a href="/health">/health</a> · <a href="/ready">/ready</a></li></ul>
<p>الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة.</p></body></html>"""


@router.get("/console", response_class=HTMLResponse, include_in_schema=False)
def console() -> str:
    return PLACEHOLDER
