#!/usr/bin/env python3
"""Materialize one explicit visible-output contract for every OWEN Logic MCP tool."""

from __future__ import annotations

import json
import re
from pathlib import Path

import owen_logic_server as srv


def family(name: str) -> str:
    rules = (
        (r"compatibility|device_(connect|download|ports|read_info)|cloud_|owencloud_|extension_action|guard_confirm", "compatibility_alias"),
        (r"gui|ui_|screenshot|menu_snapshot|focus_window|send_hotkey|launch", "gui_observation"),
        (r"live_device|simulator|smoke_test", "runtime_probe"),
        (r"modbus_(crc|request_build|frame_parse|response_build|transaction_validate|tcp_loopback)", "protocol_transaction"),
        (r"coverage_audit|parity_audit|diagnostics_audit|format_audit|installation_audit|target_coverage", "coverage_audit"),
        (r"validate|lint|preflight|guardrail_policy|capability_status|surface_probe", "decision_gate"),
        (r"catalog|index|reference|list_|snapshot|find_installation|file_analysis", "catalog_or_inventory"),
        (r"inspect|summary|query|extract|analysis", "project_inspection"),
        (r"export|to_codex_package", "artifact_export"),
        (r"import|from_codex_package", "artifact_import"),
        (r"create|insert|clone|new_project", "project_create"),
        (r"patch|set|bind|edit", "project_change"),
        (r"delete", "project_delete"),
        (r"open|lifecycle", "project_lifecycle"),
        (r"manual_|shortcut|examples|extensions", "guided_procedure"),
    )
    return next((value for pattern, value in rules if re.search(pattern, name)), "domain_operation")


NEXT_BY_FAMILY = {
    "compatibility_alias": "Use the named target tool when real execution is required; this alias must state whether it delegated or only described policy.",
    "gui_observation": "Confirm the reported window, screenshot, controls, and stop condition before trusting GUI state or sending another UI action.",
    "runtime_probe": "Treat only explicit runtime/readback proof as success; a preflight or launch attempt alone is not device or simulator proof.",
    "protocol_transaction": "Verify the complete frame fields, checksum, decoded values, and validation verdict before using the transaction.",
    "coverage_audit": "Resolve the listed gaps against the named sources; do not convert partial coverage into a complete claim.",
    "decision_gate": "Proceed only when the explicit gate verdict passes; use the listed blocker and required confirmation verbatim otherwise.",
    "catalog_or_inventory": "Choose an exact returned item/path before calling a mutating or GUI tool; absence in a bounded catalog is not universal absence.",
    "project_inspection": "Use the reported project identity, selected objects, counts, and limitations as the basis for the next exact edit or validation.",
    "artifact_export": "Verify destination, item count, size/hash, and source project before handing off the exported artifact.",
    "artifact_import": "Verify source package, destination project, imported identities, conflicts, and post-import validation before accepting the change.",
    "project_create": "Verify the scratch boundary, created identities, destination artifact, and validation proof before opening or editing it further.",
    "project_change": "Verify the exact target, before/after values, changed artifact, guard confirmation, and post-change validation.",
    "project_delete": "Verify the exact deleted identity, scratch/backup boundary, remaining references, and post-delete validation.",
    "project_lifecycle": "Use the reported PID/window/artifact and final lifecycle state; a process start is not proof that the intended project opened or saved.",
    "guided_procedure": "Follow only the returned source-backed steps and keep manual, read-only, guarded, and live-device boundaries distinct.",
    "domain_operation": "Use the explicit verdict, affected OWEN object, artifact paths, safety boundary, and limitations shown below.",
}


LAYOUT_BY_FAMILY = {
    "compatibility_alias": "delegated_result",
    "gui_observation": "ui_observation",
    "runtime_probe": "runtime_probe",
    "protocol_transaction": "protocol_frame",
    "coverage_audit": "audit_matrix",
    "decision_gate": "decision_gate",
    "catalog_or_inventory": "catalog",
    "project_inspection": "project_readback",
    "artifact_export": "artifact_receipt",
    "artifact_import": "artifact_receipt",
    "project_create": "change_receipt",
    "project_change": "change_receipt",
    "project_delete": "change_receipt",
    "project_lifecycle": "lifecycle",
    "guided_procedure": "procedure",
    "domain_operation": "domain_operation",
}


def layout(name: str, kind: str) -> str:
    short = name.removeprefix("owen_logic_")
    overrides = (
        (r"^(function|function_block|library|component|installation)_catalog$|toolbar_snapshot|shortcuts_catalog", "component_catalog"),
        (r"compiler_(diagnostics_audit|surface_probe)", "compiler_audit"),
        (r"modbus_(crc|request_build|frame_parse|response_build|transaction_validate|reference)", "protocol_frame"),
        (r"^project_st_|^st_lint$", "code_report"),
        (r"device_|live_device", "device_transaction"),
        (r"display_|visualization|screen", "display_readback"),
        (r"variable_table|project_variable", "variable_readback"),
        (r"capability_status|installation_audit|version$|health", "runtime_dashboard"),
        (r"coverage|parity|audit", "audit_matrix"),
    )
    return next((value for pattern, value in overrides if re.search(pattern, short)), LAYOUT_BY_FAMILY[kind])


def display_title(name: str) -> str:
    return name.removeprefix("owen_logic_").replace("_", " ").upper()


def main() -> int:
    specs: dict[str, dict[str, object]] = {}
    for tool in srv.TOOLS:
        name = str(tool["name"])
        schema = tool.get("inputSchema") if isinstance(tool.get("inputSchema"), dict) else {}
        required = schema.get("required") if isinstance(schema.get("required"), list) else []
        kind = family(name.removeprefix("owen_logic_"))
        specs[name] = {
            "title": display_title(name),
            "purpose": str(tool.get("description") or f"Run {name}."),
            "family": kind,
            "layout": layout(name, kind),
            "required_inputs": required,
            "next": NEXT_BY_FAMILY[kind],
            "visible_contract": [
                "tool-specific purpose and request",
                "verdict and decision facts",
                "affected OWEN identities and artifacts",
                "guardrails and execution boundary",
                "all decision-critical facts plus a bounded collection preview without JSON syntax",
                "complete collections and diagnostic payloads preserved in raw_result or a hash-verified artifact",
                "visible counts and omission boundaries tell the model when deeper evidence exists",
                "tool-specific next decision",
            ],
        }
    output = Path(__file__).with_name("owen_output_specs.json")
    output.write_text(json.dumps(specs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "specs": len(specs), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
