"""Fill and submit the public Arabic form in headless Chrome for one demo applicant (with an optional CV)."""
import asyncio, base64, json, os, sys
from datetime import date, timedelta

sys.path.insert(0, sys.path[0])
from frappe_ui import Browser

BASE, SHOTS, OPENING, KEY = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
CV_DIR = sys.argv[5] if len(sys.argv) > 5 else None
DATA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ido_talent_ai", "ido_talent_ai", "scripts", "demo_data.json")))
A = next(a for a in DATA["applicants"] if a["key"].endswith(KEY))


def dob(age):
    t = date.today()
    return (t.replace(year=t.year - age) - timedelta(days=120)).isoformat()


async def main():
    async with Browser(BASE, SHOTS, port=18092, height=2400) as b:
        await b.go(f"/jobs/security/security-supervisor-riyadh", 5)
        await b.shot(f"form_{KEY}_0_jobpage", full=True)
        await b.ev("document.querySelector('a[href*=\"/ai-apply/new\"]').click()")
        await asyncio.sleep(5)
        print("url:", await b.ev("location.pathname + location.search"))
        await b.shot(f"form_{KEY}_1_empty", full=True)
        vals = {"applicant_name": A["applicant_name"], "email_id": A["email_id"], "phone_number": A["phone_number"], "nationality": A["nationality"],
                "id_type": A["id_type"], "national_id": A["national_id"], "date_of_birth": dob(A["age"]),
                "height_cm": A.get("height_cm") or "", "weight_kg": A.get("weight_kg") or ""}
        js = f"""(() => {{ const v = {json.dumps(vals, ensure_ascii=False)}; const ans = {json.dumps(A['answers'], ensure_ascii=False)};
          const f = document.getElementById('tai-form');
          for (const [k, x] of Object.entries(v)) {{ const el = f.querySelector('[name="' + k + '"]'); if (el) {{ el.value = x; el.dispatchEvent(new Event('change', {{bubbles: true}})); }} }}
          for (const [k, x] of Object.entries(ans)) {{
            if (Array.isArray(x)) {{ f.querySelectorAll('[data-qm="' + k + '"]').forEach(c => c.checked = x.includes(c.value)); continue; }}
            const el = f.querySelector('[data-q="' + k + '"]'); if (el) el.value = x === null ? '' : String(x);
          }}
          document.getElementById('f-consent').checked = true; return 'filled'; }})()"""
        print(await b.ev(js))
        if A.get("cv") and CV_DIR:
            content = open(f"{CV_DIR}/{A['cv']}", "rb").read()
            b64 = base64.b64encode(content).decode()
            mime = {"pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}[A["cv"].rsplit(".", 1)[1]]
            print(await b.ev(f"""(() => {{ const bin = atob('{b64}'); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
               const file = new File([u], {json.dumps(A['cv'])}, {{type: '{mime}'}}); const dt = new DataTransfer(); dt.items.add(file);
               document.getElementById('f-cv').files = dt.files; return 'cv ' + file.size; }})()"""))
        await b.shot(f"form_{KEY}_2_filled", full=True)
        await b.ev("document.querySelector('#tai-form button[type=submit]').click()")
        ok = await b.wait_for("!!document.querySelector('.success')", 120)
        print("submitted:", ok, await b.ev("document.querySelector('#tai-apply').innerText.slice(0, 200)"))
        await b.shot(f"form_{KEY}_3_thanks", full=True)
        print("errors:", b.errors)


asyncio.run(main())
