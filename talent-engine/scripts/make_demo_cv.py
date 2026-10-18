"""The scanned CV of the presentation's new applicant (ماجد الشهراني), fictional, in the same shape
and quality as the synthetic scans of `make_cvs.py`, with one line deliberately hard to read so the
analysis screen shows a weak line (round 11). The data matches the application the rehearsal
submits. Checks the result through the engine's /v1/documents/inspect: exactly one line under
OCR_MIN_CONFIDENCE, the rest read.

    uv run python -m scripts.make_demo_cv            # writes data/cvs/demo-majed-cv.jpg
"""

from __future__ import annotations

import os
import random
import sys
import tempfile
from pathlib import Path

import httpx
import pymupdf
from dotenv import load_dotenv  # type: ignore[import-not-found]
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.make_cvs import OUT, build_docx, docx_to_pdf  # noqa: E402

TITLE = "ماجد الشهراني — مشرف وردية أمن"
CONTACT = [
    "الاسم: ماجد الشهراني",
    "الجوال: 0520202002",
    "البريد الإلكتروني: demo.majed@example.com",
    "رقم الهوية الوطنية: 1000009901",
    "تاريخ الميلاد: 20/06/1997",
    "الجنسية: السعودية",
    "الجنس: ذكر",
    "العنوان: حي النخيل، الرياض",
]
BODY = [
    "أعمل مشرف وردية في مجمع سكني بالرياض منذ 2019.",
    "أتابع عمل 8 حراس أمن وأوزع المهام عليهم يوميًا.",
    "خبرة في الحراسة الأمنية تزيد عن 6 سنوات في مواقع مختلفة.",
    "أتولى تنظيم جدول المناوبات الأسبوعي للحراس.",
    "رخصة أمن سارية حتى 2027.",
    "أرفع ملاحظات الوردية شفهيًا للمدير وأسجل الحوادث في دفتر الوردية.",
    "اللغة العربية بطلاقة ولدي إلمام بالإنجليزية.",
    "حاصل على الثانوية العامة.",
]
WEAK = BODY[5]  # the line the scanner "smudged"
DEST = OUT / "demo-majed-cv.jpg"


def scan(
    pdf_path: Path,
    jpg_path: Path,
    seed: int,
    smudge: float,
    noise: float = 0.0012,
    blur: float = 0.3,
) -> None:
    """`make_cvs.pdf_to_scan` with a lighter base noise, plus a blurred, faded band over one line
    (found by its text block: a full-line search fails on the visually ordered Arabic text)."""
    rng = random.Random(seed)
    with pymupdf.open(pdf_path) as doc:
        page = doc[0]
        blocks = [b for b in page.get_text("blocks") if "الوردية" in b[4] and "دفتر" in b[4]]
        assert blocks, "the weak line's text block was not found"
        x0 = min(b[0] for b in page.get_text("blocks")) - 2
        x1 = max(b[2] for b in page.get_text("blocks")) + 2
        y0, y1 = blocks[0][1], blocks[0][3]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        k = 200 / 72
        box = (max(0, int(x0 * k)), int(y0 * k) - 2, min(img.width, int(x1 * k)), int(y1 * k) + 2)
        band = img.crop(box).filter(ImageFilter.GaussianBlur(radius=smudge))
        band = Image.blend(band, Image.new("RGB", band.size, (205, 205, 200)), 0.35)  # faded ink
        img.paste(band, box)
    img = img.rotate(rng.uniform(-1.2, 1.2), expand=True, fillcolor=(245, 245, 240))
    img = img.filter(ImageFilter.GaussianBlur(radius=blur))
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * noise)):
        x, y = rng.randrange(w), rng.randrange(h)
        v = rng.choice((40, 60, 200, 230))
        px[x, y] = (v, v, v)
    img = img.convert("L").convert("RGB")
    img.save(jpg_path, "JPEG", quality=75)


def inspect(jpg_path: Path) -> tuple[list[float], float]:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    api = os.environ.get("API_URL", f"http://127.0.0.1:{os.environ.get('API_PORT', '18000')}")
    key = os.environ.get("TENANT_API_KEY", "")
    with open(jpg_path, "rb") as fh:
        r = httpx.post(
            f"{api}/v1/documents/inspect",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (jpg_path.name, fh, "image/jpeg")},
            timeout=300,
        )
    r.raise_for_status()
    d = r.json()
    doc = d.get("document", d)
    lines = [float(ln.get("c") or 0) for ln in (doc.get("layout") or {}).get("lines", [])]
    return lines, float(os.environ.get("OCR_MIN_CONFIDENCE", "0.80"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="talentai-demo-cv-") as tmp:
        work = Path(tmp)
        docx = work / "demo-majed-cv.docx"
        build_docx(docx, TITLE, CONTACT + [""] + BODY)
        pdf = docx_to_pdf(docx, work)
        for noise, blur in ((0.0012, 0.3), (0.0009, 0.3), (0.0015, 0.35)):
            for smudge in (1.6, 2.0, 2.5):
                scan(pdf, DEST, seed=41, smudge=smudge, noise=noise, blur=blur)
                confs, thr = inspect(DEST)
                weak = [i for i, c in enumerate(confs) if c < thr]
                print(
                    f"noise {noise} blur {blur} smudge {smudge}: {len(confs)} lines, weak {weak}, min {min(confs) if confs else None}"
                )
                if len(weak) == 1 and len(confs) >= 15:
                    print("ok ->", DEST)
                    return 0
    print("could not get exactly one weak line; keep the last image and look at it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
