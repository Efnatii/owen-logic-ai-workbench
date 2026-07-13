#!/usr/bin/env python3
"""Audit a native all-tools OWEN Logic run against the 170 personal contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from owen_logic_output import OWEN_OUTPUT_SPECS


def normalized(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).replace("\\", "/")).strip().lower()


def leaves(value: object, current: str = "") -> list[tuple[str, object]]:
    output: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            output.extend(leaves(item, f"{current}.{key}" if current else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            output.extend(leaves(item, f"{current}[{index}]"))
    else:
        output.append((current, value))
    return output


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_owen_output_runtime.py <all_tool_calls.jsonl>")
    source = Path(sys.argv[1]).resolve()
    records = [item for item in (json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()) if item.get("server") == "owen_logic"]
    expected = sorted(OWEN_OUTPUT_SPECS)
    actual = sorted(str(item["tool"]) for item in records)
    if actual != expected:
        raise AssertionError("native runtime records do not cover every OWEN tool exactly once")
    audits: list[dict[str, object]] = []
    for item in records:
        name = str(item["tool"])
        visible = normalized(item.get("visible_output") or "")
        raw = item.get("raw_result")
        if item.get("contract_version") != "workbench-personal-v5":
            raise AssertionError(f"{name}: personal contract missing")
        if item.get("output_contract_tool") != name:
            raise AssertionError(f"{name}: wrong personal contract identity")
        if not item.get("structured_content_present"):
            raise AssertionError(f"{name}: structuredContent missing")
        structured = item.get("structured_content")
        if not isinstance(structured, dict) or "summary" not in structured or "raw_result" not in structured:
            raise AssertionError(f"{name}: minimal structured result missing summary/raw_result")
        if set(structured) - {"summary", "problem", "next_action", "raw_result"}:
            raise AssertionError(f"{name}: service fields leaked into structuredContent")
        if structured["raw_result"] != raw or item.get("model_raw_result") != raw:
            raise AssertionError(f"{name}: model-visible raw_result is not lossless")
        if raw is None:
            raise AssertionError(f"{name}: raw_result missing")
        if "[circular]" in json.dumps(raw, ensure_ascii=False):
            raise AssertionError(f"{name}: raw data was destroyed as [circular]")
        for noise in ("action:", "input:", "result:", "evidence:"):
            if re.search(rf"(?m)^{re.escape(noise)}", visible):
                raise AssertionError(f"{name}: generic visible noise {noise}")
        if "result fields" in visible:
            raise AssertionError(f"{name}: generic visible noise result fields")
        if re.search(r"(?m)^\s{2,}[a-z][a-z0-9_]*:\s*", str(item.get("visible_output") or "")):
            raise AssertionError(f"{name}: recursive JSON/YAML-like field dump remains visible")
        if re.search(r"_meta\.raw_result|evidence_boundary|raw_evidence|доступ ии", visible, re.I):
            raise AssertionError(f"{name}: service guidance leaked into visible output")
        spec = OWEN_OUTPUT_SPECS[name]
        for marker in (spec["title"],):
            if normalized(marker) not in visible:
                raise AssertionError(f"{name}: missing personal marker {marker}")
        audits.append({
            "tool": name,
            "family": spec["family"],
            "category": item.get("category"),
            "visible_chars": len(str(item.get("visible_output") or "")),
            "raw_top_keys": len(raw) if isinstance(raw, dict) else len(raw) if isinstance(raw, list) else 1,
            "structured_result_fields": len(structured),
        })
    result = {
        "status": "PASS",
        "jsonl": str(source),
        "tools_audited": len(audits),
        "personal_contracts": len(OWEN_OUTPUT_SPECS),
        "families": {family: sum(1 for item in audits if item["family"] == family) for family in sorted({str(item["family"]) for item in audits})},
        "generic_fallback_hits": 0,
        "circular_data_losses": 0,
        "lossless_model_raw_results": len(audits),
        "minimal_structured_results": len(audits),
        "visible_chars": {"min": min(item["visible_chars"] for item in audits), "max": max(item["visible_chars"] for item in audits), "total": sum(item["visible_chars"] for item in audits)},
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
