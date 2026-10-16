/* Talent Console — Arabic-first test UI for the Talent Engine. Everything comes from the real API
   through the console session cookie; no API key and no fixed data live in this file. */
'use strict';

const DISCLAIMER = {ar:'الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة.', en:'The score is a ranking against approved criteria, not a probability of success in the job.'};
const BAND = {high:{ar:'مرتفعة', en:'High', cls:'green'}, medium:{ar:'متوسطة', en:'Medium', cls:'amber'}, low:{ar:'منخفضة', en:'Low', cls:'red'}};
const ELIG = {eligible:{ar:'مستوفٍ', en:'Eligible', cls:'green'}, not_eligible:{ar:'غير مستوفٍ بحسب ما كتبه', en:'Not eligible (as declared)', cls:'red'}, needs_review:{ar:'يحتاج مراجعة', en:'Needs review', cls:'amber'}};
const AIST = {Processing:{ar:'جاري المعالجة', en:'Processing', cls:'blue'}, Completed:{ar:'مكتمل', en:'Completed', cls:'green'}, 'Needs Review':{ar:'يحتاج مراجعة', en:'Needs Review', cls:'amber'}, Failed:{ar:'فشل', en:'Failed', cls:'red'}};
const STATUS_AI = {queued:'Processing', processing:'Processing', completed:'Completed', needs_review:'Needs Review', failed:'Failed'};
const FLAGS = {missing_evidence:{ar:'دليل ناقص', en:'Missing evidence'}, mandatory_missing:{ar:'معيار إلزامي بلا دليل', en:'Mandatory without evidence'}, mandatory_zero:{ar:'معيار إلزامي عند 0', en:'Mandatory at level 0'}, low_coverage:{ar:'تغطية منخفضة', en:'Low coverage'}, contradiction:{ar:'تعارض بين الإجابة والسيرة', en:'Answer vs CV contradiction'}, evidence_mismatch:{ar:'دليل لا يطابق الإجابة', en:'Evidence mismatch'}, quote_not_found:{ar:'اقتباس غير موجود (أُسقط)', en:'Quote not found (dropped)'}, cv_unreadable:{ar:'ملف السيرة غير مقروء', en:'CV unreadable'}, low_ocr_confidence:{ar:'ثقة OCR منخفضة', en:'Low OCR confidence'}, duplicate:{ar:'طلب مكرر', en:'Duplicate'}, stale:{ar:'قديم — نسخة معايير سابقة', en:'Stale — previous version'}, data_changed:{ar:'النتيجة لا تعكس آخر تعديل', en:'Result does not reflect the latest edit'}, hr_override:{ar:'تعديل HR', en:'HR override'}};
const GROUPS = {not_eligible:{ar:'غير مستوفين', en:'Not eligible', why:{ar:'لا يُرتَّبون، يبقون في بنك المتقدمين', en:'not ranked, kept in the talent pool'}}, needs_review:{ar:'يحتاج مراجعة', en:'Needs review', why:{ar:'قيمة مفقودة أو تغطية منخفضة أو تعارض', en:'missing value, low coverage or contradiction'}}, processing:{ar:'جاري المعالجة', en:'Processing', why:{ar:'لم تكتمل بعد', en:'not finished yet'}}, failed:{ar:'فشل', en:'Failed', why:{ar:'خطأ في المحرك بعد المحاولات', en:'engine error after retries'}}, stale:{ar:'قديم', en:'Stale', why:{ar:'نسخة معايير سابقة أو بيانات معدّلة', en:'previous criteria version or edited data'}}, duplicate:{ar:'مكرر', en:'Duplicate', why:{ar:'يُرتَّب الطلب الأصلي فقط', en:'only the original application is ranked'}}};
const FACTS = {nationality:{ar:'الجنسية', en:'Nationality'}, height_cm:{ar:'الطول (سم)', en:'Height (cm)'}, weight_kg:{ar:'الوزن (كجم)', en:'Weight (kg)'}, age:{ar:'العمر', en:'Age'}, gender:{ar:'الجنس', en:'Gender'}};
const OPS = {in:{ar:'ضمن', en:'one of'}, not_in:{ar:'ليس ضمن', en:'not one of'}, '>=':{ar:'أو أكثر', en:'or more'}, '<=':{ar:'أو أقل', en:'or less'}, '>':{ar:'أكثر من', en:'more than'}, '<':{ar:'أقل من', en:'less than'}, '==':{ar:'يساوي', en:'equals'}, '!=':{ar:'لا يساوي', en:'not'}, between:{ar:'بين', en:'between'}};
const QTYPES = {number:{ar:'رقم', en:'number'}, select:{ar:'اختيار', en:'select'}, multiselect:{ar:'اختيار متعدد', en:'multi-select'}, boolean:{ar:'نعم/لا', en:'yes/no'}, text:{ar:'نص', en:'text'}, date:{ar:'تاريخ', en:'date'}};
const LEVELS = [0, 25, 50, 75, 100];

