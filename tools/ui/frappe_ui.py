"""Headless Chrome over CDP against the local Frappe site: log in, open pages, run JS, screenshot.

Usage as a library: `async with Browser(base, shots) as b: await b.login(user, pw); await b.go(path); await b.shot(name)`."""
import asyncio, base64, json, os, subprocess, tempfile, time, urllib.request

import websockets

CHROME = "/opt/google/chrome/chrome"


class Browser:
    def __init__(self, base, shots, port=18091, width=1440, height=1000, lang="ar"):
        self.base, self.shots, self.port, self.w, self.h = base.rstrip("/"), shots, port, width, height
        self.errors, self.mid = [], 0
        os.makedirs(shots, exist_ok=True)

    async def __aenter__(self):
        prof = tempfile.mkdtemp(prefix="tai-chrome-")
        self.proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={self.port}", "--remote-debugging-address=127.0.0.1",
                                      f"--user-data-dir={prof}", "--no-first-run", "--no-default-browser-check", "--disable-gpu", "--lang=ar",
                                      f"--window-size={self.w},{self.h}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tabs = []
        for _ in range(600):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json").read())
                if any(t["type"] == "page" for t in tabs):
                    break
            except Exception:
                pass
            time.sleep(0.2)
        url = [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"]
        self.ws = await websockets.connect(url, max_size=80_000_000)
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            await self.call(d)
        await self.call("Emulation.setDeviceMetricsOverride", {"width": self.w, "height": self.h, "deviceScaleFactor": 1, "mobile": False})
        return self

    async def __aexit__(self, *a):
        try:
            await self.ws.close()
        finally:
            self.proc.terminate()

    async def call(self, method, params=None):
        self.mid += 1
        my = self.mid
        await self.ws.send(json.dumps({"id": my, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await self.ws.recv())
            m = msg.get("method")
            if m == "Runtime.exceptionThrown":
                d = msg["params"]["exceptionDetails"]
                self.errors.append(("exception", d.get("text"), (d.get("exception") or {}).get("description", "")[:400]))
            elif m == "Runtime.consoleAPICalled" and msg["params"]["type"] == "error":
                self.errors.append(("console.error", " ".join(str(a.get("value", a.get("description", ""))) for a in msg["params"]["args"])[:400], ""))
            elif m == "Log.entryAdded" and msg["params"]["entry"]["level"] == "error":
                self.errors.append(("log", msg["params"]["entry"]["text"][:300], msg["params"]["entry"].get("url", "")))
            if msg.get("id") == my:
                return msg.get("result", {})

    async def ev(self, expr):
        res = await self.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in res:
            return {"__error__": res["exceptionDetails"].get("exception", {}).get("description", res["exceptionDetails"].get("text"))}
        return res.get("result", {}).get("value")

    async def go(self, path, wait=4):
        await self.call("Page.navigate", {"url": self.base + path})
        await asyncio.sleep(wait)

    async def wait_for(self, expr, timeout=60):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if await self.ev(expr):
                return True
            await asyncio.sleep(0.5)
        return False

    async def login(self, user, pw):
        await self.go("/login", 3)
        r = await self.ev(f"""fetch('/api/method/login', {{method:'POST', headers:{{'Content-Type':'application/json','Accept':'application/json'}}, body: JSON.stringify({{usr:{json.dumps(user)}, pwd:{json.dumps(pw)}}})}}).then(r => r.status)""")
        return r

    async def shot(self, name, full=False, selector=None):
        params = {"format": "png"}
        if full:
            dims = await self.ev("({w: document.documentElement.scrollWidth, h: Math.min(document.documentElement.scrollHeight, 6000)})")
            params["clip"] = {"x": 0, "y": 0, "width": dims["w"], "height": dims["h"], "scale": 1}
            params["captureBeyondViewport"] = True
        if selector:
            box = await self.ev(f"(() => {{ const r = document.querySelector({json.dumps(selector)}).getBoundingClientRect(); return {{x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: Math.min(r.height, 6000)}}; }})()")
            params["clip"] = {"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"], "scale": 1}
            params["captureBeyondViewport"] = True
        res = await self.call("Page.captureScreenshot", params)
        path = os.path.join(self.shots, name + ".png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        return path

    async def tall_shot(self, name, selector=None, max_h=9000):
        """Grow the viewport to the full content height (the desk scrolls inside a container),
        capture the page or one element, then restore the viewport."""
        h = await self.ev("""(() => { let m = document.documentElement.scrollHeight;
            document.querySelectorAll('*').forEach(el => { if (el.scrollHeight > el.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(el).overflowY)) m = Math.max(m, el.scrollHeight + el.getBoundingClientRect().top); });
            return Math.ceil(m); })()""")
        h = min(int(h or self.h), max_h)
        await self.call("Emulation.setDeviceMetricsOverride", {"width": self.w, "height": h, "deviceScaleFactor": 1, "mobile": False})
        await asyncio.sleep(1.5)
        params = {"format": "png"}
        if selector:
            box = await self.ev(f"(() => {{ const e = document.querySelector({json.dumps(selector)}); if (!e) return null; const r = e.getBoundingClientRect(); return {{x: r.x, y: r.y, w: r.width, h: r.height}}; }})()")
            if box:
                params["clip"] = {"x": box["x"], "y": box["y"], "width": box["w"], "height": min(box["h"], h - box["y"]), "scale": 1}
        res = await self.call("Page.captureScreenshot", params)
        path = os.path.join(self.shots, name + ".png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        await self.call("Emulation.setDeviceMetricsOverride", {"width": self.w, "height": self.h, "deviceScaleFactor": 1, "mobile": False})
        await asyncio.sleep(0.5)
        return path

    async def overflow(self):
        return await self.ev("""(() => { const W = document.documentElement.clientWidth; return {docW: document.documentElement.scrollWidth, W}; })()""")
