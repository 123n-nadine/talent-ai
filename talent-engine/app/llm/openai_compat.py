"""Provider for any OpenAI-compatible chat endpoint: vLLM (local) or a cloud API (cloud).

Structured output through `response_format=json_schema` (guided decoding on vLLM). Temperature 0.
Invalid JSON -> one repair attempt -> LLMOutputError. Thinking mode is switched off for Qwen3."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.llm import prompts
from app.llm.base import DraftCriteria, JudgeRequest, LLMOutputError
from app.llm.schemas import CandidateProfile, CriterionJudgement, DraftOutput, JudgeOutput

log = logging.getLogger(__name__)
MAX_CV_CHARS = 12000


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
    ):
        self.name = name
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

    # ---- transport -------------------------------------------------------------------------
    def ready(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("LLM provider %s not ready: %s", self.name, e)
            return False

    MAX_TOKENS = {"candidate_profile": 1500, "judgement": 1500, "draft": 3000}

    def _complete(self, system: str, user: str, schema: type[BaseModel], name: str) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": self.MAX_TOKENS.get(name, 1500),  # bounds runaway generations
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
        self.last_usage = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "seconds": round(time.time() - t0, 2),
        }
        content = resp.choices[0].message.content or ""
        return content

    def _structured(self, system: str, user: str, schema: type[BaseModel], name: str) -> BaseModel:
        raw = self._complete(system, user, schema, name)
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
            prompts.load(prompts.PROFILE), user, CandidateProfile, "candidate_profile"
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
        out = self._structured(prompts.load(self.prompt_version), user, JudgeOutput, "judgement")
        assert isinstance(out, JudgeOutput)
        return out.criteria

    def draft_criteria(self, title: str, description: str) -> DraftCriteria:
        user = f"Job title: {title}\nExisting description (may be empty): {description}"
        out = self._structured(prompts.load(prompts.DRAFT), user, DraftOutput, "draft")
        assert isinstance(out, DraftOutput)
        total = sum(c.weight for c in out.criteria) or 1.0
        criteria = []
        for c in out.criteria:
            d = c.model_dump()
            d["weight"] = round(
                c.weight * 100 / total, 1
            )  # the draft must total 100, HR edits it anyway
            criteria.append(d)
        diff = round(100 - sum(c["weight"] for c in criteria), 1)
        if criteria and diff:
            criteria[0]["weight"] = round(criteria[0]["weight"] + diff, 1)
        return DraftCriteria(
            description=out.description,
            criteria=criteria,
            questions=[q.model_dump() for q in out.questions],
            rules=[],
        )


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic schema with every property required and no extra keys, so guided decoding cannot
    drop the lists (an 8B model otherwise answers with the summary only)."""
    schema = model.model_json_schema()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)
    return schema


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()
