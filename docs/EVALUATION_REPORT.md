# Evaluation report (phase 4) — 2026-10-15

Server: Quadro RTX 6000 (Turing, shared), vLLM cap `--gpu-memory-utilization 0.40`, Triton attention backend (no FlashAttention on Turing).
Gold set: 55 synthetic applicants since round 6 (`talent-engine/eval/gold/`: 40 «مشرف أمن», 15 «محلل بيانات»; 50 in phase 4), expected eligibility and flags, and an **expected level per criterion that is computed by `eval/make_gold.py` from the rubric table itself — not a human judgement**: a numeric answer through the engine's own `level_from_rubric`, a select answer by its fixed position, the languages answer by the demo rule, and each free-text answer written for one rubric level (five texts in all). «Exact level» below therefore means «the pipeline reproduced the rubric table»; human labelling of real applications is OPEN_QUESTIONS #13. All data fictional.
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
- What the batch was made of (`eval/bench.py`, raw reports in `talent-engine/eval/reports/*-bench-*.json`): the 50 gold applicants cycled twice; 46 applicants without a CV and 54 with a text PDF (the gold CV lines rendered through Word → LibreOffice, i.e. the same kind of Arabic text PDF the demo uses); no scanned image, so no OCR time is in these figures. The per-applicant pipeline mean is over all 100 (the no-CV ones cost ~1 s). The arithmetic behind the wall time: 100 × 28.0 s ÷ 8 workers = 350 s against 325 s measured from the last submission to the last result (402 s from the first submission); ×10 gives the 54 min projection.
- Applicants without a CV cost ~1 s (no model call). A 1000-applicant job where only half attach a CV would take roughly half the times above.
- The RQ per-job overhead noted in phase 1 (~1.5 s) is now minor next to the LLM time; keep as is.

## 3. Why applicant 2001 scored 92.5 in phase 3 and 100 now

His supervision answer is 7 years. The rubric says level 100 = «أكثر من 5»; the 8B model judged it 75 («3–5 سنوات») when it had to read the rubric itself. Since this phase the level of a structured answer comes from the rubric thresholds in code, so the answer 7 → 100 and the model only confirms it from the CV. The demo ranking after this change is identical to the phase-1 deterministic ranking (`eval/reports/ranking_before_code_levels.json` vs `ranking_after_code_levels.json`).

## 4. Thresholds and settings adopted

- `OCR_MIN_CONFIDENCE` stays 0.80 (the synthetic scans score 0.91; no real scans yet to calibrate against).
- Quote verification: fuzzy ratio ≥ 0.9 after Arabic normalisation; 100% of levels > 0 carried verified evidence in every run.
- Tenant settings: `ai_provider=local`, `ai_model=qwen3-8b-awq`, `judge_prompt=judge-v1`.

Raw reports: `talent-engine/eval/reports/` (git-ignored, dated JSON + Markdown).

## 5. Round 6 rerun (2026-10-18, 55 applicants, `judge-v1`, Qwen3-8B-AWQ)

After Nadine's review of the gold set: supervision years never exceed security years any more (6 applicants corrected: GOLD-SEC-002, 011, 012, 020, 026, 035; whether the engine should flag such answers is OPEN_QUESTIONS #22), the gold job's age rule is 21 as on the demo form, and five eligibility edge cases were added (GOLD-SEC-036…040: non-Saudi → not eligible, age 20 → not eligible, age exactly 21 → eligible, height blank → needs review, age blank → needs review). Same format as §1; raw report `eval/reports/2026-10-18_1305-8b-v1-r6.*`.

| run | model | prompt | level exact | level ±1 step | levels>0 with evidence | eligibility | expected flags found | free-text criterion exact | supervision exact | pipeline time / applicant |
|---|---|---|---|---|---|---|---|---|---|---|
| 8B v1 r6 | `qwen3-8b-awq` | `judge-v1` | 98.5% | 100.0% | 100% | 100% | 100% | 62% | 100% | 21.58 s |

The result in two parts (as asked in round 6):

| part | what it measures | exact | within one step | judgements |
|---|---|---|---|---|
| levelled in code from the rubric table | numeric, select and multi-select answers through the thresholds in code | 100% | 100% | 305 |
| judged by the model | the free-text «وصف مشروع» (13 judgements) and the CV side of the 3 contradiction cases (the expected level comes from the CV) | 69% | 100% | 16 |

