"""Inventory items with stable ids (SC-001, EP-012 …), shared by the guide and COVERAGE.md."""

from __future__ import annotations

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PREFIX = {"screen": "SC", "button": "BT", "doctype": "DT", "field": "FD", "endpoint": "EP", "hook": "HK", "stage": "SG", "flag": "FL",
          "status": "SS", "setting": "SE", "role": "RL", "command": "CM", "decision": "DC", "evaluation": "EV", "security": "SY", "architecture": "AR"}


def load() -> list[dict]:
    items = json.load(open(os.path.join(ROOT, "docs", "guide", "inventory.json"), encoding="utf-8"))
    seen: dict[str, int] = {}
    for it in items:  # inventory.json keeps the order of the code, so ids are stable between runs
        p = PREFIX[it["cat"]]
        seen[p] = seen.get(p, 0) + 1
        it["code"] = f"{p}-{seen[p]:03d}"
    return items


ITEMS = load()
BY_ID = {it["id"]: it for it in ITEMS}


def code(iid: str) -> str:
    return BY_ID[iid]["code"]


def line(iid: str, text: str | None = None) -> str:
    """A technical-box line: «EP-012 GET /v1/jobs/{ref}/ranking»."""
    it = BY_ID[iid]
    return f"{it['code']} {text or it['name']}"


def find(cat: str, pred) -> list[dict]:
    return [it for it in ITEMS if it["cat"] == cat and pred(it)]