const S = {
  lang: localStorage.getItem('tc_lang') || 'ar', dev: localStorage.getItem('tc_dev') === '1', screen: 'home', user: '', tenant: '',
  jobs: [], job: localStorage.getItem('tc_job') || null, sel: null, scr: null, log: [], hiliteKey: null,
  names: JSON.parse(localStorage.getItem('tc_names') || '{}'),  // host-side data (names) stays in this browser only
  edit: null, draft: null, form: null, proc: null, procTimer: null, listFilters: {ai:'', band:'', elig:'', q:''}, listSort: 'score',
  settings: null, cache: {},
};
const t = (ar, en) => S.lang === 'ar' ? ar : en;
const L = o => o ? (S.lang === 'ar' ? o.ar : o.en) : '';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const N = n => `<bdi class="num">${esc(n)}</bdi>`;
const fmt1 = n => n == null ? '—' : (Math.round(n * 10) / 10).toString();
const pct = n => n == null ? '—' : Math.round(n * 100) + '%';
const fd = s => { if (!s) return '—'; const d = new Date(s); if (isNaN(d)) return esc(s); return `<bdi>${esc(d.toLocaleString(S.lang === 'ar' ? 'ar-EG-u-nu-latn' : 'en-GB', {day:'numeric', month:'long', year:'numeric', hour:'numeric', minute:'2-digit'}))}</bdi>`; };
// Latin words and numbers inside Arabic sentences keep their own order (no jumbled «dob 1، name 3»)
const mix = s => esc(s).replace(/(?<![&#\w])[A-Za-z0-9](?:[A-Za-z0-9_.:/@%+\-]*[A-Za-z0-9%])?(?:\s+[A-Za-z](?:[A-Za-z0-9_.:/@%+\-]*[A-Za-z0-9%])?)*/g, m => `<bdi dir="ltr">${m}</bdi>`);
const qt = s => `«<bdi>${esc(s)}</bdi>»`;
// Same labels as the engine (app/domain/arabic_text.py)
const REDACT = {name:['الاسم', 'name'], phone:['الهاتف', 'phone'], email:['البريد', 'e-mail'], national_id:['رقم الهوية', 'ID number'], dob:['تاريخ الميلاد', 'date of birth'], age:['العمر', 'age'], nationality:['الجنسية', 'nationality'], gender:['الجنس', 'gender'], address:['العنوان', 'address'], url:['رابط', 'link']};
const redactLabel = k => REDACT[k] ? t(REDACT[k][0], REDACT[k][1]) : k;
const method = m => { m = m || ''; const base = m.split('+').pop(); if (m.startsWith('libreoffice+')) return t('ملف DOC/RTF محوَّل إلى PDF', 'DOC/RTF converted to PDF'); if (base.startsWith('ocr:')) return t('قراءة ضوئية (OCR)', 'OCR (scanned image)'); if (base === 'pdf_text') return t('نص PDF مباشر', 'PDF text layer'); if (base === 'docx') return t('ملف Word', 'Word file'); return esc(base || '—'); };
const chipMand = m => m ? `<span class="chip mand">${t('إلزامي', 'mandatory')}</span>` : `<span class="chip">${t('اختياري', 'optional')}</span>`;
const FLAG_CLS = {hr_override:'purple', duplicate:'grey', stale:'grey', data_changed:'grey'};
const chip = (o, extra) => `<span class="chip ${o.cls || ''}"><span class="dot"></span>${L(o)}${extra || ''}</span>`;
const chipBand = (b, elig) => elig === 'not_eligible' ? `<span class="chip">${t('خارج الترتيب', 'Not ranked')}</span>` : (BAND[b] ? chip(BAND[b]) : '');
const chipElig = s => ELIG[s] ? chip(ELIG[s]) : '';
const chipAi = st => chip(AIST[STATUS_AI[st] || st] || AIST.Processing);
const chipLvl = l => `<span class="chip ${l >= 75 ? 'green' : l >= 50 ? 'amber' : l > 0 ? 'red' : ''}">${l}</span>`;
const disclaimer = () => `<div class="disclaimer">ⓘ ${L(DISCLAIMER)}</div>`;
const nameOf = ref => (S.names[ref] && S.names[ref].name) || ref;
const saveNames = () => localStorage.setItem('tc_names', JSON.stringify(S.names));
const who = ref => nameOf(ref) === ref ? N(ref) : `${esc(nameOf(ref))} · ${N(ref)}`;
const flagChips = flags => (flags || []).filter(f => FLAGS[f]).map(f => `<span class="chip ${FLAG_CLS[f] || 'amber'}">${L(FLAGS[f])}</span>`).join(' ');

/* ---------- API (session cookie; every call logged for the developer view) ---------- */
async function api(method, url, body, isForm){
  const t0 = performance.now();
  const opts = {method, credentials:'same-origin', headers:{}};
  if (body !== undefined) { if (isForm) opts.body = body; else { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); } }
  const r = await fetch(url, opts);
  let data = null; try { data = await r.json(); } catch (e) { data = null; }
  S.log.unshift({method, url, status:r.status, ms:Math.round(performance.now() - t0), req: isForm ? '[multipart]' : body, res:data}); S.log = S.log.slice(0, 12);
  if (r.status === 401) { location.href = '/console/login'; throw new Error('session expired'); }
  if (!r.ok) { const msg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : r.status; throw new Error(msg); }
  if (S.dev) renderDev();
  return data;
}
const get = url => api('GET', url);

async function loadJobs(){ S.jobs = (await get('/v1/jobs')).jobs; if (!S.job || !S.jobs.some(j => j.ref === S.job)) S.job = S.jobs.length ? S.jobs[0].ref : null; }
const jobTitle = ref => { const j = S.jobs.find(x => x.ref === ref); return j ? j.title : ref; };
function jobSelect(action){ return `<select data-action="${action}">${S.jobs.map(j => `<option value="${esc(j.ref)}" ${j.ref === S.job ? 'selected' : ''}>${esc(j.title)} — ${esc(j.ref)}</option>`).join('')}</select>`; }
function reqText(r){ const v = Array.isArray(r.value) ? r.value.join('، ') : r.value; const u = {height_cm:'سم', weight_kg:'كجم', age:t('سنة', 'years')}[r.fact] || ''; if (r.operator === 'in' || r.operator === 'not_in') return `${L(OPS[r.operator])}: ${esc(v)}`; if (r.operator === '>=' || r.operator === '<=') return `${esc(v)} ${u} ${L(OPS[r.operator])}`; if (r.operator === 'between') return `${L(OPS.between)} ${esc(r.value[0])} ${t('و', 'and')} ${esc(r.value[1])} ${u}`; return `${L(OPS[r.operator] || {ar:r.operator, en:r.operator})} ${esc(v)} ${u}`; }

/* ---------- shell ---------- */
const NAV = [
  {sec:{ar:'التوظيف', en:'Recruitment'}}, {k:'home', ar:'الرئيسية', en:'Home'}, {k:'apply', ar:'نموذج التقديم', en:'Application form'}, {k:'list', ar:'المتقدمون', en:'Applicants'}, {k:'ranking', ar:'الترتيب', en:'Ranking'},
  {sec:{ar:'Talent AI', en:'Talent AI'}}, {k:'profile', ar:'ملف المعايير', en:'AI Job Profile'}, {k:'processing', ar:'المعالجة', en:'Processing'}, {k:'cv', ar:'تحليل السيرة', en:'CV analysis'}, {k:'tryfile', ar:'جرّب ملف', en:'Try a file'}, {k:'jobs', ar:'مهام الذكاء', en:'AI Jobs'}, {k:'audit', ar:'سجل التدقيق', en:'Audit log'}, {k:'settings', ar:'الإعدادات', en:'Settings'},
];
const SCREENS = {cv:rCvAnalysis, tryfile:rTryFile, home:rHome, profile:rProfile, apply:rApply, processing:rProcessing, list:rList, applicant:rApplicant, ranking:rRanking, jobs:rJobs, settings:rSettings, audit:rAudit};
let renderSeq = 0;
async function render(){
  const seq = ++renderSeq;
  document.documentElement.lang = S.lang; document.documentElement.dir = S.lang === 'ar' ? 'rtl' : 'ltr';
  const nav = NAV.map(n => n.sec ? `<div class="sec">${L(n.sec)}</div>` : `<a class="${S.screen === n.k || (S.screen === 'applicant' && n.k === 'list') ? 'active' : ''}" data-action="go" data-screen="${n.k}">${L(n)}</a>`).join('');
  const title = NAV.find(n => n.k === S.screen) || {ar:'المتقدم', en:'Applicant'};
  const shell = `
    <nav class="rail"><div class="mark">T</div><button class="active" title="desk">▦</button><button title="settings" data-action="go" data-screen="settings">⚙</button><div class="spacer"></div><form method="post" action="/console/logout"><button title="logout" type="submit">⎋</button></form></nav>
    <aside class="sidebar"><div class="brand"><bdi dir="ltr">✦ Talent Console</bdi><small>${esc(S.tenant)} · ${t('بيانات صناعية فقط', 'synthetic data only')}</small></div>
      <div class="ws"><div class="ico">T</div><div><b>${t('الشاغر الحالي', 'Current opening')}</b><small>${esc(jobTitle(S.job) || t('لا شواغر', 'no openings'))}</small></div></div>
      <div class="nav">${nav}</div><div class="me"><div class="av">${esc((S.user || '?')[0].toUpperCase())}</div><div><b>${esc(S.user)}</b><br><span class="hint">${t('مستخدم الكونسول', 'console user')}</span></div></div></aside>
    <div class="main">
      <div class="topbar"><div class="crumbs"><span>🏠</span> / <span>${t('التوظيف', 'Recruitment')}</span> / <b>${L(title)}</b></div><span class="badge-demo">${t('بيانات تجريبية', 'Test data')}</span>
        <label class="tgl" data-action="toggleDev"><span class="sw ${S.dev ? 'on' : ''}"></span>${t('عرض المطوّر', 'Developer view')}</label>
        <div class="seg"><button class="${S.lang === 'ar' ? 'on' : ''}" data-action="setLang" data-lang="ar">عربي</button><button class="${S.lang === 'en' ? 'on' : ''}" data-action="setLang" data-lang="en">English</button></div></div>
      <div class="content"><div class="screen" id="screen"><div class="hint"><span class="spin"></span> ${t('جارٍ التحميل…', 'Loading…')}</div></div>${S.dev ? '<aside class="dev" id="dev"></aside>' : ''}</div>
    </div>`;
  document.getElementById('app').innerHTML = shell;
  try { const html = await SCREENS[S.screen](); if (seq !== renderSeq) return; document.getElementById('screen').innerHTML = html; }
  catch (e) { if (seq !== renderSeq) return; document.getElementById('screen').innerHTML = `<div class="card"><div class="note danger">✗ ${esc(e.message)}</div></div>`; }
  if (S.dev) renderDev();
  if (S.hiliteKey) { const m = document.getElementById('q-' + S.hiliteKey); if (m) m.scrollIntoView({block:'center', behavior:'smooth'}); }
}
function renderDev(){
  const el = document.getElementById('dev'); if (!el) return;
  const items = S.log.map(x => `<h4><span class="ep">${esc(x.method)} ${esc(x.url)}</span> → ${x.status} · ${x.ms}ms</h4>${x.req ? `<pre>${esc(typeof x.req === 'string' ? x.req : JSON.stringify(x.req, null, 1)).slice(0, 1500)}</pre>` : ''}<pre>${esc(JSON.stringify(x.res, null, 1) || '').slice(0, 2500)}</pre>`).join('');
  el.innerHTML = `<h3>Developer view</h3><p>${t('آخر نداءات الـ API من هذه الشاشة (الطلب والرد كما هما). المفتاح لا يظهر: الجلسة كوكي.', 'The latest API calls of this screen (request and response as sent). No key is visible: the session is a cookie.')}</p>${items || '<p>—</p>'}`;
}
function go(screen, opts){ S.log = []; if (screen === 'cv' || screen === 'tryfile') { S.cvPage = 0; S.cvSel = null; S.cvLine = null; } S.screen = screen; S.hiliteKey = null; if (opts && opts.sel) S.sel = opts.sel; if (opts && opts.scr) S.scr = opts.scr; if (screen !== 'processing' && S.procTimer) { clearInterval(S.procTimer); S.procTimer = null; } render(); }
function pageTitle(title, sub, actions){ return `<div class="page-title"><div><h1>${title}</h1>${sub ? `<div class="sub">${sub}</div>` : ''}</div>${actions ? `<div class="actions">${actions}</div>` : ''}</div>`; }
function modal(html){ document.getElementById('modal').innerHTML = html; document.getElementById('overlay').classList.add('on'); }
function closeModal(){ document.getElementById('overlay').classList.remove('on'); }
let toastTimer = null;
function toast(msg){ const el = document.getElementById('toast'); el.textContent = msg; el.classList.add('on'); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('on'), 3200); }
function reasonDialog(title, onOk, extra){
  modal(`<h3>${title}</h3>${extra || ''}<div class="field"><label>${t('السبب', 'Reason')} <span class="req">*</span></label><textarea id="m-reason" placeholder="${t('مطلوب — يُسجَّل في سجل التدقيق', 'Required — recorded in the audit log')}"></textarea></div><div class="acts"><button class="btn" data-action="closeModal">${t('إلغاء', 'Cancel')}</button><button class="btn primary" id="m-ok">${t('تأكيد', 'Confirm')}</button></div>`);
  document.getElementById('m-ok').onclick = () => { const r = document.getElementById('m-reason').value.trim(); if (!r) { toast(t('السبب مطلوب', 'A reason is required')); return; } closeModal(); onOk(r); };
}

/* ---------- home ---------- */
async function rHome(){
  await loadJobs();
  const cards = await Promise.all(S.jobs.map(async j => { const rk = await get(`/v1/jobs/${encodeURIComponent(j.ref)}/ranking`); const g = rk.groups; return `<div class="card"><h2>${esc(j.title)} <small>${esc(j.ref)} · v${j.active_version}</small></h2>
      <div class="aihead" style="grid-template-columns:repeat(4,1fr)"><div class="kpi"><small>${t('المتقدمون', 'Applicants')}</small><b>${rk.total}</b></div><div class="kpi"><small>${t('مرتَّبون', 'Ranked')}</small><b>${rk.ranked_total}</b></div><div class="kpi"><small>${t('يحتاج مراجعة', 'Needs review')}</small><b>${g.needs_review.length}</b></div><div class="kpi"><small>${t('غير مستوفين / فشل', 'Not eligible / failed')}</small><b>${g.not_eligible.length} / ${g.failed.length}</b></div></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" data-action="pickJob" data-ref="${esc(j.ref)}" data-screen="profile">${t('ملف المعايير', 'AI Job Profile')}</button><button class="btn" data-action="pickJob" data-ref="${esc(j.ref)}" data-screen="apply">${t('تقديم طلب', 'Apply')}</button><button class="btn" data-action="pickJob" data-ref="${esc(j.ref)}" data-screen="list">${t('المتقدمون', 'Applicants')}</button><button class="btn primary" data-action="pickJob" data-ref="${esc(j.ref)}" data-screen="ranking">${t('الترتيب', 'Ranking')}</button></div>${disclaimer()}</div>`; }));
  return pageTitle(t('الشواغر', 'Job openings'), `${N(S.jobs.length)} ${t('شاغر بملف معايير معتمد', 'openings with an approved profile')}`, `<button class="btn primary" data-action="newJob">＋ ${t('شاغر جديد', 'New opening')}</button>`) +
    `<div class="note">${t('الدورة: ملف المعايير (أوزان 100%) ← نموذج التقديم ← المعالجة خطوة بخطوة ← شاشة المتقدم بالأدلة ← الترتيب بالمجموعات. HR وحده يقرر؛ الذكاء يرتّب ويشرح.', 'The cycle: AI Job Profile (weights 100%) → application form → step-by-step processing → applicant screen with evidence → grouped ranking. HR alone decides; the AI ranks and explains.')}</div>` + (cards.join('') || `<div class="card"><p class="hint">${t('لا شواغر بعد. أنشئ شاغرًا جديدًا.', 'No openings yet. Create one.')}</p></div>`);
}

/* ---------- AI Job Profile (editor) ---------- */
function newEdit(ref){ return {ref:ref || '', title:'', description:'', criteria:[], rules:[], questions:[], version:null, approved_by:null, approved_at:null, dirty:true, isNew:true}; }
function fromJob(j){ const v = j.version || {criteria:[], rules:[], questions:[]}; return {ref:j.ref, title:j.title, description:j.description, criteria:JSON.parse(JSON.stringify(v.criteria)), rules:JSON.parse(JSON.stringify(v.rules)), questions:JSON.parse(JSON.stringify(v.questions)), version:v.version, approved_by:v.approved_by, approved_at:v.approved_at, dirty:false, isNew:false}; }
const weightSum = e => Math.round(e.criteria.reduce((a, c) => a + (Number(c.weight) || 0), 0) * 10) / 10;
function hintsOf(r){ if (r.gte != null) return `>= ${r.gte}`; if (r.gt != null) return `> ${r.gt}`; if (r.answers && r.answers.length) return r.answers.join(' | '); return ''; }
function parseHints(s, qtype){ s = (s || '').trim(); const out = {gte:null, gt:null, answers:null}; if (!s) return out; if (qtype === 'number') { const m = /^(>=|>)\s*(-?\d+(\.\d+)?)$/.exec(s); if (m) { out[m[1] === '>=' ? 'gte' : 'gt'] = Number(m[2]); } return out; } out.answers = s.split('|').map(x => x.trim()).filter(Boolean); return out; }
async function rProfile(){
  await loadJobs();
  if (!S.edit || (S.edit.ref !== S.job && !S.edit.isNew)) { if (!S.job) S.edit = newEdit(''); else S.edit = fromJob(await get(`/v1/jobs/${encodeURIComponent(S.job)}`)); }
  const e = S.edit; const sum = weightSum(e); const ok = Math.abs(sum - 100) < 0.001 && e.criteria.length > 0;
  const qopts = (sel) => `<option value="">${t('— بدون —', '— none —')}</option>` + e.questions.map(q => `<option value="${esc(q.key)}" ${q.key === sel ? 'selected' : ''}>${esc(q.label)}</option>`).join('');
  const crit = e.criteria.map((c, i) => { const q = e.questions.find(x => x.key === c.question); const qtype = q ? q.type : 'text'; return `<tr><td><input value="${esc(c.key)}" data-crit="${i}" data-f="key" class="num" style="width:100%" placeholder="key"><br><input value="${esc(c.text)}" data-crit="${i}" data-f="text" style="width:100%;margin-top:4px" placeholder="${t('نص المعيار', 'criterion text')}"></td>
    <td><label class="chk"><input type="checkbox" ${c.mandatory ? 'checked' : ''} data-crit="${i}" data-f="mandatory"> ${t('إلزامي', 'mandatory')}</label></td>
    <td><input class="w-in num" type="number" min="0" max="100" step="0.5" value="${c.weight}" data-crit="${i}" data-f="weight"> <span class="hint">%</span></td>
    <td><select data-crit="${i}" data-f="question">${qopts(c.question)}</select></td>
    <td class="rub">${c.rubric.map((r, j) => `<div style="display:flex;gap:4px;align-items:center;margin:2px 0"><b class="num" style="width:28px">${r.level}</b><input value="${esc(r.text)}" data-crit="${i}" data-rub="${j}" data-f="text" style="flex:1" placeholder="${t('وصف المستوى', 'level description')}"><input value="${esc(hintsOf(r))}" data-crit="${i}" data-rub="${j}" data-f="hints" style="width:96px" ${qtype === 'number' ? 'class="num"' : 'dir="auto"'} placeholder="${qtype === 'number' ? '>= 3' : t('إجابة | إجابة', 'answer | answer')}" title="${t('تلميح للحساب بالكود: للأرقام >= أو > ، وللاختيارات الإجابات مفصولة بـ |', 'Code hint: >= or > for numbers; answers separated by | for selects')}"></div>`).join('')}</td>
    <td><button class="btn sm danger" data-action="delCrit" data-i="${i}">✕</button></td></tr>`; }).join('');
  const rules = e.rules.map((r, i) => `<tr><td><select data-rule="${i}" data-f="fact">${Object.keys(FACTS).map(f => `<option value="${f}" ${r.fact === f ? 'selected' : ''}>${L(FACTS[f])}</option>`).join('')}</select></td><td><select data-rule="${i}" data-f="operator">${Object.keys(OPS).map(o => `<option value="${o}" ${r.operator === o ? 'selected' : ''}>${o} — ${L(OPS[o])}</option>`).join('')}</select></td><td><input value="${esc(Array.isArray(r.value) ? r.value.join(', ') : r.value)}" data-rule="${i}" data-f="value" placeholder="${t('قيمة أو قيم مفصولة بفاصلة', 'value or comma-separated values')}"></td><td>${chip(ELIG.needs_review)}</td><td><button class="btn sm danger" data-action="delRule" data-i="${i}">✕</button></td></tr>`).join('');
  const qs = e.questions.map((q, i) => `<tr><td><input value="${esc(q.key)}" data-q="${i}" data-f="key" class="num" style="width:110px"></td><td><input value="${esc(q.label)}" data-q="${i}" data-f="label" style="width:240px"></td><td><select data-q="${i}" data-f="type">${Object.keys(QTYPES).map(k => `<option value="${k}" ${q.type === k ? 'selected' : ''}>${L(QTYPES[k])}</option>`).join('')}</select></td><td><input value="${esc((q.options || []).join(' | '))}" data-q="${i}" data-f="options" placeholder="${t('خيارات مفصولة بـ |', 'options separated by |')}" style="width:200px" dir="auto"></td><td><label class="chk"><input type="checkbox" ${q.required !== false ? 'checked' : ''} data-q="${i}" data-f="required"> ${t('مطلوب', 'required')}</label></td><td><button class="btn sm danger" data-action="delQ" data-i="${i}">✕</button></td></tr>`).join('');
  const totalChip = ok ? `<span class="chip green">${t('المجموع', 'Total')}: ${N('100%')}</span>` : `<span class="chip red">${t('المجموع', 'Total')}: ${N(sum + '%')} — ${t('يجب أن يكون 100%', 'must be 100%')}</span>`;
  const statusChip = e.isNew ? `<span class="chip amber">${t('شاغر جديد — لم يُعتمد بعد', 'New opening — not approved yet')}</span>` : e.dirty ? `<span class="chip amber"><span class="dot"></span>${t('مسودة نسخة', 'Draft of version')} ${N('v' + (e.version + 1))}</span> <span class="hint">${t('النسخة المعتمدة الحالية', 'Current approved version')} ${N('v' + e.version)}</span>` : `<span class="chip green"><span class="dot"></span>${t('معتمد', 'Approved')} ${N('v' + e.version)}</span> <span class="hint">${t('اعتمدها:', 'Approved by:')} ${esc(e.approved_by || '—')} · ${fd(e.approved_at)}</span>`;
  const draftHtml = S.draft ? `<div class="card"><h2>${t('مسودة معايير مولّدة بالذكاء الاصطناعي', 'AI-generated criteria draft')} <span class="chip amber">${t('مسودة — تحتاج اعتماد', 'Draft — needs approval')}</span></h2><div class="draft">${esc(S.draft.description)}\n\n${S.draft.criteria.map(c => `• ${c.text} — ${c.mandatory ? t('إلزامي', 'mandatory') : t('اختياري', 'optional')} — ${c.weight}%`).join('\n')}</div><div style="margin-top:10px;display:flex;gap:8px"><button class="btn primary" data-action="useDraft">${t('استخدام المسودة في المحرّر', 'Use the draft in the editor')}</button><button class="btn" data-action="discardDraft">${t('تجاهل المسودة', 'Discard draft')}</button></div><p class="hint">${t('المسودة لا تُستخدم في أي تقييم قبل الاعتماد.', 'The draft is not used for any assessment before approval.')}</p></div>` : '';
  return pageTitle(`${t('ملف المعايير', 'AI Job Profile')}: ${esc(e.title || t('(بدون عنوان)', '(untitled)'))}`, `AI Job Profile · ${N(e.ref || '—')} · ${statusChip}`,
    `${S.jobs.length ? jobSelect('pickJobProfile') : ''}<button class="btn" data-action="newJob">＋ ${t('شاغر جديد', 'New')}</button><button class="btn" data-action="aiDraft">✦ ${t('مسودة بالذكاء الاصطناعي', 'AI draft')}</button><button class="btn primary" data-action="approveProfile" ${ok && (e.dirty || e.isNew) ? '' : 'disabled'} title="${ok ? '' : t('المجموع يجب أن يكون 100%', 'Total must be 100%')}">✓ ${t('اعتماد نسخة جديدة', 'Approve new version')}</button>`) +
  draftHtml +
  `<div class="card"><h2>${t('الشاغر', 'Opening')}</h2><div class="grid2"><div class="field"><label>${t('مرجع الشاغر (Job Opening)', 'Opening reference')}</label><input value="${esc(e.ref)}" data-edit="ref" ${e.isNew ? '' : 'readonly class="num"'}></div><div class="field"><label>${t('المسمى', 'Title')}</label><input value="${esc(e.title)}" data-edit="title"></div></div><div class="field"><label>${t('الوصف الوظيفي', 'Job description')}</label><textarea data-edit="description">${esc(e.description)}</textarea></div></div>
  <div class="card"><h2>${t('معايير التقييم وسُلّم التقييم', 'Criteria and rubric')} <small>AI Job Criterion</small> ${totalChip} <button class="btn sm" data-action="addCrit" style="margin-inline-start:auto">＋ ${t('معيار', 'criterion')}</button></h2>
    <div class="tscroll"><table class="edit"><thead><tr><th>${t('المعيار', 'Criterion')}</th><th>${t('النوع', 'Type')}</th><th>${t('الوزن', 'Weight')}</th><th>${t('يغذّيه سؤال', 'Fed by question')}</th><th>${t('سُلّم التقييم 0 / 25 / 50 / 75 / 100 + تلميح الحساب', 'Rubric 0 / 25 / 50 / 75 / 100 + code hint')}</th><th></th></tr></thead><tbody>${crit || `<tr><td colspan="6" class="hint">${t('لا معايير بعد', 'No criteria yet')}</td></tr>`}</tbody></table></div>
    <div class="note">${t('الدرجة = Σ(الوزن٪ × المستوى) ÷ 100. المستويات ثابتة: 0 أو 25 أو 50 أو 75 أو 100. الإجابات الرقمية والاختيارية تُحسب بالكود من التلميحات؛ النموذج اللغوي يحكم على الإجابات النصية والسيرة فقط. دليل ناقص ← 0 مع وسم. إلزامي عند 0 ← فئة منخفضة. تغطية أقل من 60% ← يحتاج مراجعة.', 'Score = Σ(weight% × level) ÷ 100. Fixed levels 0/25/50/75/100. Numeric and select answers are computed in code from the hints; the language model judges free-text answers and the CV only. Missing evidence → 0 flagged. Mandatory at 0 → low band. Coverage below 60% → needs review.')}</div>
    <p class="hint">${t('أي تعديل يصبح مسودة نسخة جديدة؛ بعد اعتمادها تُعلَّم التقييمات السابقة «قديمة» حتى تُعاد.', 'Any edit becomes a draft of a new version; after approval earlier assessments are flagged stale until re-scored.')}</p></div>
  <div class="stack">
    <div class="card"><h2>${t('الشروط الإلزامية (الأهلية)', 'Hard rules (eligibility)')} <small>${t('تُقارن في الكود بالقيم المصرّح بها', 'Compared in code with the declared values')}</small> <button class="btn sm" data-action="addRule" style="margin-inline-start:auto">＋</button></h2>
      <div class="tscroll"><table class="edit"><thead><tr><th>${t('البيان', 'Fact')}</th><th>${t('العامل', 'Operator')}</th><th>${t('القيمة', 'Value')}</th><th>${t('إذا كان مفقودًا', 'If missing')}</th><th></th></tr></thead><tbody>${rules || `<tr><td colspan="5" class="hint">${t('لا شروط', 'No rules')}</td></tr>`}</tbody></table></div>
      <div class="note">${t('أي شرط يفشل على قيمة مصرّح بها ← «غير مستوفٍ بحسب ما كتبه». قيمة مفقودة ← «يحتاج مراجعة». النموذج اللغوي لا يرى الجنسية ولا العمر.', 'A rule failing on a declared value → "Not eligible (as declared)". A missing value → "Needs review". The language model never sees nationality or age.')}</div></div>
    <div class="card"><h2>${t('أسئلة الفرز في نموذج التقديم', 'Screening questions')} <button class="btn sm" data-action="addQ" style="margin-inline-start:auto">＋</button></h2>
      <div class="tscroll"><table class="edit"><thead><tr><th>key</th><th>${t('السؤال', 'Question')}</th><th>${t('النوع', 'Type')}</th><th>${t('الخيارات', 'Options')}</th><th></th><th></th></tr></thead><tbody>${qs || `<tr><td colspan="6" class="hint">${t('لا أسئلة', 'No questions')}</td></tr>`}</tbody></table></div>
      <div class="note">${t('إجابات المتقدم هي المصدر الأساسي. الفراغ يعني «لم يُجب» (دليل ناقص)، أما 0 فإجابة حقيقية.', 'The answers are the primary source. A blank means "not answered" (missing evidence); 0 is a real answer.')}</div></div>
  </div>`;
}
function editPayload(e){
  return {title:e.title, description:e.description, approved_by:S.user ? `console:${S.user}` : null,
    criteria:e.criteria.map(c => ({key:c.key, text:c.text, text_en:c.text_en || null, weight:Number(c.weight) || 0, mandatory:!!c.mandatory, question:c.question || null, rubric:c.rubric.map(r => ({level:r.level, text:r.text || '—', gte:r.gte == null ? null : r.gte, gt:r.gt == null ? null : r.gt, answers:r.answers && r.answers.length ? r.answers : null}))})),
    rules:e.rules.map(r => { let v = r.value; if (r.operator === 'in' || r.operator === 'not_in' || r.operator === 'between') v = String(v).split(',').map(x => x.trim()).filter(Boolean).map(x => isNaN(Number(x)) ? x : Number(x)); else if (!isNaN(Number(v)) && String(v).trim() !== '') v = Number(v); return {fact:r.fact, operator:r.operator, value:v, if_missing:'review'}; }),
    questions:e.questions.map(q => ({key:q.key, label:q.label, label_en:q.label_en || null, type:q.type, options:(q.options && q.options.length) ? q.options : null, required:q.required !== false, hint:q.hint || null}))};
}
async function approveProfile(){
  const e = S.edit; if (!e.ref) { toast(t('أدخل مرجع الشاغر', 'Enter the opening reference')); return; }
  try { const r = await api('PUT', `/v1/jobs/${encodeURIComponent(e.ref)}`, editPayload(e)); S.job = e.ref; localStorage.setItem('tc_job', S.job); S.edit = null; toast(r.new_version ? t(`اعتُمدت النسخة v${r.version.version}. التقييمات السابقة أصبحت قديمة حتى تُعاد.`, `Version v${r.version.version} approved. Earlier assessments are now stale until re-scored.`) : t('لا تغيير في المحتوى — النسخة الحالية باقية', 'No content change — the current version stays')); render(); }
  catch (err) { toast(t('رُفض الاعتماد: ', 'Approval refused: ') + err.message); }
}
async function aiDraft(){
  const e = S.edit; if (!e.title) { toast(t('أدخل المسمى أولًا', 'Enter the title first')); return; }
  toast(t('جارٍ توليد المسودة…', 'Generating the draft…'));
  try { S.draft = await api('POST', '/v1/jobs/draft-criteria', {title:e.title, description:e.description}); render(); } catch (err) { toast(err.message); }
}

/* ---------- application form ---------- */
async function rApply(){
  await loadJobs(); if (!S.job) return `<div class="card">${t('لا شواغر', 'No openings')}</div>`;
  const j = S.cache['job:' + S.job] || (S.cache['job:' + S.job] = await get(`/v1/jobs/${encodeURIComponent(S.job)}`));
  const v = j.version; if (!S.form || S.form.job !== S.job) S.form = {job:S.job, name:'', email:'', phone:'', nationality:'السعودية', idType:'هوية وطنية', idNo:'', dob:'', height:'', weight:'', answers:{}, consent:false, cv:null};
  const F = S.form; const facts = new Set(v.rules.map(r => r.fact));
  const field = (lbl, inner, req) => `<div class="field"><label>${lbl}${req ? ' <span class="req">*</span>' : ''}</label>${inner}</div>`;
  const q = v.questions.map(qq => { const val = F.answers[qq.key]; if (qq.type === 'select') return field(esc(qq.label), `<select data-ans="${qq.key}"><option value="">${t('— اختر —', '— choose —')}</option>${(qq.options || []).map(o => `<option ${val === o ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>`, qq.required); if (qq.type === 'multiselect') return field(esc(qq.label), `<div class="multi">${(qq.options || []).map(o => `<label class="chk"><input type="checkbox" value="${esc(o)}" data-ans-multi="${qq.key}" ${(val || []).includes(o) ? 'checked' : ''}> ${esc(o)}</label>`).join('')}</div>`, qq.required); if (qq.type === 'number') return field(esc(qq.label), `<input type="number" min="0" step="0.5" value="${val == null ? '' : esc(val)}" data-ans="${qq.key}"><div class="help hint">${esc(qq.hint || t('اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب', 'Write 0 if none. Blank means not answered'))}</div>`, qq.required); if (qq.type === 'boolean') return field(esc(qq.label), `<select data-ans="${qq.key}"><option value="">—</option><option value="نعم" ${val === 'نعم' ? 'selected' : ''}>${t('نعم', 'Yes')}</option><option value="لا" ${val === 'لا' ? 'selected' : ''}>${t('لا', 'No')}</option></select>`, qq.required); if (qq.type === 'date') return field(esc(qq.label), `<input type="date" value="${esc(val || '')}" data-ans="${qq.key}">`, qq.required); return field(esc(qq.label), `<textarea data-ans="${qq.key}">${esc(val || '')}</textarea>`, qq.required); }).join('');
  return pageTitle(t('نموذج التقديم', 'Application form'), `${esc(j.title)} · ${N(j.ref)} · ${t('نسخة المعايير', 'profile version')} ${N('v' + v.version)}`, jobSelect('pickJobApply')) +
  `<div class="note">${t('هذه الشاشة تقوم مقام نظام الموارد البشرية: الاسم والبريد والجوال ورقم الهوية تبقى هنا في متصفحك ولا تُرسل للمحرك. يُرسل فقط: الحقائق المسموحة (الجنسية والعمر المحسوب من تاريخ الميلاد والطول والوزن)، الإجابات، بصمة الهوية HMAC، والسيرة الذاتية.', 'This screen stands in for the HR system: name, e-mail, phone and national ID stay in your browser and are never sent to the engine. Only the allowed facts (nationality, age computed from the date of birth, height, weight), the answers, the HMAC id token and the CV are sent.')}</div>
  <div class="grid2"><div class="card"><h2>${t('بيانات المتقدم', 'Applicant')}</h2>
    ${field(t('الاسم الكامل', 'Full name'), `<input value="${esc(F.name)}" data-form="name">`, true)}
    <div class="grid2">${field(t('البريد', 'E-mail'), `<input value="${esc(F.email)}" data-form="email">`)}${field(t('الجوال', 'Mobile'), `<input value="${esc(F.phone)}" data-form="phone" class="num">`)}</div>
    <div class="grid2">${field(L(FACTS.nationality), `<select data-form="nationality">${['السعودية', 'مصر', 'اليمن', 'السودان', 'باكستان', 'الهند', 'الأردن', 'سوريا'].map(x => `<option ${F.nationality === x ? 'selected' : ''}>${x}</option>`).join('')}</select>`, facts.has('nationality'))}${field(t('رقم الهوية / الإقامة', 'National ID / Iqama'), `<input value="${esc(F.idNo)}" data-form="idNo" class="num" placeholder="${t('يُستخدم لكشف التكرار فقط (بصمة)', 'duplicate detection only (hashed)')}">`)}</div>
    <div class="grid3">${field(t('تاريخ الميلاد', 'Date of birth'), `<input type="date" value="${esc(F.dob)}" data-form="dob">`, facts.has('age'))}${facts.has('height_cm') ? field(L(FACTS.height_cm), `<input type="number" value="${esc(F.height)}" data-form="height" class="num">`) : ''}${facts.has('weight_kg') ? field(L(FACTS.weight_kg), `<input type="number" value="${esc(F.weight)}" data-form="weight" class="num">`) : ''}</div>
    ${field(t('السيرة الذاتية (اختياري)', 'CV (optional)'), `<input type="file" accept=".pdf,.docx,.doc,.rtf,.jpg,.jpeg,.png" data-form="cv"><div class="hint">PDF · DOCX · DOC · RTF · JPG · PNG — ${t('الصور والملفات الممسوحة تُقرأ بـ OCR', 'images and scans are read with OCR')}</div>`)}
    <label class="chk"><input type="checkbox" ${F.consent ? 'checked' : ''} data-form="consent"><span><b>${t('أوافق على معالجة بياناتي لغرض التوظيف', 'I consent to the processing of my data for recruitment')}</b><br><span class="hint">${t('مطلوبة. نسخة نص الموافقة تُحفظ مع الطلب.', 'Required. The consent text version is stored with the application.')}</span></span></label>
  </div>
  <div class="card"><h2>${t('أسئلة الفرز', 'Screening questions')} <small>${t('من ملف المعايير المعتمد', 'from the approved profile')}</small></h2>${q || `<p class="hint">${t('لا أسئلة في هذا الملف', 'No questions in this profile')}</p>`}
    <div style="margin-top:12px;display:flex;gap:8px"><button class="btn primary" data-action="submitForm">${t('إرسال الطلب', 'Submit application')}</button></div></div></div>`;
}
function ageFrom(dob){ if (!dob) return null; const d = new Date(dob); if (isNaN(d)) return null; return Math.floor((Date.now() - d.getTime()) / 31557600000); }
async function submitForm(){
  const F = S.form; const j = S.cache['job:' + S.job]; const v = j.version;
  if (!F.name) { toast(t('الاسم مطلوب', 'Name is required')); return; }
  if (!F.consent) { toast(t('الموافقة مطلوبة', 'Consent is required')); return; }
  const missing = v.questions.filter(q => q.required !== false && (F.answers[q.key] == null || F.answers[q.key] === '' || (Array.isArray(F.answers[q.key]) && !F.answers[q.key].length)));
  if (missing.length) { toast(t('أسئلة مطلوبة بلا إجابة: ', 'Required questions unanswered: ') + missing.map(q => q.label).join('، ')); return; }
  const factsNeeded = new Set(v.rules.map(r => r.fact)); const facts = {nationality:F.nationality};
  if (factsNeeded.has('age') || F.dob) facts.age = ageFrom(F.dob);
  if (factsNeeded.has('height_cm')) facts.height_cm = F.height === '' ? null : Number(F.height);
  if (factsNeeded.has('weight_kg')) facts.weight_kg = F.weight === '' ? null : Number(F.weight);
  const answers = {}; v.questions.forEach(q => { const val = F.answers[q.key]; answers[q.key] = (q.type === 'number' && val !== '' && val != null) ? Number(val) : (val == null ? '' : val); });
  const ref = 'CON-APP-' + Date.now().toString(36).toUpperCase();
  try {
    let id_token = null; if (F.idNo.trim()) id_token = (await api('POST', '/console/id-token', {national_id:F.idNo.trim()})).id_token;
    await api('PUT', `/v1/candidates/${ref}`, {id_token, facts, answers, consent:true});
    S.names[ref] = {name:F.name, applied:new Date().toISOString(), job:S.job}; saveNames();
    if (F.cv) { const fd = new FormData(); fd.append('file', F.cv, F.cv.name); fd.append('name_hint', F.name); toast(t('جارٍ قراءة السيرة الذاتية…', 'Reading the CV…')); await api('PUT', `/v1/candidates/${ref}/cv`, fd, true); }
    const s = await api('POST', '/v1/screenings', {job_ref:S.job, candidate_ref:ref});
    S.form = null; toast(t('تم حفظ الطلب فورًا. بدأت المعالجة.', 'Application saved. Processing started.'));
    go('processing', {scr:s.screening_id, sel:ref});
  } catch (err) { toast(t('خطأ: ', 'Error: ') + err.message); }
}

/* ---------- processing (live) ---------- */
async function rProcessing(){
  if (!S.scr) { const list = (await get('/v1/screenings?limit=30')).screenings; if (!list.length) return pageTitle(t('المعالجة', 'Processing')) + `<div class="card"><p class="hint">${t('لا توجد عمليات فرز بعد. قدّم طلبًا من نموذج التقديم.', 'No screenings yet. Submit an application first.')}</p></div>`; S.scr = list[0].screening_id; }
  const s = await get(`/v1/screenings/${S.scr}`); S.sel = s.candidate_ref;
  const running = s.status === 'queued' || s.status === 'processing';
  if (running && !S.procTimer) S.procTimer = setInterval(async () => { if (S.screen !== 'processing') { clearInterval(S.procTimer); S.procTimer = null; return; } const x = await get(`/v1/screenings/${S.scr}`); if (x.status !== 'queued' && x.status !== 'processing') { clearInterval(S.procTimer); S.procTimer = null; } document.getElementById('screen').innerHTML = procHtml(x); }, 1000);
  return procHtml(s);
}
function procHtml(s){
  const running = s.status === 'queued' || s.status === 'processing';
  const steps = s.stages.map((st, i) => `<div class="pstep ${st.status === 'done' ? 'done' : st.status === 'running' ? 'on' : st.status === 'skipped' ? 'skip' : st.status === 'failed' ? 'failed' : ''}"><div class="n">${st.status === 'done' ? '✓' : st.status === 'skipped' ? '–' : st.status === 'failed' ? '✗' : i + 1}</div><div class="t"><b>${esc(S.lang === 'ar' ? st.label_ar : st.label_en)}</b><small>${st.status === 'running' ? `<span class="spin"></span> ${t('جارٍ…', 'running…')}` : mix((S.lang === 'ar' ? st.note : st.note_en || st.note) || '')}${st.ms != null && st.ms > 50 ? ` <span class="num">(${(st.ms / 1000).toFixed(1)}s)</span>` : ''}</small></div></div>`).join('');
  const done = !running;
  const result = done ? (s.status === 'failed' ? `<div class="note danger">✗ ${t('فشلت المعالجة بعد', 'Processing failed after')} ${s.attempts} ${t('محاولات:', 'attempts:')} ${esc(s.error)}. ${t('الطلب محفوظ وظاهر بشكل طبيعي.', 'The application is saved and visible normally.')} <button class="btn sm primary" data-action="retry" data-id="${s.screening_id}">↻ ${t('إعادة المحاولة', 'Retry')}</button></div>` :
    `<div class="aihead"><div class="kpi"><small>${t('الأهلية', 'Eligibility')}</small>${chipElig(s.eligibility)}</div><div class="kpi"><small>${t('الدرجة', 'Score')}</small><b class="score ${s.eligibility === 'not_eligible' ? 'off' : s.band}">${N(fmt1(s.score))}</b> ${chipBand(s.band, s.eligibility)}</div><div class="kpi"><small>${t('التغطية', 'Coverage')}</small><b>${N(pct(s.coverage))}</b></div><div class="kpi"><small>ai_status</small>${chipAi(s.status)}</div></div><div class="note">${t('اكتملت المعالجة ولم تتغيّر حالة المتقدم؛ الذكاء يرتّب ويشرح فقط.', 'Processing complete; the applicant status did not change. The AI only ranks and explains.')} ${t('الوقت الكلي', 'Total time')}: <b class="num">${((s.versions.total_ms || 0) / 1000).toFixed(1)}s</b> · ${t('النموذج', 'model')}: <code>${esc(s.versions.model)}</code></div>${disclaimer()}`) : `<div class="note"><span class="spin"></span> ${t('جارٍ…', 'Running…')} ${t('المحاولة', 'attempt')} ${s.attempts}</div>`;
  return pageTitle(t('المعالجة', 'Processing'), `${t('المتقدم', 'Applicant')} ${who(s.candidate_ref)} · ${esc(s.job_title)} · ${chipAi(s.status)}`, `<button class="btn primary" data-action="openApp" data-id="${esc(s.candidate_ref)}" data-scr="${s.screening_id}" ${done ? '' : 'disabled'}>${t('فتح شاشة المتقدم', 'Open applicant')} ↗</button>`) +
  `<div class="card"><h2>${t('خط المعالجة', 'Pipeline')} <small>${t('استلام ← قراءة الإجابات ← نص السيرة ← إخفاء الهوية ← الملف المنظّم ← التحقق من الأدلة ← الشروط ← الحكم ← الدرجة ← الفهرسة', 'intake → answers → CV text → redaction → profile → evidence → rules → judgement → score → index')}</small></h2><div class="pipe pipe-grid">${steps}</div>${result}</div>`;
}


/* ---------- CV analysis (shared by the applicant analysis and «جرّب ملف») ---------- */
const confCls = c => c >= 0.9 ? 'hi' : c >= 0.8 ? 'mid' : 'lo';
function cvAnalysisHtml(d){
  const lay = d.layout || {pages:[], lines:[]}; const pages = lay.pages || []; const P = S.cvPage || 0; const pg = pages[P] || {w:1, h:1};
  const sel = S.cvSel; const selBoxes = new Set(); const selLines = new Set();
  if (sel && d.quote_boxes && d.quote_boxes[sel]) d.quote_boxes[sel].forEach(([li, bi]) => { selLines.add(li); selBoxes.add(li + ':' + bi); });
  if (S.cvLine != null) selLines.add(S.cvLine);
  const rects = (lay.lines || []).map((ln, li) => ln.p !== P ? '' : (ln.boxes && ln.boxes.length ? ln.boxes : [[...ln.b, ln.c, ln.t]]).map((b, bi) => {
    const hit = selBoxes.has(li + ':' + bi) || selBoxes.has(li + ':-1') || S.cvLine === li;
    return `<rect class="ocrbox ${confCls(b[4])} ${hit ? 'hit' : ''}" x="${b[0]}" y="${b[1]}" width="${Math.max(1, b[2] - b[0])}" height="${Math.max(1, b[3] - b[1])}" data-action="cvLine" data-line="${li}"><title>${esc(b[5] || ln.t)} — ${Math.round((b[4] ?? ln.c) * 100)}%</title></rect>`; }).join('')).join('');
  const img = d.page_images && d.page_images[P] ? d.page_images[P] : null;
  const viewer = img ? `<div class="pageview"><img src="${esc(img)}" alt="page ${P + 1}"><svg viewBox="0 0 ${pg.w} ${pg.h}" preserveAspectRatio="none">${rects}</svg></div>` : `<p class="hint">${t('لا توجد صورة للصفحة', 'No page image')}</p>`;
  const pager = pages.length > 1 ? `<div class="seg" style="margin-bottom:8px">${pages.map((_, i) => `<button class="${i === P ? 'on' : ''}" data-action="cvPage" data-p="${i}">${t('صفحة', 'Page')} ${i + 1}</button>`).join('')}</div>` : '';
  const lines = (lay.lines || []).map((ln, li) => `<div class="ocrline ${selLines.has(li) ? 'hit' : ''}" data-action="cvLine" data-line="${li}"><span class="cf ${confCls(ln.c)}">${lay.source === 'image' || d.ocr_confidence != null ? Math.round(ln.c * 100) + '%' : t('نص', 'text')}</span><span class="ln">${esc(ln.t)}</span>${pages.length > 1 ? `<span class="hint">p${ln.p + 1}</span>` : ''}</div>`).join('');
  const tokenize = x => esc(x).replace(/\[[^\]]{1,20}\]/g, m => `<mark class="tok">${m}</mark>`);
  const pairs = d.redaction_pairs && d.redaction_pairs.length ? `<table class="redact"><thead><tr><th>${t('قبل — النص كما استُخرج', 'Before — as extracted')}</th><th>${t('بعد — ما يصل إلى النموذج اللغوي', 'After — what reaches the language model')}</th></tr></thead><tbody>${d.redaction_pairs.filter(([a, b]) => a || b).map(([a, b]) => `<tr class="${a !== b ? 'chg' : ''}"><td>${esc(a)}</td><td>${tokenize(b)}</td></tr>`).join('')}</tbody></table>` : `<div class="grid2"><div><b class="lbl">${t('قبل', 'Before')}</b><div class="cvtext">${esc(d.raw_text || '')}</div></div><div><b class="lbl">${t('بعد', 'After')}</b><div class="cvtext">${tokenize(d.redacted_text || '')}</div></div></div>`;
  const counts = d.redaction && d.redaction.counts ? Object.entries(d.redaction.counts).map(([k, v]) => `<span class="chip">${esc(redactLabel(k))} · ${N(v)}</span>`).join(' ') : `<span class="hint">${t('لم يُعثر على بيانات شخصية', 'no personal data found')}</span>`;
  const ev = (d.criteria || []).filter(c => d.quote_boxes && d.quote_boxes[c.key]).map(c => `<div class="evq ${sel === c.key ? 'on' : ''}" data-action="cvSel" data-key="${c.key}"><b>${esc(c.text)}</b> ${chipLvl(c.cv_level != null ? c.cv_level : c.effective_level)}<div class="quote">${qt(c.cv_quote || String(c.evidence || '').split(' | ')[0])}</div></div>`).join('');
  const avg = d.ocr_confidence != null ? pct(d.ocr_confidence) : t('طبقة نصية (100%)', 'text layer (100%)');
  return `<div class="aihead" style="grid-template-columns:repeat(4,1fr)"><div class="kpi"><small>${t('طريقة الاستخراج', 'Method')}</small><b style="font-size:15px">${method(d.extraction_method || d.method)}</b><div class="hint"><bdi class="num">${esc(d.extraction_method || d.method || '')}</bdi></div></div><div class="kpi"><small>${t('الصفحات / الأسطر', 'Pages / lines')}</small><b>${N(pages.length)} / ${N((lay.lines || []).length)}</b></div><div class="kpi"><small>${t('ثقة القراءة', 'Read confidence')}</small><b style="font-size:17px">${avg}</b></div><div class="kpi"><small>${t('حروف', 'Characters')}</small><b>${N(d.chars || 0)}</b></div></div>
    <div class="split" style="grid-template-columns:1.1fr 1fr"><div class="card"><h2>${t('الملف الأصلي', 'Original file')} <small>${t('مربع لكل سطر أو مقطع بلون الثقة', 'one box per line or segment, coloured by confidence')}</small></h2>${pager}${viewer}<div class="legend"><span class="cf hi">≥ 90%</span><span class="cf mid">80–89%</span><span class="cf lo">&lt; 80%</span><span class="cf hitc">${t('دليل محدد', 'selected evidence')}</span></div></div>
    <div><div class="card"><h2>${t('النص المستخرج', 'Extracted text')} <small>${t('انقر سطرًا لإبرازه على الصورة', 'click a line to locate it on the page')}</small></h2><div class="ocrlines">${lines || `<p class="hint">—</p>`}</div></div>
    ${ev ? `<div class="card"><h2>${t('أدلة السيرة', 'CV evidence')} <small>${t('انقر دليلًا لتظليله في النص والصورة', 'click to highlight it in the text and on the page')}</small></h2>${ev}</div>` : ''}</div></div>
    <div class="card"><h2>${t('إخفاء الهوية: قبل وبعد', 'Redaction: before and after')} <small>${counts}</small></h2>${pairs}<div class="note">${t('الاسم والهاتف والبريد والهوية وتاريخ الميلاد والجنسية والجنس والعنوان تُستبدل برموز قبل أي نموذج لغوي. النموذج يرى عمود «بعد» فقط.', 'Name, phone, e-mail, ID, date of birth, nationality, gender and address are replaced by tokens before any language model. The model only sees the "after" column.')}</div></div>`;
}
async function rCvAnalysis(){
  if (!S.sel) return pageTitle(t('تحليل السيرة', 'CV analysis')) + `<div class="card"><p class="hint">${t('افتح متقدمًا له سيرة ثم اضغط «تحليل السيرة»، أو استخدم «جرّب ملف».', 'Open an applicant with a CV and press "CV analysis", or use "Try a file".')}</p></div>`;
  if (!S.scr) S.scr = await latestScreening(S.sel);
  const doc = (await get(`/v1/candidates/${encodeURIComponent(S.sel)}/cv?include_raw=true`)).document;
  let s = null; if (S.scr) s = await get(`/v1/screenings/${S.scr}`);
  const d = {...doc, page_images:(doc.page_images || []).map(x => `/v1/candidates/${encodeURIComponent(S.sel)}/cv/${x}`), quote_boxes:s && s.cv ? s.cv.quote_boxes : {}, criteria:s ? s.criteria : []};
  if (doc.status !== 'ready') return pageTitle(t('تحليل السيرة', 'CV analysis'), who(S.sel)) + `<div class="card"><div class="note strong">${t('تعذّرت قراءة الملف:', 'The file could not be read:')} ${esc(doc.error)}</div><p><a href="/v1/candidates/${encodeURIComponent(S.sel)}/cv/file" target="_blank">${t('فتح الملف الأصلي', 'Open the original file')}</a></p></div>`;
  return pageTitle(t('تحليل السيرة', 'CV analysis'), `${who(S.sel)} · ${s ? esc(s.job_title) : ''}`, `<a class="btn" href="/v1/candidates/${encodeURIComponent(S.sel)}/cv/file" target="_blank">⤓ ${t('الملف الأصلي', 'Original file')}</a><button class="btn" data-action="openApp" data-id="${esc(S.sel)}" data-scr="${S.scr || ''}">${t('شاشة المتقدم', 'Applicant')} ↗</button>`) + cvAnalysisHtml(d);
}
async function rTryFile(){
  const res = S.tryRes;
  const form = `<div class="card"><h2>${t('جرّب ملف', 'Try a file')} <small>${t('يُقرأ الملف ويُخفى ما فيه من بيانات شخصية ولا يُحفظ شيء', 'the file is read and redacted; nothing is stored')}</small></h2>
    <div class="grid2"><div class="field"><label>${t('الملف', 'File')} (PDF · DOCX · DOC · RTF · JPG · PNG)</label><input type="file" id="try-file" accept=".pdf,.docx,.doc,.rtf,.jpg,.jpeg,.png"></div><div class="field"><label>${t('اسم صاحب السيرة (اختياري، لإخفائه)', 'Name on the CV (optional, to redact it)')}</label><input id="try-name"></div></div>
    <button class="btn primary" data-action="tryRun">${t('اقرأ الملف', 'Read the file')}</button> <span class="hint">${t('الصور والملفات الممسوحة تمر بـ OCR (حوالي 20 ثانية للصفحة).', 'Images and scans go through OCR (about 20 s per page).')}</span>
    <div class="note">${t('بيانات صناعية فقط على هذا الخادم.', 'Synthetic data only on this server.')}</div></div>`;
  if (!res) return pageTitle(t('جرّب ملف', 'Try a file')) + form;
  if (res.busy) return pageTitle(t('جرّب ملف', 'Try a file')) + form + `<div class="card"><span class="spin"></span> ${t('جارٍ القراءة…', 'Reading…')}</div>`;
  if (res.error) return pageTitle(t('جرّب ملف', 'Try a file')) + form + `<div class="card"><div class="note danger">${esc(res.error)}</div></div>`;
  if (res.status !== 'ready') return pageTitle(t('جرّب ملف', 'Try a file')) + form + `<div class="card"><div class="note strong">${t('تعذّرت قراءة الملف:', 'The file could not be read:')} ${esc(res.error || '')}</div></div>`;
  return pageTitle(t('جرّب ملف', 'Try a file')) + form + cvAnalysisHtml(res);
}
async function tryRun(){
  const f = document.getElementById('try-file').files[0]; if (!f) { toast(t('اختر ملفًا', 'Choose a file')); return; }
  const fd = new FormData(); fd.append('file', f, f.name); fd.append('include_raw', 'true'); const nm = document.getElementById('try-name').value.trim(); if (nm) fd.append('name_hint', nm);
  S.tryRes = {busy:true}; S.cvPage = 0; S.cvSel = null; S.cvLine = null; render();
  try { const r = await api('POST', '/v1/documents/inspect', fd, true); S.tryRes = {...r, error: r.status === 'ready' ? null : r.error}; if (r.status !== 'ready') S.tryRes.error = r.error || 'unreadable'; } catch (e) { S.tryRes = {error:e.message}; }
  render();
}

/* ---------- applicants list ---------- */
async function rows_for(ref){ const rk = await get(`/v1/jobs/${encodeURIComponent(ref)}/ranking`); const out = rk.ranked.map(x => ({...x, group:'ranked'})); Object.keys(rk.groups).forEach(g => rk.groups[g].forEach(x => out.push({...x, group:g}))); return {rk, rows:out}; }
async function rList(){
  await loadJobs(); if (!S.job) return `<div class="card">${t('لا شواغر', 'No openings')}</div>`;
  const {rows} = await rows_for(S.job); const F = S.listFilters;
  let list = rows.slice();
  if (F.ai) list = list.filter(x => STATUS_AI[x.status] === F.ai);
  if (F.band) list = list.filter(x => x.band === F.band);
  if (F.elig) list = list.filter(x => x.eligibility === F.elig);
  if (F.q) list = list.filter(x => (nameOf(x.candidate_ref) + ' ' + x.candidate_ref).toLowerCase().includes(F.q.toLowerCase()));
  list.sort((a, b) => S.listSort === 'score' ? ((b.score ?? -1) - (a.score ?? -1)) : S.listSort === 'date' ? String(b.created_at).localeCompare(String(a.created_at)) : nameOf(a.candidate_ref).localeCompare(nameOf(b.candidate_ref)));
  const opt = (v, lbl, cur) => `<option value="${v}" ${cur === v ? 'selected' : ''}>${lbl}</option>`;
  return pageTitle(t('المتقدمون', 'Applicants'), `${N(list.length)} ${t('سجل', 'records')} · ${esc(jobTitle(S.job))}`, jobSelect('pickJobList')) +
  `<div class="card"><div class="filters"><input class="search" placeholder="${t('بحث بالاسم أو الرقم', 'Search by name or reference')}" value="${esc(F.q)}" data-filter="q">
      <select data-filter="ai">${opt('', t('كل حالات المعالجة', 'All ai_status'), F.ai)}${Object.keys(AIST).map(k => opt(k, L(AIST[k]), F.ai)).join('')}</select>
      <select data-filter="band">${opt('', t('كل الفئات', 'All bands'), F.band)}${Object.keys(BAND).map(b => opt(b, L(BAND[b]), F.band)).join('')}</select>
      <select data-filter="elig">${opt('', t('كل حالات الأهلية', 'All eligibility'), F.elig)}${Object.keys(ELIG).map(e => opt(e, L(ELIG[e]), F.elig)).join('')}</select>
      <select data-filter="sort">${opt('score', t('ترتيب: الدرجة', 'Sort: score'), S.listSort)}${opt('date', t('ترتيب: تاريخ التقديم', 'Sort: applied'), S.listSort)}${opt('name', t('ترتيب: الاسم', 'Sort: name'), S.listSort)}</select></div>
    <table><thead><tr><th>${t('الاسم', 'Name')}</th><th>ai_status</th><th>${t('الدرجة', 'Score')}</th><th>${t('الفئة', 'Band')}</th><th>${t('الأهلية', 'Eligibility')}</th><th>${t('الترتيب', 'Rank')}</th><th>${t('تاريخ التقييم', 'Evaluated')}</th></tr></thead><tbody>
    ${list.map(x => `<tr class="row" data-action="openApp" data-id="${esc(x.candidate_ref)}" data-scr="${x.screening_id}"><td><b>${esc(nameOf(x.candidate_ref))}</b>${x.duplicate_of ? ` <span class="chip grey">⧉ ${t('مكرر', 'duplicate')}</span>` : ''}${x.group === 'stale' ? ` <span class="chip grey">⚠ ${t('قديم', 'stale')}</span>` : ''}<div class="list-id num">${esc(x.candidate_ref)}</div></td><td>${chipAi(x.status)}</td><td>${x.score != null && x.status !== 'failed' ? `<b class="score ${x.eligibility === 'not_eligible' ? 'off' : x.band}">${N(fmt1(x.score))}</b>` : '<span class="hint">—</span>'}</td><td>${x.band ? chipBand(x.band, x.eligibility) : ''}</td><td>${chipElig(x.eligibility)}</td><td class="num">${x.rank || '—'}</td><td>${fd(x.completed_at)}</td></tr>`).join('') || `<tr><td colspan="7" class="hint">${t('لا متقدمين', 'No applicants')}</td></tr>`}
    </tbody></table>${disclaimer()}</div>`;
}

/* ---------- applicant ---------- */
async function latestScreening(ref){ const l = (await get(`/v1/screenings?candidate_ref=${encodeURIComponent(ref)}&limit=1`)).screenings; return l.length ? l[0].screening_id : null; }
async function rApplicant(){
  if (!S.scr && S.sel) S.scr = await latestScreening(S.sel);
  if (!S.scr) return `<div class="card">${t('لا تقييم لهذا المتقدم', 'No assessment for this applicant')}</div>`;
  const s = await get(`/v1/screenings/${S.scr}`); S.sel = s.candidate_ref;
  const cand = await get(`/v1/candidates/${encodeURIComponent(s.candidate_ref)}`);
  const job = S.cache['job:' + s.job_ref] || (S.cache['job:' + s.job_ref] = await get(`/v1/jobs/${encodeURIComponent(s.job_ref)}`));
  const questions = (job.version && job.version.questions) || []; const qLabel = {}; questions.forEach(q => { qLabel[q.key] = q.label; }); const critText = {}; (job.version && job.version.criteria || []).forEach(c => { critText[c.key] = c; });
  const f = (lbl, val) => `<div class="field"><label>${lbl}</label><div class="val ro">${val}</div></div>`;
  const factRow = k => cand.facts && cand.facts[k] != null ? esc(cand.facts[k]) : `<span class="chip amber">${t('غير مصرّح', 'not declared')}</span>`;
  const head = pageTitle(esc(nameOf(s.candidate_ref)), `Job Applicant · ${N(s.candidate_ref)} · ${esc(s.job_title)} · ai_status ${chipAi(s.status)} ${flagChips(s.flags.filter(x => x !== 'hr_override'))}`,
    `${s.cv && s.cv.status === 'ready' ? `<button class="btn primary" data-action="go" data-screen="cv">◫ ${t('تحليل السيرة', 'CV analysis')}</button>` : ''}<button class="btn" data-action="rescreenOne" data-id="${esc(s.candidate_ref)}" data-job="${esc(s.job_ref)}">↻ ${t('إعادة التقييم', 'Re-score')}</button><button class="btn" data-action="go" data-screen="ranking">${t('الترتيب', 'Ranking')} ↗</button>`);
  const dupBox = s.duplicate_of ? `<div class="note grey">⧉ <b>${t('طلب مكرر', 'Duplicate application')}</b> — ${t('نفس بصمة الهوية مثل', 'Same id token as')} <b class="num">${esc(s.duplicate_of)}</b>. ${t('لا يُحذف أي طلب تلقائيًا؛ يُرتَّب الطلب الأصلي فقط.', 'Nothing is deleted automatically; only the original application is ranked.')}</div>` : '';
  const staleBox = !s.current ? `<div class="note grey">⚠ ${s.stale_reason === 'data_changed' ? t('النتيجة لا تعكس آخر تعديل على بيانات المتقدم', 'The result does not reflect the latest edit to the applicant data') : t('هذه النتيجة محسوبة بنسخة معايير سابقة', 'This result was computed with a previous criteria version')} (${N('v' + s.job_version)}). ${t('لا تدخل الترتيب حتى تُعاد.', 'It is not ranked until re-scored.')} <button class="btn sm primary" data-action="rescreenOne" data-id="${esc(s.candidate_ref)}" data-job="${esc(s.job_ref)}">↻ ${t('إعادة التقييم', 'Re-score')}</button></div>` : '';
  if (s.status === 'failed' || s.status === 'queued' || s.status === 'processing') return head + dupBox + `<div class="card"><h2>${t('تقييم الذكاء الاصطناعي', 'AI assessment')} ${chipAi(s.status)}</h2>${s.status === 'failed' ? `<div class="note danger">✗ ${esc(s.error)} — ${t('بعد', 'after')} ${s.attempts} ${t('محاولات. الطلب محفوظ وإجاباته كاملة.', 'attempts. The application is saved with its answers.')}</div><div style="margin-top:10px"><button class="btn primary" data-action="retry" data-id="${s.screening_id}">↻ ${t('إعادة المحاولة', 'Retry')}</button></div>` : `<div class="note"><span class="spin"></span> ${t('جاري المعالجة…', 'Processing…')} <button class="btn sm" data-action="go" data-screen="processing">${t('متابعة', 'Follow')}</button></div>`}</div>` + answersCard(cand, questions);
  const checks = (s.eligibility_checks || []).map(c => `<li>${c.ok === true ? '✓' : c.ok === false ? '✗' : '?'} ${mix(S.lang === 'ar' ? c.text_ar : c.text_en)}</li>`).join('');
  const evCell = c => { if (c.missing_evidence && c.overridden_level == null) return `<span class="src missing">${t('دليل ناقص', 'missing evidence')}</span> <span class="hint">${t('لم يُجب ولا تذكره السيرة', 'not answered and not in the CV')}</span>`; if (c.contradiction) { const parts = String(c.evidence || '').split(' | '); return `<div class="contra"><div><span class="src cv">${t('من السيرة', 'from the CV')}</span> <span class="quote" data-action="hilite" data-key="${c.key}">${qt(parts[0])}</span> → ${chipLvl(c.level)}</div><div><span class="src form">${t('إجابة النموذج', 'form answer')}</span> <span class="quote none">${esc((parts[1] || '').replace(/^إجابة النموذج: /, ''))}</span></div><div class="chip amber">⇄ ${t('تعارض — يُستخدم الأدنى', 'contradiction — the lower is used')}</div></div>`; } if (c.source === 'cv_quote') return `<span class="src cv">${t('من السيرة', 'from the CV')}</span> <span class="quote" data-action="hilite" data-key="${c.key}">${qt(c.evidence)}</span>`; const ql = qLabel[c.field] ? `${esc(qLabel[c.field])}: ` : ''; const conf = c.cv_quote ? `<div style="margin-top:4px"><span class="src cv">${c.confirmed_by_cv ? t('تؤكده السيرة', 'confirmed by CV') : t('من السيرة', 'from the CV')} ${c.cv_level != null ? '· ' + c.cv_level : ''}</span> <span class="quote" data-action="hilite" data-key="${c.key}">${qt(c.cv_quote)}</span></div>` : ''; return `<span class="src form">${t('إجابة النموذج', 'form answer')}</span> <span class="quote none">${ql}<b>${esc(c.evidence)}</b></span>${conf}`; };
  const rubricText = (key, lvl) => { const c = critText[key]; const r = c && c.rubric.find(x => x.level === lvl); return r ? esc(r.text) : ''; };
  const crit = s.criteria.map(c => `<tr class="${S.hiliteKey === c.key ? 'sel' : ''}"><td>${esc(c.text)}</td><td>${chipMand(c.mandatory)}</td><td class="num">${c.weight}%</td><td>${chipLvl(c.effective_level)} <span class="hint">${rubricText(c.key, c.effective_level)}</span>${c.overridden_level != null ? ` <span class="tag-hr" title="${esc(c.override_reason)}">${t('تعديل HR', 'HR edit')}</span><div class="hint">${t('مستوى الذكاء:', 'AI level:')} ${c.missing_evidence ? t('دليل ناقص', 'missing') : c.level} · ${esc(c.override_by)}: ${esc(c.override_reason)}</div>` : ''}</td><td>${evCell(c)}</td><td><button class="btn sm" data-action="override" data-key="${c.key}" data-text="${esc(c.text)}">${t('إلغاء الحكم', 'Override')}</button></td></tr>`).join('');
  const strengths = s.strengths.map(x => `<div class="chip green" style="margin:3px 2px">${esc(x.text)} · ${x.level}</div>`).join('') || `<p class="hint">${t('لا شيء', 'none')}</p>`;
  const gaps = s.gaps.map(x => `<div class="chip ${x.missing ? 'amber' : 'red'}" style="margin:3px 2px">${esc(x.text)} · ${x.missing ? t('دليل ناقص', 'missing') : x.level}</div>`).join('') || `<p class="hint">${t('لا شيء', 'none')}</p>`;
  const raise = s.raise_score.length ? `<ul class="ul">${s.raise_score.map(x => `<li>${x.missing ? t('تقديم دليل على', 'Provide evidence for') : t('إثبات المستوى 100 في', 'Prove level 100 in')} «${esc(x.text)}»: <b class="num">+${fmt1(x.points)}</b> ${t('نقطة', 'points')}</li>`).join('')}</ul>` : `<p class="hint">${t('الدرجة كاملة', 'Full score')}</p>`;
  const cv = s.cv; const quotes = s.criteria.map(c => ({q:c.cv_quote || ((c.source === 'cv_quote' || c.contradiction) && c.evidence ? String(c.evidence).split(' | ')[0] : ''), key:c.key})).filter(x => x.q);
  let cvHtml;
  if (!cv) cvHtml = `<p class="hint">${t('لم يرفع المتقدم سيرة ذاتية. التقييم من إجابات النموذج فقط.', 'No CV uploaded. Assessed from the form answers only.')}</p>`;
  else if (cv.status !== 'ready') cvHtml = `<div class="note strong">${t('تعذّرت قراءة الملف:', 'The file could not be read:')} ${esc(cv.error)}</div>`;
  else { let h = esc(cv.redacted_text || ''); quotes.forEach(({q, key}) => { const eq = esc(q); if (eq && h.includes(eq)) h = h.replace(eq, `<mark class="${S.hiliteKey === key ? 'hot' : ''}" id="q-${key}">${eq}</mark>`); }); cvHtml = `<div class="cvtext">${h}</div><p class="hint">${t('النص بعد إخفاء البيانات الشخصية كما يراه النموذج. الاقتباسات المظلّلة هي أدلة السيرة.', 'The redacted text as the model sees it. Highlighted quotes are the CV evidence.')} ${cv.method ? `· ${method(cv.method)}` : ''}${cv.ocr_confidence != null ? ` · ${t('ثقة OCR', 'OCR confidence')} ${N(pct(cv.ocr_confidence))}` : ''}${cv.redaction && cv.redaction.counts ? ` · ${t('أُخفي:', 'removed:')} ${Object.entries(cv.redaction.counts).map(([k, v]) => `${esc(redactLabel(k))} (${N(v)})`).join('، ')}` : ''}</p>`; }
  const vers = s.versions || {};
  return head + dupBox + staleBox +
  `<div class="split"><div>
    <div class="card"><h2>${t('تقييم الذكاء الاصطناعي', 'AI assessment')} <span class="chip blue">${t('قراءة فقط — لا يغيّر الحالة', 'read-only — never changes status')}</span></h2>
      <div class="aihead">
        <div class="kpi"><small>${t('الأهلية', 'Eligibility')}</small>${chipElig(s.eligibility)}</div>
        <div class="kpi"><small>${t('الدرجة', 'Score')} <code>ai_score</code></small><b class="score ${s.eligibility === 'not_eligible' ? 'off' : s.band}">${N(fmt1(s.score))}</b> <span class="hint">/ 100</span><div>${chipBand(s.band, s.eligibility)}</div></div>
        <div class="kpi"><small>${t('التغطية', 'Coverage')}</small><b>${N(pct(s.coverage))}</b>${s.needs_review ? `<div><span class="chip amber">${t('يحتاج مراجعة', 'Needs review')}</span></div>` : ''}</div>
        <div class="kpi"><small>${t('الترتيب في الشاغر', 'Rank in opening')}</small><b>${s.rank ? `${N(s.rank)} ${t('من', 'of')} ${N(s.ranked_total)}` : '—'}</b>${!s.rank ? `<div class="hint">${s.eligibility === 'not_eligible' ? t('غير مرتَّب — غير مستوفٍ', 'Not ranked — not eligible') : s.duplicate_of ? t('غير مرتَّب — طلب مكرر', 'Not ranked — duplicate') : !s.current ? t('غير مرتَّب — نتيجة قديمة', 'Not ranked — stale') : t('غير مرتَّب — يحتاج مراجعة', 'Not ranked — needs review')}</div>` : ''}</div>
      </div>
      <div class="grid2"><div><b class="lbl">${t('أسباب الأهلية', 'Eligibility reasons')}</b><ul class="ul">${checks || `<li>${t('لا شروط إلزامية لهذا الشاغر', 'No hard rules for this opening')}</li>`}</ul></div><div><b class="lbl">${t('الملخص', 'Summary')}</b><div class="summary">${mix(s.summary)}</div></div></div>
      ${s.flags.includes('mandatory_zero') ? `<div class="note danger">${t('معيار إلزامي في المستوى 0 ← الفئة «منخفضة» بغض النظر عن الدرجة.', 'A mandatory criterion at level 0 → band "Low" regardless of the score.')}</div>` : ''}
      ${s.flags.includes('contradiction') ? `<div class="note strong">⇄ ${t('تعارض بين الإجابة والسيرة: يُستخدم المستوى الأدنى المدعوم بالدليل، والطلب يحتاج مراجعة بشرية.', 'Answer vs CV contradiction: the lower evidenced level is used and the application needs human review.')}</div>` : ''}
      ${s.flags.includes('cv_unreadable') ? `<div class="note strong">${t('ملف السيرة غير مقروء — التقييم من الإجابات فقط.', 'The CV file is unreadable — assessed from the answers only.')}</div>` : ''}
      ${disclaimer()}
    </div>
    <div class="card"><h2>${t('نقاط القوة والنواقص', 'Strengths and gaps')}</h2><div class="grid3"><div><b class="lbl">${t('نقاط القوة', 'Strengths')} <span class="hint">(75–100)</span></b>${strengths}</div><div><b class="lbl">${t('النواقص', 'Gaps')} <span class="hint">(0–25 ${t('أو دليل ناقص', 'or missing')})</span></b>${gaps}</div><div><b class="lbl">${t('ما الذي يرفع درجته', 'What would raise the score')}</b>${raise}</div></div></div>
    <div class="card"><h2>${t('المعايير والأدلة', 'Criteria and evidence')} <small>AI Assessment Evidence · ${t('انقر اقتباس السيرة لإبرازه', 'click a CV quote to highlight it')}</small></h2>
      <table><thead><tr><th>${t('المعيار', 'Criterion')}</th><th>${t('النوع', 'Type')}</th><th>${t('الوزن', 'W')}</th><th>${t('المستوى', 'Level')}</th><th>${t('الدليل', 'Evidence')}</th><th></th></tr></thead><tbody>${crit}</tbody></table>
      <div class="audit"><span>${t('المزوّد', 'provider')}: <code>${esc(vers.provider)}</code></span><span>${t('النموذج', 'model')}: <code>${esc(vers.model)}</code></span><span>${t('الموجّه', 'prompt')}: <code>${esc(vers.prompt)}</code></span><span>${t('نسخة المعايير', 'profile version')}: <code>v${s.job_version}</code></span><span>${t('بصمة المدخلات', 'input hash')}: <code>${esc(String(s.input_hash).slice(0, 23))}…</code></span><span>${t('تاريخ التقييم', 'evaluated on')}: ${fd(s.completed_at)}</span><span>${t('الوقت', 'time')}: <code>${((vers.total_ms || 0) / 1000).toFixed(1)}s</code></span></div>${disclaimer()}</div>
    ${answersCard(cand, questions, job.version ? job.version.criteria : [])}
    <div class="card"><h2>${t('بيانات المتقدم', 'Applicant details')} <small>${t('الحقائق المسموحة فقط تُرسل للمحرك', 'only the allowed facts reach the engine')}</small></h2><div class="grid2">
      ${f(t('الاسم (في متصفحك فقط)', 'Name (this browser only)'), esc(nameOf(s.candidate_ref)))}${f(t('بصمة الهوية', 'ID token'), cand.id_token ? `<span class="num">${esc(cand.id_token.slice(0, 16))}…</span> <span class="hint">(HMAC)</span>` : '—')}
      ${Object.keys(FACTS).filter(k => cand.facts && k in cand.facts).map(k => f(L(FACTS[k]), factRow(k))).join('')}
      ${f(t('السيرة', 'CV'), cv ? (cv.status === 'ready' ? `<span class="chip green">${method(cv.method)}</span>` : `<span class="chip red">${t('غير مقروءة', 'unreadable')}</span>`) : `<span class="chip">${t('بدون سيرة', 'No CV')}</span>`)}${f(t('تاريخ التقديم', 'Applied on'), fd(cand.created_at))}
    </div></div>
  </div>
  <div class="cvpanel"><div class="card"><h2>${t('عرض السيرة الذاتية', 'CV viewer')}</h2>${cvHtml}</div></div></div>`;
}
function answersCard(cand, questions, criteria){
  criteria = criteria || []; const feeds = k => criteria.filter(c => c.question === k).map(c => esc(c.text)).join('، ');
  if (!questions.length) return '';
  const blank = v => v == null || v === '' || (Array.isArray(v) && !v.length);
  return `<div class="card"><h2>${t('إجابات نموذج التقديم', 'Application form answers')} <small>${t('المصدر الأساسي للتقييم', 'primary source of the assessment')}</small></h2><table><thead><tr><th>${t('السؤال', 'Question')}</th><th>${t('الإجابة', 'Answer')}</th><th>${t('يغذّي', 'Feeds')}</th></tr></thead><tbody>${questions.map(q => { const v = cand.answers[q.key]; return `<tr><td>${esc(q.label)}</td><td>${blank(v) ? `<span class="chip amber">${t('لم يُجب', 'not answered')}</span>` : `<b>${esc(Array.isArray(v) ? v.join('، ') : v)}</b>${(v === 0 || v === '0') ? ` <span class="hint">(${t('صفر حقيقي — ليس فراغًا', 'a real zero, not blank')})</span>` : ''}`}</td><td class="hint">${feeds(q.key) || t('معلومة فقط', 'info only')}</td></tr>`; }).join('')}</tbody></table></div>`;
}
async function doOverride(key, text){
  const s = await get(`/v1/screenings/${S.scr}`); const c = s.criteria.find(x => x.key === key);
  modal(`<h3>${t('إلغاء حكم الذكاء', 'Override the AI judgement')}: ${esc(text)}</h3><div class="field"><label>${t('المستوى الجديد', 'New level')}</label><select id="m-level">${LEVELS.map(l => `<option value="${l}" ${l === c.effective_level ? 'selected' : ''}>${l}</option>`).join('')}</select></div><div class="field"><label>${t('السبب', 'Reason')} <span class="req">*</span></label><textarea id="m-reason" placeholder="${t('مطلوب — يُسجَّل في سجل التدقيق مع اسمك', 'Required — recorded in the audit log with your name')}"></textarea></div><div class="acts"><button class="btn" data-action="closeModal">${t('إلغاء', 'Cancel')}</button><button class="btn primary" id="m-ok">${t('تأكيد', 'Confirm')}</button></div>`);
  document.getElementById('m-ok').onclick = async () => { const r = document.getElementById('m-reason').value.trim(); if (!r) { toast(t('السبب مطلوب', 'A reason is required')); return; } const lvl = Number(document.getElementById('m-level').value); closeModal(); try { await api('POST', `/v1/screenings/${S.scr}/override`, {criterion_key:key, level:lvl, reason:r, by:`console:${S.user}`}); toast(t('تم التعديل وأُعيد حساب الدرجة', 'Overridden; the score was recomputed')); render(); } catch (e) { toast(e.message); } };
}

/* ---------- ranking ---------- */
async function rRanking(){
  await loadJobs(); if (!S.job) return `<div class="card">${t('لا شواغر', 'No openings')}</div>`;
  const rk = await get(`/v1/jobs/${encodeURIComponent(S.job)}/ranking`); const job = S.cache['job:' + S.job] || (S.cache['job:' + S.job] = await get(`/v1/jobs/${encodeURIComponent(S.job)}`)); const crit = (job.version && job.version.criteria) || [];
  const row = x => `<div class="rankrow r1"><div class="pos num">${x.rank}</div><div class="c-name"><b class="${nameOf(x.candidate_ref) === x.candidate_ref ? 'num' : ''}">${esc(nameOf(x.candidate_ref))}</b><div class="list-id">${nameOf(x.candidate_ref) === x.candidate_ref ? '' : `<span class="num">${esc(x.candidate_ref)}</span> · `}v${x.job_version}</div></div><div><b class="score ${x.band}">${N(fmt1(x.score))}</b></div><div>${chipBand(x.band)}</div><div class="bar ${x.band}"><i style="width:${x.score}%"></i></div><div class="hint">${t('تغطية', 'cov.')} ${N(pct(x.coverage))}</div><div><button class="btn sm" data-action="openApp" data-id="${esc(x.candidate_ref)}" data-scr="${x.screening_id}">↗</button></div></div>`;
  const other = x => `<div class="rankrow r3"><div class="pos off">—</div><div class="c-name"><b class="${nameOf(x.candidate_ref) === x.candidate_ref ? 'num' : ''}">${esc(nameOf(x.candidate_ref))}</b><div class="list-id">${mix(S.lang === 'ar' ? x.reason_ar : x.reason_en)}</div></div><div>${x.score != null && x.status !== 'failed' ? `<b class="score ${x.eligibility === 'not_eligible' ? 'off' : x.band}">${N(fmt1(x.score))}</b>` : '<span class="hint">—</span>'}</div><div class="c-chips">${chipAi(x.status)} ${chipElig(x.eligibility)}</div><div><button class="btn sm" data-action="openApp" data-id="${esc(x.candidate_ref)}" data-scr="${x.screening_id}">↗</button></div></div>`;
  const stale = rk.groups.stale.length;
  return pageTitle(`${t('ترتيب الشاغر', 'Ranking')}: ${esc(rk.job_title)}`, `${N(rk.total)} ${t('متقدمًا', 'applicants')} · ${N(rk.ranked_total)} ${t('مرتَّبون', 'ranked')} · ${t('نسخة المعايير', 'profile version')} ${N('v' + rk.job_version)}`,
    `${jobSelect('pickJobRanking')}<button class="btn" data-action="rescreenAll">↻ ${t('إعادة تقييم الكل', 'Re-score all')}</button><button class="btn primary" data-action="exportCsv">⤓ ${t('تصدير القائمة', 'Export shortlist')} CSV</button>`) +
  (stale ? `<div class="note grey">⚠ ${N(stale)} ${t('تقييمات قديمة لا تدخل الترتيب.', 'stale assessments are excluded from the ranking.')} <button class="btn sm primary" data-action="rescreenAll">↻ ${t('إعادة تقييم الكل', 'Re-score all')}</button></div>` : '') +
  `<div class="split" style="grid-template-columns:2.6fr 1fr"><div>
    <div class="card"><h2>${t('المرتَّبون (مكتملون ومستوفون)', 'Ranked (completed and eligible)')} <small>${t('من الأعلى إلى الأدنى', 'high to low')}</small></h2>${rk.ranked.map(row).join('') || `<p class="hint">${t('لا أحد', 'Nobody')}</p>`}${disclaimer()}</div>
    ${Object.keys(GROUPS).map(g => `<details class="collapse" ${rk.groups[g].length ? '' : ''}><summary>${L(GROUPS[g])} (${N(rk.groups[g].length)}) — ${L(GROUPS[g].why)}</summary><div style="margin-top:10px">${rk.groups[g].map(other).join('') || `<p class="hint">${t('لا أحد', 'Nobody')}</p>`}</div></details>`).join('')}
  </div>
  <div><div class="card"><h2>${t('الأوزان المعتمدة', 'Approved weights')} <small>v${rk.job_version}</small></h2><table><tbody>${crit.map(c => `<tr><td>${esc(c.text)} ${c.mandatory ? chipMand(true) : ''}</td><td class="num">${c.weight}%</td></tr>`).join('')}<tr><td><b>${t('المجموع', 'Total')}</b></td><td class="num"><b>${crit.reduce((a, c) => a + c.weight, 0)}%</b></td></tr></tbody></table><p class="hint">${t('تغيير الأوزان يكون من ملف المعايير (مسودة ← اعتماد نسخة جديدة ← إعادة تقييم الكل).', 'Weights change through the AI Job Profile (draft → approve a new version → re-score all).')}</p></div>
    <div class="card"><h2>${t('كيف يُحسب', 'How it is computed')}</h2><div class="kv"><small>${t('الدرجة', 'score')}</small><span class="num">Σ(w% × level) ÷ 100</span><small>${t('المستويات', 'levels')}</small><span class="num">0 · 25 · 50 · 75 · 100</span><small>${t('التغطية', 'coverage')}</small><span class="num">Σw(evidence) ÷ Σw</span><small>${t('الفئات', 'bands')}</small><span class="bands"><span class="chip green">${t('مرتفعة: 75 فأكثر', 'high: 75+')}</span><span class="chip amber">${t('متوسطة: 50 إلى 74.9', 'medium: 50–74.9')}</span><span class="chip red">${t('منخفضة: أقل من 50', 'low: below 50')}</span></span><small>${t('إلزامي', 'mandatory')}</small><span>${t('المستوى 0 ← منخفضة؛ بلا دليل ← يحتاج مراجعة', 'level 0 → low; no evidence → needs review')}</span></div>${disclaimer()}</div>
  </div></div>`;
}
async function exportCsv(){
  const rk = await get(`/v1/jobs/${encodeURIComponent(S.job)}/ranking`);
  const head = ['rank', 'applicant_ref', 'name', 'score', 'band', 'coverage', 'ai_status', 'profile_version', 'strengths'];
  const lines = rk.ranked.map(x => [x.rank, x.candidate_ref, nameOf(x.candidate_ref), fmt1(x.score), L(BAND[x.band]), pct(x.coverage), L(AIST[STATUS_AI[x.status]]), 'v' + x.job_version, (x.strengths || []).join(' | ')]);
  const csv = '﻿' + [head].concat(lines).map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\r\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `shortlist_${S.job}.csv`; document.body.appendChild(a); a.click(); a.remove();
  toast(t('نُزّل ملف CSV (UTF-8 مع BOM) يفتح بالعربية في Excel', 'CSV downloaded (UTF-8 with BOM), opens correctly in Excel'));
}

/* ---------- AI jobs ---------- */
async function rJobs(){
  const list = (await get('/v1/screenings?limit=200')).screenings;
  const c = st => list.filter(x => x.status === st).length;
  const rows = list.map(x => `<tr><td class="num">${esc(x.screening_id)}</td><td><b>${esc(nameOf(x.candidate_ref))}</b><div class="list-id num">${esc(x.candidate_ref)}</div></td><td>${esc(x.job_title)} <span class="hint">v${x.job_version}</span></td><td>${chipAi(x.status)}</td><td class="num">${x.attempts}</td><td>${fd(x.created_at)}</td><td>${x.error ? `<span class="was">${esc(x.error).slice(0, 120)}</span>` : '—'}</td><td>${x.status === 'failed' ? `<button class="btn sm primary" data-action="retry" data-id="${x.screening_id}">↻ ${t('إعادة المحاولة', 'Retry')}</button>` : `<button class="btn sm" data-action="openApp" data-id="${esc(x.candidate_ref)}" data-scr="${x.screening_id}">↗</button>`}</td></tr>`).join('');
  return pageTitle(t('مهام الذكاء الاصطناعي', 'AI Recruitment Jobs'), `AI Recruitment Job · ${N(list.length)} ${t('مهمة (آخر 200)', 'jobs (last 200)')} · ${t('طابور خلفي', 'background queue')}`, `<button class="btn" data-action="go" data-screen="jobs">↻ ${t('تحديث', 'Refresh')}</button>`) +
  `<div class="aihead" style="grid-template-columns:repeat(5,1fr)">${[['queued', 'في الانتظار', 'Queued'], ['processing', 'جارٍ', 'Running'], ['completed', 'مكتمل', 'Completed'], ['needs_review', 'يحتاج مراجعة', 'Needs review'], ['failed', 'فشل', 'Failed']].map(([k, ar, en]) => `<div class="kpi"><small>${t(ar, en)}</small><b>${N(c(k))}</b></div>`).join('')}</div>
  <div class="card"><div class="tscroll"><table><thead><tr><th>${t('المهمة', 'Job')}</th><th>${t('المتقدم', 'Applicant')}</th><th>${t('الشاغر', 'Opening')}</th><th>${t('الحالة', 'Status')}</th><th>${t('المحاولات', 'Attempts')}</th><th>${t('الوقت', 'Time')}</th><th>${t('رسالة الخطأ', 'Error')}</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>
  <div class="note">${t('فشل المهمة لا يمنع حفظ الطلب ولا يغيّر حالته. الملف التالف لا يُفشل المهمة: يُقيَّم من الإجابات مع علامة.', 'A failed job never blocks saving the application or changes its status. A corrupt file never fails a job: the applicant is assessed from the answers with a flag.')}</div></div>`;
}

/* ---------- settings ---------- */
async function rSettings(){
  const s = S.settings = await get('/v1/settings');
  const facts = ['nationality', 'age', 'height_cm', 'weight_kg', 'gender'];
  return pageTitle(t('إعدادات الذكاء الاصطناعي للتوظيف', 'AI Recruitment Settings'), `AI Recruitment Settings · ${t('المحرّك هو مالك هذه القيم', 'the engine owns these values')} · <code>GET/PUT /v1/settings</code>`, `<button class="btn primary" data-action="saveSettings">${t('حفظ', 'Save')}</button>`) +
  `<div class="grid2"><div class="card"><h2>${t('المزوّد والنموذج', 'Provider and model')}</h2>
    <div class="field"><label>${t('المزوّد', 'Provider')} <code>ai_provider</code></label><div class="seg">${['local', 'cloud', 'fake'].map(p => `<button class="${s.ai_provider === p ? 'on' : ''}" data-setting="ai_provider" data-val="${p}">${p === 'local' ? t('محلي (vLLM داخل الشبكة)', 'Local (vLLM in the network)') : p === 'cloud' ? t('سحابي', 'Cloud') : t('وهمي (اختبار)', 'Fake (tests)')}</button>`).join('')}</div><div class="hint" style="margin-top:4px">${esc(s.providers[s.ai_provider])} · ${s.provider_ready ? `<span class="chip green">${t('جاهز', 'ready')}</span>` : `<span class="chip red">${esc(s.provider_note)}</span>`}</div></div>
    <div class="grid2"><div class="field"><label>${t('النموذج', 'Model')} <code>ai_model</code></label><input value="${esc(s.ai_model)}" data-setting="ai_model" class="num"></div><div class="field"><label>${t('موجّه الحكم', 'Judge prompt')} <code>judge_prompt</code></label><select data-setting="judge_prompt">${['judge-v1', 'judge-v2'].map(p => `<option ${s.judge_prompt === p ? 'selected' : ''}>${p}</option>`).join('')}</select></div></div>
    <div class="grid2"><div class="field"><label>${t('المهلة (ثانية)', 'Timeout (s)')} <code>llm_timeout_s</code></label><input class="num" type="number" value="${s.llm_timeout_s}" data-setting="llm_timeout_s"></div><div class="field"><label>${t('أقصى عدد محاولات', 'Max retries')} <code>max_retries</code></label><input class="num" type="number" value="${s.max_retries}" data-setting="max_retries"></div></div>
    ${s.ai_provider === 'cloud' ? `<div class="note strong">⚠ ${t('الوضع السحابي يرسل النص المُخفى الهوية إلى مزوّد خارجي. يتطلب موافقة خطية من العميل وفق نظام حماية البيانات الشخصية.', 'Cloud mode sends the redacted text to an external provider. It requires written client approval under the PDPL.')}</div>` : `<div class="note">${t('الوضع المحلي: لا تغادر أي بيانات الخادم.', 'Local mode: no data leaves the server.')}</div>`}
  </div>
  <div class="card"><h2>${t('قراءة المستندات والاحتفاظ', 'Documents and retention')}</h2>
    <div class="field"><label>OCR <code>ocr_provider</code></label><select data-setting="ocr_provider">${Object.keys(s.ocr_providers).map(p => `<option value="${p}" ${s.ocr_provider === p ? 'selected' : ''}>${p} — ${esc(s.ocr_providers[p])}</option>`).join('')}</select><div class="hint">${s.ocr_ready ? `<span class="chip green">${t('جاهز', 'ready')}</span>` : `<span class="chip red">${esc(s.ocr_note)}</span>`}</div></div>
    <div class="field"><label>${t('الاحتفاظ بالبيانات (يوم)', 'Retention (days)')} <code>retention_days</code></label><input class="num" type="number" value="${s.retention_days}" data-setting="retention_days"></div>
    <div class="field"><label>${t('عنوان الـ callback', 'Callback URL')} <code>callback_url</code></label><input class="num" value="${esc(s.callback_url || '')}" data-setting="callback_url" placeholder="http://host.docker.internal:18060/callback"></div>
    <div class="field"><label>${t('سر الـ callback', 'Callback secret')} <code>callback_secret</code></label><input type="password" value="" data-setting="callback_secret" placeholder="${s.callback_secret_set ? t('محفوظ — اتركه فارغًا للإبقاء', 'set — leave blank to keep') : t('غير محدد', 'not set')}"></div>
  </div></div>
  <div class="card"><h2>${t('البيانات المسموح بإرسالها إلى المحرك', 'Facts allowed to be sent to the engine')} <code>allowed_facts</code></h2>
    <div>${facts.map(k => `<label class="tgl" style="margin-inline-end:16px"><input type="checkbox" ${s.allowed_facts.includes(k) ? 'checked' : ''} data-fact="${k}"> <span class="num">${k}</span></label>`).join('')}</div>
    <div class="note">${t('لا يُرسل أبدًا: الاسم، البريد، الجوال، رقم الهوية، تاريخ الميلاد، الصورة. العمر يُحسب في النظام ويُرسل كرقم. الجنسية والعمر للشروط فقط ولا يراهما النموذج اللغوي. مفتاح الـ API لا يظهر هنا ولا في المتصفح.', 'Never sent: name, e-mail, phone, national ID, date of birth, photo. Age is computed in the system and sent as a number. Nationality and age serve the rules only and never reach the language model. The API key is not shown here nor in the browser.')}</div></div>`;
}
S.settingsPatch = {};
async function saveSettings(){
  const p = S.settingsPatch; if (!Object.keys(p).length) { toast(t('لا تغييرات', 'No changes')); return; }
  try { await api('PUT', '/v1/settings', p); S.settingsPatch = {}; toast(t('حُفظت الإعدادات في المحرّك', 'Settings saved in the engine')); render(); } catch (e) { toast(t('رُفض: ', 'Refused: ') + e.message); }
}

/* ---------- audit ---------- */
async function rAudit(){
  const ev = (await get('/v1/audit?limit=200')).events;
  const rows = ev.map(e => `<tr><td>${fd(e.at)}</td><td class="num">${esc(e.ref)}</td><td>${esc(e.action)}</td><td>${esc(e.actor)}</td><td class="payload"><bdi class="mono">${esc(JSON.stringify(e.payload).slice(0, 160))}</bdi></td></tr>`).join('');
  return pageTitle(t('سجل التدقيق', 'Audit log'), `AI Recruitment Audit Log · ${N(ev.length)} ${t('سجل (آخر 200)', 'entries (last 200)')}`) +
  `<div class="card"><div class="tscroll"><table><thead><tr><th>${t('الوقت', 'Time')}</th><th>${t('المرجع', 'Reference')}</th><th>${t('الإجراء', 'Action')}</th><th>${t('المستخدم', 'Actor')}</th><th>${t('التفاصيل', 'Details')}</th></tr></thead><tbody>${rows}</tbody></table></div>
  <div class="note">${t('يُعرض رقم المتقدم فقط؛ لا أسماء ولا هويات في السجل. السجل يُضاف إليه فقط. تغييرات الحالة تكون بيد مستخدم فقط ولا يقوم بها الذكاء.', 'Only the applicant reference is shown; no names or identities in the log. The log is append-only. Status changes are made only by a user, never by the AI.')}</div></div>`;
}

/* ---------- actions ---------- */
async function rescreen(candRef, jobRef){ try { const r = await api('POST', '/v1/screenings', {job_ref:jobRef, candidate_ref:candRef, force:true}); go('processing', {scr:r.screening_id, sel:candRef}); } catch (e) { toast(e.message); } }
document.addEventListener('click', async e => {
  const el = e.target.closest('[data-action]'); if (!el) return; const d = el.dataset; const a = d.action;
  if (a === 'go') go(d.screen);
  else if (a === 'setLang') { S.lang = d.lang; localStorage.setItem('tc_lang', S.lang); render(); }
  else if (a === 'toggleDev') { S.dev = !S.dev; localStorage.setItem('tc_dev', S.dev ? '1' : '0'); render(); }
  else if (a === 'pickJob') { S.job = d.ref; localStorage.setItem('tc_job', S.job); S.edit = null; S.form = null; go(d.screen); }
  else if (a === 'openApp') { S.sel = d.id; S.scr = d.scr || null; go('applicant', {sel:d.id, scr:d.scr || null}); }
  else if (a === 'newJob') { S.edit = newEdit(''); S.draft = null; go('profile'); }
  else if (a === 'addCrit') { S.edit.criteria.push({key:'criterion_' + (S.edit.criteria.length + 1), text:'', weight:0, mandatory:false, question:null, rubric:LEVELS.map(l => ({level:l, text:'', gte:null, gt:null, answers:null}))}); S.edit.dirty = true; render(); }
  else if (a === 'delCrit') { S.edit.criteria.splice(Number(d.i), 1); S.edit.dirty = true; render(); }
  else if (a === 'addRule') { S.edit.rules.push({fact:'height_cm', operator:'>=', value:180, if_missing:'review'}); S.edit.dirty = true; render(); }
  else if (a === 'delRule') { S.edit.rules.splice(Number(d.i), 1); S.edit.dirty = true; render(); }
  else if (a === 'addQ') { S.edit.questions.push({key:'q' + (S.edit.questions.length + 1), label:'', type:'number', options:null, required:true}); S.edit.dirty = true; render(); }
  else if (a === 'delQ') { S.edit.questions.splice(Number(d.i), 1); S.edit.dirty = true; render(); }
  else if (a === 'approveProfile') approveProfile();
  else if (a === 'aiDraft') aiDraft();
  else if (a === 'useDraft') { const dr = S.draft; S.edit.description = dr.description || S.edit.description; S.edit.criteria = dr.criteria.map(c => ({key:c.key, text:c.text, text_en:c.text_en, weight:c.weight, mandatory:!!c.mandatory, question:c.question || null, rubric:(c.rubric || []).map(r => ({level:r.level, text:r.text, gte:r.gte ?? null, gt:r.gt ?? null, answers:r.answers || null}))})); if (dr.questions && dr.questions.length) S.edit.questions = dr.questions.map(q => ({...q})); if (dr.rules && dr.rules.length && !S.edit.rules.length) S.edit.rules = dr.rules.map(r => ({...r})); S.edit.dirty = true; S.draft = null; render(); }
  else if (a === 'discardDraft') { S.draft = null; render(); }
  else if (a === 'submitForm') submitForm();
  else if (a === 'retry') { try { await api('POST', `/v1/screenings/${d.id}/retry`, {}); go('processing', {scr:d.id}); } catch (err) { toast(err.message); } }
  else if (a === 'rescreenOne') rescreen(d.id, d.job);
  else if (a === 'rescreenAll') { try { const r = await api('POST', `/v1/jobs/${encodeURIComponent(S.job)}/rescreen`, {}); toast(t(`أُعيد تقييم ${r.queued.length} متقدم (تُخطّي ${r.skipped.length} محدّث)`, `${r.queued.length} re-scored (${r.skipped.length} already current)`)); go('jobs'); } catch (err) { toast(err.message); } }
  else if (a === 'override') doOverride(d.key, d.text);
  else if (a === 'hilite') { S.hiliteKey = d.key; render(); }
  else if (a === 'exportCsv') exportCsv();
  else if (a === 'saveSettings') saveSettings();
  else if (a === 'closeModal') closeModal();
  else if (a === 'cvPage') { S.cvPage = Number(d.p); render(); }
  else if (a === 'cvSel') { S.cvSel = S.cvSel === d.key ? null : d.key; S.cvLine = null; const k = S.cvSel && document.querySelector('.ocrline.hit'); render(); }
  else if (a === 'cvLine') { const li = Number(d.line); S.cvLine = S.cvLine === li ? null : li; S.cvSel = null; const lay = document.querySelector('.pageview'); render(); }
  else if (a === 'tryRun') tryRun();
  else if (d.setting === 'ai_provider') { S.settingsPatch.ai_provider = d.val; S.settings.ai_provider = d.val; document.querySelectorAll('[data-setting="ai_provider"]').forEach(b => b.classList.toggle('on', b.dataset.val === d.val)); }
});
document.addEventListener('change', e => {
  const el = e.target; const d = el.dataset;
  if (d.crit != null) { const c = S.edit.criteria[Number(d.crit)]; if (d.rub != null) { const r = c.rubric[Number(d.rub)]; if (d.f === 'text') r.text = el.value; else { const q = S.edit.questions.find(x => x.key === c.question); Object.assign(r, parseHints(el.value, q ? q.type : 'select')); } } else if (d.f === 'mandatory') c.mandatory = el.checked; else if (d.f === 'weight') c.weight = Number(el.value) || 0; else c[d.f] = el.value || null; S.edit.dirty = true; render(); }
  else if (d.rule != null) { S.edit.rules[Number(d.rule)][d.f] = el.value; S.edit.dirty = true; render(); }
  else if (d.q != null) { const q = S.edit.questions[Number(d.q)]; if (d.f === 'required') q.required = el.checked; else if (d.f === 'options') q.options = el.value.split('|').map(x => x.trim()).filter(Boolean); else q[d.f] = el.value; S.edit.dirty = true; render(); }
  else if (d.edit) { S.edit[d.edit] = el.value; S.edit.dirty = true; if (S.dev) renderDev(); }
  else if (d.filter) { if (d.filter === 'sort') S.listSort = el.value; else S.listFilters[d.filter] = el.value; render(); }
  else if (d.form) { if (d.form === 'cv') S.form.cv = el.files[0] || null; else S.form[d.form] = el.type === 'checkbox' ? el.checked : el.value; }
  else if (d.ans) S.form.answers[d.ans] = el.value;
  else if (d.ansMulti) { const cur = Array.isArray(S.form.answers[d.ansMulti]) ? S.form.answers[d.ansMulti].slice() : []; if (el.checked) { if (!cur.includes(el.value)) cur.push(el.value); } else { const i = cur.indexOf(el.value); if (i >= 0) cur.splice(i, 1); } S.form.answers[d.ansMulti] = cur; }
  else if (d.setting) { const v = el.type === 'number' ? Number(el.value) : el.value; if (d.setting === 'callback_secret' && !v) return; S.settingsPatch[d.setting] = v; }
  else if (d.fact) { const cur = new Set(S.settingsPatch.allowed_facts || S.settings.allowed_facts); if (el.checked) cur.add(d.fact); else cur.delete(d.fact); S.settingsPatch.allowed_facts = [...cur]; }
  else if (d.action === 'pickJobProfile' || d.action === 'pickJobApply' || d.action === 'pickJobList' || d.action === 'pickJobRanking') { S.job = el.value; localStorage.setItem('tc_job', S.job); S.edit = null; S.form = null; render(); }
});
document.addEventListener('input', e => { const d = e.target.dataset; if (d.filter === 'q') { S.listFilters.q = e.target.value; } });
document.getElementById('overlay').addEventListener('click', e => { if (e.target.id === 'overlay') closeModal(); });

(async () => { try { const me = await get('/console/me'); S.user = me.user; S.tenant = me.tenant; } catch (e) { return; } render(); })();
