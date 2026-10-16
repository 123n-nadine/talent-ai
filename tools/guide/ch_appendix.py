"""Chapter 16: the technical appendix — every inventory item that no narrative page explains, by
category, with its code (searchable in the PDF), its technical name (LTR) and one Arabic line."""

from __future__ import annotations

from explain import explain
from inv import ITEMS
from model import Chapter, Page, Table

CATS = [
    ("screen", "الشاشات والصفحات"), ("button", "الأزرار والإجراءات"), ("doctype", "أنواع البيانات في Frappe"), ("field", "الحقول المضافة"),
    ("endpoint", "طرق الواجهة البرمجية"), ("hook", "الخطوات التلقائية"), ("stage", "المراحل"), ("flag", "الوسوم"), ("status", "الحالات"),
    ("setting", "الإعدادات"), ("role", "الأدوار والمستخدمين"), ("command", "الأوامر والسكربتات"), ("decision", "القرارات والأسئلة"),
    ("evaluation", "نتائج التقييم"), ("security", "الأمان"), ("architecture", "البنية والتثبيت"),
]
ROWS_PER_PAGE = 26


def appendix(claimed: set[str]) -> Chapter:
    pages = []
    for cat, title in CATS:
        items = [it for it in ITEMS if it["cat"] == cat and it["id"] not in claimed]
        if not items:
            continue
        for i in range(0, len(items), ROWS_PER_PAGE):
            part = items[i:i + ROWS_PER_PAGE]
            n = i // ROWS_PER_PAGE + 1
            rows = [[it["code"], it["name"][:90], explain(it)] for it in part]
            pages.append(Page(f"app-{cat}-{n}", f"{title}" + (f" ({n})" if len(items) > ROWS_PER_PAGE else ""), break_before=False, blocks=[
                Table(["الرقم", "الاسم التقني", "معناه"], rows, ltr_cols=(0, 1), widths=(0.11, 0.47, 0.42), small=True),
            ], ids=[it["id"] for it in part]))
    for pg in pages:  # rows may break across pages, but a category title never ends a page alone
        pg.break_before = False
    return Chapter("appendix", "16 — ملحق للفريق التقني: الجرد الكامل", pages,
                   intro="كل بند في الجرد ليه رقم. البنود اللي اتشرحت في فصل، رقمها مكتوب في صندوق «للفريق التقني» في صفحتها؛ والباقي هنا.")
