"""Playwright helpers for the Talent AI checks: log in like a person, capture whole elements (the
desk scrolls inside a container), audit the layout (overlapping or cut text, overflow, small
fonts, weak contrast) and time page loads. Uses the server's Chrome (`channel="chrome"`)."""

from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page, async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE = os.environ.get("TAI_BASE", "http://127.0.0.1:18050")
CONSOLE = os.environ.get("TAI_CONSOLE", "http://127.0.0.1:18000")
VIEWPORTS = {"1100": (1100, 800), "1366": (1366, 768), "1440": (1440, 900), "1920": (1920, 1080), "m375": (375, 812), "m390": (390, 844)}


def env(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.rstrip("\n").split("=", 1)
            out[k.strip()] = v.split("#")[0].strip() if k.strip() != "CONSOLE_PASSWORD" else v.strip()
    return out


DEV = env(os.path.join(ROOT, "dev-frappe", ".env"))
ENG = env(os.path.join(ROOT, "talent-engine", ".env"))


@asynccontextmanager
async def browser():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True, args=["--font-render-hinting=none"])
        try:
            yield b
        finally:
            await b.close()


async def new_page(b: Browser, viewport: str = "1440", scale: float = 1, locale: str = "ar-SA") -> Page:
    w, h = VIEWPORTS[viewport]
    mobile = viewport.startswith("m")
    ctx = await b.new_context(
        viewport={"width": w, "height": h}, device_scale_factor=scale, locale=locale, is_mobile=mobile, has_touch=mobile,
        timezone_id="Asia/Riyadh", accept_downloads=True,
    )
    page = await ctx.new_page()
    page.errors = []  # type: ignore[attr-defined]
    page.on("pageerror", lambda e: page.errors.append(str(e)))  # type: ignore[attr-defined]
    page.on("console", lambda m: page.errors.append("console: " + m.text) if m.type == "error" and "favicon" not in m.text else None)  # type: ignore[attr-defined]
    return page


