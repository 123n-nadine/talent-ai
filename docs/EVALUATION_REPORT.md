# Evaluation report (phase 4) — 2026-10-15

Server: Quadro RTX 6000 (Turing, shared), vLLM cap `--gpu-memory-utilization 0.40`, Triton attention backend (no FlashAttention on Turing).
Gold set: 50 synthetic applicants (`talent-engine/eval/gold/`: 35 «مشرف أمن», 15 «محلل بيانات»), expected levels per criterion from the approved rubric, expected eligibility and flags. All data fictional.
Judgement design since this phase: structured form answers (numbers, selects) are judged **in code** from the rubric; the LLM judges only free-text answers and the CV side (confirm / contradict / add evidence). Applicants without a CV and without free-text criteria never call the model.

## 1. Model and prompt comparison (gold set, 50 applicants, judge prompt `judge-v1` = English, `judge-v2` = Arabic)

| run | model | prompt | level exact | level ±1 step | levels>0 with evidence | eligibility | expected flags found | free-text criterion exact | supervision exact | pipeline time / applicant |
|---|---|---|---|---|---|---|---|---|---|---|
| 8B v1 | `qwen3-8b-awq` | `judge-v1` | 98% | 100.0% | 100% | 100% | 100% | 77% | 91% | 11.49 s |
| 8B v2 | `qwen3-8b-awq` | `judge-v2` | 97% | 97.7% | 100% | 100% | 73% | 62% | 91% | 12.25 s |
| 4B v1 | `qwen3-4b-awq` | `judge-v1` | 96% | 96.1% | 100% | 100% | 73% | 31% | 91% | 12.05 s |

- Rerun of 8B v1 (same inputs twice): identical levels for **100%** of applicants. Name-swap (same CVs, different name hint): identical for **100%**.
- The remaining inexact cases of 8B v1 are the free-text «وصف مشروع» criterion (the only one judged from a free answer: 77% exact, 100% within one step) and the 3 contradiction cases of «خبرة الإشراف» (expected 50 from a CV that states two years; the model's CV level lands one step away but the contradiction flag is always raised).
- **Decision: Qwen3-8B-AWQ with `judge-v1`.** `judge-v2` (Arabic instructions) is worse on free text and misses contradiction flags; Qwen3-4B-AWQ misses most free-text levels (31%) and flags. Qwen3-14B-AWQ (10 GB of weights) does not fit under the 0.40 cap (9.4 GB); it would need ~0.60 and was not downloaded.
- Not answered by this gold set: Arabic-model alternatives (ALLaM, Command R7B Arabic) have no official AWQ weights that fit the cap; revisit if the free-text criterion matters more to the client.

## 2. Throughput (100 applicants, 54 with a CV, Qwen3-8B-AWQ, judge-v1)

| workers | wall time for 100 | applicants / min | projected 1000 | GPU used (max) | failures |
|---|---|---|---|---|---|
| 2 | 13.4 min | 7.5 | 134 min | 9484 MiB | 0 |
| 4 | 7.8 min | 12.8 | 78 min | 9484 MiB | 0 |
| 8 | 5.4 min | 18.4 | 54 min | 9484 MiB | 0 |

- GPU memory never exceeded the cap: vLLM holds ~8.7–9.0 GB regardless of concurrency (the KV cache is pre-allocated inside the 0.40 share).
- Per-applicant pipeline time rises with concurrency (13.9 s → 18.1 s → 28.0 s) because the GPU is shared between requests; total throughput still improves. 8 workers ≈ **1000 applicants in about 55 minutes**; 4 workers ≈ 78 minutes. The default is 4 workers (`make up`, `WORKERS=8 make up` for peaks).
- Applicants without a CV cost ~0.1 s (no model call). A 1000-applicant job where only half attach a CV would take roughly half the times above.
- The RQ per-job overhead noted in phase 1 (~1.5 s) is now minor next to the LLM time; keep as is.

## 3. Why applicant 2001 scored 92.5 in phase 3 and 100 now

His supervision answer is 7 years. The rubric says level 100 = «أكثر من 5»; the 8B model judged it 75 («3–5 سنوات») when it had to read the rubric itself. Since this phase the level of a structured answer comes from the rubric thresholds in code, so the answer 7 → 100 and the model only confirms it from the CV. The demo ranking after this change is identical to the phase-1 deterministic ranking (`eval/reports/ranking_before_code_levels.json` vs `ranking_after_code_levels.json`).

## 4. Thresholds and settings adopted

- `OCR_MIN_CONFIDENCE` stays 0.80 (the synthetic scans score 0.91; no real scans yet to calibrate against).
- Quote verification: fuzzy ratio ≥ 0.9 after Arabic normalisation; 100% of levels > 0 carried verified evidence in every run.
- Tenant settings: `ai_provider=local`, `ai_model=qwen3-8b-awq`, `judge_prompt=judge-v1`.

Raw reports: `talent-engine/eval/reports/` (git-ignored, dated JSON + Markdown).
