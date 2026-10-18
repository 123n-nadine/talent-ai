"""Provider for any OpenAI-compatible chat endpoint: vLLM (local) or a cloud API (cloud).

Structured output through `response_format=json_schema` (guided decoding on vLLM). Temperature 0.
Invalid JSON -> one repair attempt -> LLMOutputError. Thinking mode is switched off for Qwen3.

Output budget (round 7): every call may use what the model's context leaves after the prompt
(`max_model_len`, bounded by a per-task cap), and an answer cut off by that budget
(`finish_reason == "length"`) is retried once with a shorter prompt — a trimmed CV text and a
request for a compact answer — instead of the same request again (GOLD-SEC-015 failed three times
on an unclosed profile JSON)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.llm import prompts
from app.llm.base import DraftCriteria, JudgeRequest, LLMOutputError
from app.llm.draft import normalise_draft
from app.llm.schemas import CandidateProfile, CriterionJudgement, DraftOutput, JudgeOutput

log = logging.getLogger(__name__)
MAX_CV_CHARS = 12000
COMPACT_NOTE = (
    "\n\nThe previous answer was cut off before the JSON closed. Return a compact answer: at most 6 "
    "items per list, every quote at most 120 characters, the summary one sentence, no repetition."
)


class OpenAICompatLLM:
    prompt_version = prompts.JUDGE

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 120.0,
        max_retries: int = 2,
        disable_thinking: bool = True,
        http_client: Any = None,  # httpx2.Client (openai>=3) with a mock transport in tests
        judge_prompt: str = prompts.JUDGE,
        max_model_len: int = 8192,  # the served model's context (prompt + answer)
    ):
        self.name = name
        self.max_model_len = max_model_len
        self.prompt_version = judge_prompt
        self.model = model
        self.base_url = base_url
        self.disable_thinking = disable_thinking
        self.max_retries = max_retries
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or "EMPTY",
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.last_usage: dict[str, Any] = {}
        self.last_finish_reason: str | None = None

    # ---- transport -------------------------------------------------------------------------
    def ready(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("LLM provider %s not ready: %s", self.name, e)
            return False

    # per-task caps (Nadine, round 8: 2500 — ten times a normal profile answer; a runaway answer
    # then costs ~40 s instead of ~100 s before the shorter retry)
    MAX_TOKENS = {"candidate_profile": 2500, "judgement": 2500, "draft": 3000}
    MIN_TOKENS = 256

    def output_budget(self, name: str, *texts: str) -> int:
        """Tokens the answer may use: the context minus a conservative estimate of the prompt
        (Arabic runs at about one token per two characters), never above the task's cap."""
        prompt_est = sum(len(t) for t in texts) // 2 + 200  # messages framing and schema
        room = self.max_model_len - prompt_est - 64
        return max(self.MIN_TOKENS, min(self.MAX_TOKENS.get(name, 1500), room))

    def _complete(self, system: str, user: str, schema: type[BaseModel], name: str) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": self.output_budget(name, system, user),  # bounds runaway generations
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": name, "schema": strict_schema(schema)},
            },
        }
        if self.disable_thinking:
            kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        t0 = time.time()
        resp = self.client.chat.completions.create(**kwargs)
        usage = getattr(resp, "usage", None)
        self.last_finish_reason = getattr(resp.choices[0], "finish_reason", None)
        self.last_usage = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "max_tokens": kwargs["max_tokens"],
            "finish_reason": self.last_finish_reason,
            "seconds": round(time.time() - t0, 2),
        }
        content = resp.choices[0].message.content or ""
        return content

    def _structured(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        name: str,
        shorter: Any = None,  # callable(user) -> a shorter user message for a cut-off answer
    ) -> BaseModel:
        raw = self._complete(system, user, schema, name)
        if self.last_finish_reason == "length" and shorter is not None:
            # the answer hit the output budget: a repair of the unclosed JSON would be asked to
            # finish what did not fit, so the request itself is made smaller instead
            log.warning(
                "%s answer from %s cut off at the output budget, retrying shorter", name, self.name
            )
            raw = self._complete(system, shorter(user), schema, name)
            self.last_usage["retried_shorter"] = True
        try:
            return schema.model_validate_json(_strip_fences(raw))
        except (ValidationError, ValueError) as first:
            log.warning(
                "invalid %s JSON from %s, asking for a repair: %s",
                name,
                self.name,
                str(first)[:200],
            )
            repair_user = (
                "The JSON below does not match the schema. Return the corrected JSON only.\n\n"
                f"Schema:\n{json.dumps(strict_schema(schema), ensure_ascii=False)}\n\n"
                f"Validation error:\n{str(first)[:800]}\n\nJSON:\n{raw[:6000]}"
            )
            raw2 = self._complete(system, repair_user, schema, name)
            try:
                return schema.model_validate_json(_strip_fences(raw2))
            except (ValidationError, ValueError) as second:
                raise LLMOutputError(
                    f"{name}: invalid JSON after repair: {str(second)[:300]}"
                ) from second

    # ---- tasks -----------------------------------------------------------------------------
    def profile(self, redacted_text: str) -> CandidateProfile:
        user = "CV text (redacted):\n\n" + redacted_text[:MAX_CV_CHARS]
        out = self._structured(
            prompts.load(prompts.PROFILE),
            user,
            CandidateProfile,
            "candidate_profile",
            shorter=lambda _u: (
                "CV text (redacted):\n\n" + shorten(redacted_text, MAX_CV_CHARS // 2) + COMPACT_NOTE
            ),
        )
        assert isinstance(out, CandidateProfile)
        return out

    def judge(self, req: JudgeRequest) -> list[CriterionJudgement]:
        blocks = []
        for c in req.criteria:
            q = req.questions.get(c.get("question") or "")
            ans = req.answers.get(c.get("question") or "")
            answer_txt = ans.canonical if (ans and ans.answered) else "not answered"
            if c["key"] in req.code_levels:
                answer_txt += f" (level {req.code_levels[c['key']]} already computed by the system from this answer; judge only the CV side)"
            rubric = "\n".join(
                f"  level {r['level']}: {r['text']}"
                for r in sorted(c["rubric"], key=lambda r: r["level"])
            )
            blocks.append(
                f"criterion key: {c['key']}\ntext: {c['text']}\nmandatory: {c.get('mandatory', False)}\n"
                f"question key: {c.get('question')}\nquestion: {q['label'] if q else '-'}\n"
                f"stored answer: {answer_txt}\nrubric:\n{rubric}"
            )
        derived = json.dumps(req.derived, ensure_ascii=False) if req.derived else "{}"
        user = (
            "Criteria:\n\n"
            + "\n\n".join(blocks)
            + f"\n\nFacts derived in code from the CV: {derived}\n\n"
            + (
                "Redacted CV text:\n" + req.redacted_text[:MAX_CV_CHARS]
                if req.redacted_text
                else "No CV was provided."
            )
        )
        out = self._structured(
            prompts.load(self.prompt_version),
            user,
            JudgeOutput,
            "judgement",
            shorter=lambda u: (
                (
                    u.replace(
                        req.redacted_text[:MAX_CV_CHARS],
                        shorten(req.redacted_text, MAX_CV_CHARS // 2),
                    )
                    if req.redacted_text
                    else u
                )
                + COMPACT_NOTE
            ),
        )
        assert isinstance(out, JudgeOutput)
        return out.criteria

    def draft_criteria(self, title: str, description: str) -> DraftCriteria:
        user = f"Job title: {title}\nExisting description (may be empty): {description}"
        out = self._structured(prompts.load(prompts.DRAFT), user, DraftOutput, "draft")
        assert isinstance(out, DraftOutput)
        return normalise_draft(out)  # keys, question links, rubric levels and weights fixed in code


MAX_LIST_ITEMS = 12  # a CV never needs more; the 8B model otherwise loops on one item (round 8)


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic schema with every property required and no extra keys, so guided decoding cannot
    drop the lists (an 8B model otherwise answers with the summary only), and every list of
    objects bounded by `maxItems` so a repeating model is stopped by the grammar instead of by the
    output budget (the three cut-off profiles of round 7 repeated one language item 70–94 times).
    The result model itself is unchanged: the bound lives only in the schema sent to the model."""
    schema = model.model_json_schema()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            if node.get("type") == "array" and "maxItems" not in node:
                node["maxItems"] = MAX_LIST_ITEMS
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)
    return schema


def shorten(text: str, limit: int) -> str:
    """The first `limit` characters of a text, cut at a line break so no sentence is split."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    return head[: head.rfind("\n")] if "\n" in head[limit // 2 :] else head


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()
