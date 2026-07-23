"""Build compact, evidence-constrained context for copilot follow-ups."""

from __future__ import annotations

import json
from typing import Any

from app.cache import build_cache_key, get_cache, stable_hash
from app.config import settings
from app.database import (
    get_analysis_evidence_chain,
    get_copilot_report_source_turn,
    list_recent_copilot_messages,
)


CONTEXT_TTL_SECONDS = 24 * 60 * 60
MAX_EVIDENCE_SNIPPET = 700
MAX_REQUIREMENTS = 20


def _parse_json(value: str | None) -> dict:
    try:
        parsed = json.loads(value or "")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _short(value: Any, limit: int = MAX_EVIDENCE_SNIPPET) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit] + ("..." if len(text) > limit else "")


def _build_snapshot(report: dict, evidence_chain: dict | None) -> dict:
    analysis = _parse_json(report.get("parsed_result"))
    items = []
    for item in (evidence_chain or {}).get("items", [])[:MAX_REQUIREMENTS]:
        requirement = item.get("requirement") or {}
        decision = item.get("decision") or {}
        candidate_by_id = {
            candidate.get("id"): candidate
            for candidate in item.get("candidates", [])
            if isinstance(candidate, dict)
        }
        evidence = [
            _short(candidate_by_id[evidence_id].get("snippet"))
            for evidence_id in decision.get("evidence_ids", [])
            if evidence_id in candidate_by_id
        ][:3]
        review = item.get("review") or {}
        items.append(
            {
                "requirement": {
                    "id": requirement.get("id"),
                    "skill": requirement.get("skill"),
                    "category": requirement.get("category"),
                    "source_quote": _short(requirement.get("source_quote"), 500),
                },
                "decision": {
                    "status": decision.get("status", "missing_evidence"),
                    "confidence": decision.get("confidence"),
                    "rationale": _short(decision.get("rationale"), 300),
                    "evidence": evidence,
                },
                "review": {
                    "verdict": review.get("verdict"),
                    "corrected_status": review.get("corrected_status"),
                    "note": _short(review.get("note"), 300),
                },
            }
        )
    return {
        "report_id": report.get("id"),
        "resume_version_id": report.get("resume_version_id"),
        "target_role": report.get("target_role") or "目标岗位",
        "analysis": {
            "score": analysis.get("score", report.get("score")),
            "summary": _short(analysis.get("summary"), 1200),
            "matched_skills": analysis.get("matched_skills", [])[:30],
            "missing_skills": analysis.get("missing_skills", [])[:30],
            "risk_points": analysis.get("risk_points", [])[:10],
            "action_plan": analysis.get("action_plan", [])[:10],
            "resume_bullets": analysis.get("resume_bullets", [])[:10],
        },
        "evidence_chain": {
            "pipeline_version": (evidence_chain or {}).get("pipeline_version"),
            "items": items,
        },
    }


def _pointer_key(report_id: int) -> str:
    return build_cache_key("copilot:context_pointer", {"report_id": report_id})


def invalidate_report_context(report_id: int | None) -> None:
    if report_id is None or not settings.cache_enabled:
        return
    get_cache().delete(_pointer_key(int(report_id)))


def get_copilot_context(report: dict, session_id: int) -> dict:
    """Return a compact report snapshot plus a tiny recent message window."""
    report_id = int(report["id"])
    cache = get_cache()
    pointer = cache.get_json(_pointer_key(report_id)) if settings.cache_enabled else None
    snapshot = None
    revision = None
    if isinstance(pointer, dict) and pointer.get("revision"):
        revision = str(pointer["revision"])
        snapshot_key = build_cache_key(
            "copilot:context", {"report_id": report_id, "revision": revision}
        )
        snapshot = cache.get_json(snapshot_key)

    if not isinstance(snapshot, dict):
        source_turn_id = get_copilot_report_source_turn(report_id)
        evidence_chain = (
            get_analysis_evidence_chain(source_turn_id)
            if source_turn_id is not None
            else None
        )
        snapshot = _build_snapshot(report, evidence_chain)
        revision = stable_hash(snapshot)[:24]
        if settings.cache_enabled:
            snapshot_key = build_cache_key(
                "copilot:context", {"report_id": report_id, "revision": revision}
            )
            cache.set_json(snapshot_key, snapshot, CONTEXT_TTL_SECONDS)
            cache.set_json(_pointer_key(report_id), {"revision": revision}, CONTEXT_TTL_SECONDS)

    messages = [
        {
            "role": item.get("role"),
            "content": _short(item.get("content"), 500),
        }
        for item in list_recent_copilot_messages(session_id, limit=4)
    ]
    return {"snapshot": snapshot, "revision": revision or stable_hash(snapshot)[:24], "messages": messages}