async def login_desk(page: Page, user: str, password: str, via_form: bool = True) -> float:
    """Log in through the real login page (or the API). Returns the seconds until the desk is ready."""
    t0 = time.time()
    if via_form:
        await page.goto(BASE + "/login")
        await page.fill("#login_email", user)
        await page.fill("#login_password", password)
        await page.click(".btn-login")
        await page.wait_for_url("**/desk**", timeout=90000)
    else:
        await page.goto(BASE + "/login")
        st = await page.evaluate(
            """([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
                body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [user, password])
        assert st == 200, f"login {user}: HTTP {st}"
        await page.goto(BASE + "/desk")
    await page.wait_for_function("window.frappe && frappe.boot && frappe.boot.user", timeout=90000)
    return round(time.time() - t0, 2)


async def login_console(page: Page, user: str, password: str) -> float:
    t0 = time.time()
    await page.goto(CONSOLE + "/console/login")
    await page.fill("input[name=username]", user)
    await page.fill("input[name=password]", password)
    await page.click("button[type=submit]")
    await page.wait_for_url("**/console**", timeout=60000)
    await page.wait_for_function("!!document.querySelector('#screen') && !document.querySelector('#screen .spin')", timeout=60000)
    return round(time.time() - t0, 2)


async def settle(page: Page, extra: float = 1.0, timeout: int = 60000) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    try:
        await page.wait_for_function("!document.querySelector('.tai .spin, #screen .spin, .frappe-control .spin')", timeout=timeout)
    except Exception:
        pass
    await asyncio.sleep(extra)


async def goto_timed(page: Page, url: str, ready: str | None = None, timeout: int = 90000) -> float:
    """Open a URL and return seconds until `ready` (a JS condition) is true, or until the network is idle."""
    t0 = time.time()
    await page.goto(url if url.startswith("http") else BASE + url)
    if ready:
        await page.wait_for_function(ready, timeout=timeout)
    else:
        await settle(page, 0)
    return round(time.time() - t0, 2)


async def content_height(page: Page) -> int:
    return await page.evaluate(
        """() => { let m = document.documentElement.scrollHeight;
        document.querySelectorAll('*').forEach(el => { const cs = getComputedStyle(el);
          if (el.scrollHeight > el.clientHeight + 20 && /(auto|scroll)/.test(cs.overflowY)) m = Math.max(m, el.scrollHeight + el.getBoundingClientRect().top); });
        return Math.ceil(m); }"""
    )


async def shot(page: Page, path: str, selector: str | None = None, full: bool = False, max_h: int = 14000, pad: int = 0) -> str:
    """Screenshot one element (whole, even if the desk scrolls inside a container) or the page."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    vp = page.viewport_size or {"width": 1440, "height": 900}
    grow = full or selector
    if grow:
        h = min(max(await content_height(page), vp["height"]), max_h)
        if h > vp["height"]:
            await page.set_viewport_size({"width": vp["width"], "height": h})
            await asyncio.sleep(0.8)
    try:
        if selector:
            loc = page.locator(selector).first
            await loc.wait_for(state="visible", timeout=30000)
            if pad:
                box = await loc.bounding_box()
                await page.screenshot(path=path, clip={"x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
                                                      "width": min(box["width"] + 2 * pad, vp["width"]), "height": box["height"] + 2 * pad})
            else:
                await loc.screenshot(path=path)
        else:
            try:
                await page.screenshot(path=path, full_page=False)
            except Exception as e:  # Chrome sometimes refuses one capture ("Unable to capture screenshot"); try once more
                if "Unable to capture" not in str(e):
                    raise
                await asyncio.sleep(1.5)
                await page.screenshot(path=path, full_page=False)
    finally:
        if grow:
            await page.set_viewport_size(vp)
            await asyncio.sleep(0.3)
    return path


AUDIT_JS = r"""
(rootSel) => {
  const roots = Array.from(document.querySelectorAll(rootSel)).filter(r => r.getBoundingClientRect().width > 0);
  const W = document.documentElement.clientWidth;
  const issues = [];
  if (document.documentElement.scrollWidth > W + 2) issues.push({type: 'page-overflow', detail: document.documentElement.scrollWidth + ' > ' + W});
  const path = (el) => { const p = []; for (let e = el; e && e !== document.body && p.length < 5; e = e.parentElement) {
      p.unshift(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.classList.length ? '.' + Array.from(e.classList).slice(0, 2).join('.') : '')); } return p.join(' > '); };
  const lum = (c) => { const m = c.match(/[\d.]+/g); if (!m) return null; const [r, g, b] = m.slice(0, 3).map(v => { v = v / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      return { L: 0.2126 * r + 0.7152 * g + 0.0722 * b, a: m.length > 3 ? parseFloat(m[3]) : 1 }; };
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor; const l = lum(c); if (l && l.a > 0.5) return l.L; } return 1; };
  const leaves = [];
  const seen = new Set();
  for (const root of roots) {
    root.querySelectorAll('*').forEach(el => {
      if (seen.has(el)) return; seen.add(el);
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.3) return;
      if (el.closest('svg') && el.tagName !== 'svg') return;
      // the content of a closed <details> is not on screen (Chrome still reports its boxes)
      const closed = el.closest('details:not([open])'); if (closed && !el.closest('summary')) return;
      const texts = Array.from(el.childNodes).filter(n => n.nodeType === 3 && n.textContent.trim().length > 0);
      if (!texts.length) return;
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const fs = parseFloat(cs.fontSize);
      if (fs < 11.5) issues.push({type: 'small-font', where: path(el), detail: fs + 'px', text: el.textContent.trim().slice(0, 40)});
      if (el.scrollWidth > el.clientWidth + 2 && (cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis') && cs.display !== 'inline')
        issues.push({type: 'cut-text', where: path(el), text: el.textContent.trim().slice(0, 60)});
      const fg = lum(cs.color); const bg = bgOf(el);
      if (fg) { const hi = Math.max(fg.L, bg), lo = Math.min(fg.L, bg); const ratio = (hi + 0.05) / (lo + 0.05);
        const large = fs >= 18 || (fs >= 14 && parseInt(cs.fontWeight) >= 600);
        if (ratio < (large ? 3 : 4.5)) issues.push({type: 'low-contrast', where: path(el), detail: ratio.toFixed(2) + ':1', text: el.textContent.trim().slice(0, 40)}); }
      const rects = [];
      texts.forEach(t => { const rg = document.createRange(); rg.selectNodeContents(t); Array.from(rg.getClientRects()).forEach(b => { if (b.width > 1 && b.height > 1) rects.push(b); }); });
      if (rects.length) leaves.push({el, rects});
      // text squeezed into a column too narrow for it (one or two letters per line)
      const lines = new Set(rects.map(b => Math.round(b.top))).size;
      const chars = texts.reduce((n, t) => n + t.textContent.trim().length, 0);
      if (lines >= 3 && chars / lines < 3) issues.push({type: 'squeezed-text', where: path(el), detail: lines + ' lines', text: el.textContent.trim().slice(0, 40)});
      // text sticking out of a box that does not scroll
      const pr = el.parentElement && el.parentElement.getBoundingClientRect();
      rects.forEach(b => { if (b.right > W + 2 || b.left < -2) issues.push({type: 'off-screen-text', where: path(el), text: el.textContent.trim().slice(0, 40)}); });
    });
  }
  // overlapping text of two different elements
  for (let i = 0; i < leaves.length; i++) for (let j = i + 1; j < leaves.length; j++) {
    const a = leaves[i], b = leaves[j];
    if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    let hit = null;
    for (const x of a.rects) { for (const y of b.rects) {
      const w = Math.min(x.right, y.right) - Math.max(x.left, y.left), h = Math.min(x.bottom, y.bottom) - Math.max(x.top, y.top);
      if (w > 3 && h > 3) { hit = w * h; break; } } if (hit) break; }
    if (hit) issues.push({type: 'overlap', where: path(a.el) + '  ⟷  ' + path(b.el), text: a.el.textContent.trim().slice(0, 30) + ' | ' + b.el.textContent.trim().slice(0, 30)});
  }
  const fonts = {plex: document.fonts.check('16px "IBM Plex Sans Arabic"', 'عربي'), dir: (roots[0] && getComputedStyle(roots[0]).direction) || document.dir};
  return {issues, fonts, count: leaves.length};
}
"""


async def audit(page: Page, root: str) -> dict:
    return await page.evaluate(AUDIT_JS, root)


def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------------------- calls from the page
async def xcall(page: Page, method: str, args: dict | None = None):
    """frappe.xcall as the logged-in user; errors come back as {"__error__": message}."""
    return await page.evaluate(
        """([m, a]) => frappe.xcall(m, a).then(r => r, e => ({__error__: String((e && (e.message || e.exc_type)) || e)}))""",
        [method, args or {}],
    )


async def call_status(page: Page, path: str, args: dict | None = None, method: str = "GET", needles: list[str] | None = None) -> dict:
    """HTTP status of one call as the page's user (desk, website or guest); `needles` are looked up
    in the whole reply (only true/false comes back, so a secret used as a needle is never copied)."""
    return await page.evaluate(
        """async ([path, args, method, needles]) => {
          const tok = (window.frappe && frappe.csrf_token) || (window.csrf_token) || '';
          let url = path; const opt = {method, headers: {'Accept': 'application/json', 'X-Frappe-CSRF-Token': tok}, credentials: 'same-origin'};
          if (method === 'GET' && args) url += (url.includes('?') ? '&' : '?') + new URLSearchParams(Object.entries(args).map(([k, v]) => [k, typeof v === 'string' ? v : JSON.stringify(v)]));
          else if (args) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(args); }
          const r = await fetch(url, opt); const txt = await r.text();
          return {status: r.status, body: txt.slice(0, 400), type: r.headers.get('content-type') || '',
                  found: Object.fromEntries((needles || []).map((n, i) => [i, txt.includes(n)]))};
        }""",
        [path, args, method, needles or []],
    )


async def wait_value(page: Page, doctype: str, name: str, field: str, ok, timeout: float = 300, every: float = 1.5):
    t0 = time.time()
    val = None
    while time.time() - t0 < timeout:
        r = await xcall(page, "frappe.client.get_value", {"doctype": doctype, "filters": name, "fieldname": field})
        val = r.get(field) if isinstance(r, dict) else None
        if ok(val):
            return val, round(time.time() - t0, 1)
        await asyncio.sleep(every)
    return val, None


def compact_png(path: str, colors: int = 256) -> str:
    """UI screenshots as 8-bit PNG: same look, about a third of the size (guide and report)."""
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(path, optimize=True)
    return path