- **Distinct texts the model was measured on: 5 free-text answers** (one written per rubric level, repeated across the 15 analyst applicants) **and 31 CV documents** (one per applicant with a CV, built from the same sentence templates). The free-text figure (8 of 13 exact, all within one step) rests on five texts only and says little about real free answers; the 5 edge cases and the 6 corrected applicants were all levelled and classified as expected (eligibility 100%).
- Rerun (same 55 inputs twice): identical levels for **98%** of applicants (54 of 55; the one difference is GOLD-SEC-023, whose second pass failed and has no levels — see below). Name-swap (same CVs, different name hint): identical for **100%**.
- **Failures: 1 applicant of 55 in both passes (GOLD-SEC-015), and GOLD-SEC-023 in the second pass only**, each after the 3 attempts, with `LLMOutputError: candidate_profile: invalid JSON after repair … EOF while parsing` — the model's profile extraction of the CV was cut off before the JSON closed (output length limit of the profile call), the repair could not close it, and the screening ended «Failed» as decision 14 prescribes for engine errors. GOLD-SEC-023 passed in the first pass and in the name-swap pass, so the cut-off is not deterministic. Fixed in round 7 (§6): the output budget follows the context and a cut-off answer is retried with a shorter prompt.
- Mean pipeline time per applicant 21.6 s (11.5 s in phase 4 on this set): the engine now indexes every applicant for the talent pool and runs the leak guard; measured with 4 workers while the demo stack was idle.

## 6. Round 7 rerun (2026-10-18, 55 applicants, after the output-budget fix)

Fix (`app/llm/openai_compat.py`): the answer budget of every model call is what the served model's context (`LLM_MAX_MODEL_LEN` = `VLLM_MAX_MODEL_LEN`, 8192) leaves after the prompt, bounded by a per-task cap of 4000 tokens (the old limit was a fixed 1500); an answer cut off at that budget (`finish_reason == "length"`) is retried once with the CV text trimmed to half and a request for a compact answer, instead of the same request again. Permanent tests: GOLD-SEC-015's own CV through a mocked endpoint whose first answer is cut off (`test_cut_off_profile_is_retried_shorter_not_repaired`), the budget arithmetic, the line-safe trimming. Raw report `eval/reports/2026-10-18_1439-8b-v1-r7.*` (two passes + name-swap).

| run | model | prompt | level exact | level ±1 step | levels>0 with evidence | eligibility | expected flags found | free-text criterion exact | supervision exact | pipeline time / applicant |
|---|---|---|---|---|---|---|---|---|---|---|
| 8B v1 r7 | `qwen3-8b-awq` | `judge-v1` | 98.2% | 99.7% | 100% | 100% | 100% | 62% | 100% | 29.82 s |

- **Failures: 0 of 55 in both passes and in the name-swap pass** (round 6: 1 and 2). GOLD-SEC-015, GOLD-SEC-023 and GOLD-SEC-009 each hit the budget on the first profile call and completed on the shorter retry (`llm_calls[].retried_shorter`), with normal-sized answers (328–504 tokens).
- Rerun (same 55 inputs twice): identical levels for **100%** of applicants (round 6: 98%). Name-swap (same CVs, different name hint): identical for **100%**.

| part | what it measures | exact | within one step | judgements |
|---|---|---|---|---|
| levelled in code from the rubric table | numeric, select and multi-select answers through the thresholds in code, when the model did not override them from the CV | 100% | 100% | 311 |
| judged by the model | the free-text «وصف مشروع» (13), the CV side of the 3 contradiction cases, and one level the model took from the CV (GOLD-SEC-021) | 65% | 94% | 17 |

- The one new model miss: GOLD-SEC-021 answered «منتهية أو قيد الإصدار» for the licence (rubric level 50) and the CV says «رخصة حارس الأمن منتهية وقيد التجديد»; the model read the CV as no valid licence (level 0), raised a contradiction and the lower CV-backed level was used, so the application went to «يحتاج مراجعة» with the contradiction and `mandatory_zero` flags — a stricter reading than the rubric text, visible to HR with its evidence. The same in all three passes. The raw report file still counts this judgement in the code part (99.7% of 312 / 68.8% of 16): `eval/run.py` now classifies a level taken from the CV as the model's judgement, which gives the table above; the next run reports it directly.
- Distinct texts the model was measured on: unchanged — 5 free-text answers and 31 CV documents.
- **Time**: mean pipeline time per applicant 29.8 s (round 6: 21.6 s), median 26.4 s, max 249.7 s; wall time for the 55 applicants 491 s (round 6: 431 s), 4 workers. The three retried applicants took ~140 s each: the first profile call ran to the 4000-token budget before the model stopped (~100 s at this GPU's ~40 tokens/s), then the shorter retry answered in 7–12 s; the other applicants average 23.4 s, and the 249 s maximum is an applicant that queued behind those long generations. So the fix trades a «Failed» for about two extra minutes on the rare runaway answer; a lower cap (for example 2500) would halve that cost and still leave ten times the size of a normal profile answer — to decide with Nadine.
