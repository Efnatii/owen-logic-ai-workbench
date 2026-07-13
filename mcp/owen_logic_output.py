"""Per-tool human and AI output contracts for the OWEN Logic MCP surface."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DISPLAY_FORMAT_VERSION = "workbench-personal-v6"
_SPEC_PATH = Path(__file__).with_name("owen_output_specs.json")
OWEN_OUTPUT_SPECS: dict[str, dict[str, Any]] = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
_SENSITIVE = re.compile(r"token|secret|password|cookie|credential|authorization|api[_-]?key", re.I)
_NOISY = re.compile(r"(^|_)(stack|traceback|base64|raw_bytes|binary_data|debug_dump)($|_)", re.I)
_CATALOG_ALIAS_KIND = {
    "owen_logic_function_catalog": "function",
    "owen_logic_function_block_catalog": "function_block",
}
_CATALOG_PREVIEW_LIMIT = 8
_RECORD_PREVIEW_LIMIT = 6

_LAYOUT_HEADINGS = {
    "delegated_result": "Delegated capability and exact boundary",
    "ui_observation": "Observed window and controls",
    "runtime_probe": "Runtime verdict and measured readback",
    "protocol_frame": "Protocol frame and validation",
    "audit_matrix": "Coverage verdict and unresolved gaps",
    "decision_gate": "Gate decision and prerequisites",
    "catalog": "Available OWEN items",
    "component_catalog": "OWEN component catalog",
    "project_readback": "Project identity and selected objects",
    "artifact_receipt": "Artifact receipt and validation",
    "change_receipt": "Project change and readback",
    "lifecycle": "Process, window, and project lifecycle",
    "procedure": "Source-backed procedure",
    "domain_operation": "OWEN operation outcome",
    "compiler_audit": "Compiler surface and evidence boundary",
    "code_report": "Structured Text code and diagnostics",
    "device_transaction": "Device transaction and safety state",
    "display_readback": "Display model and visual readback",
    "variable_readback": "Variable model and binding readback",
    "runtime_dashboard": "Installation and runtime health",
}

_DECISION_LAYOUTS = {
    "runtime_probe", "audit_matrix", "decision_gate", "catalog", "component_catalog",
    "project_readback", "procedure", "compiler_audit", "runtime_dashboard",
    "ui_observation", "display_readback", "variable_readback",
}


def _catalog_alias_projection(tool_name: str, raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    catalog_kind = _CATALOG_ALIAS_KIND.get(tool_name)
    target = raw.get("target_result")
    if not catalog_kind or not isinstance(target, dict) or not isinstance(target.get("catalogs"), dict):
        return None
    entries = target["catalogs"].get(catalog_kind)
    entries = entries if isinstance(entries, list) else []
    installed_assets = target.get("installed_assets") if isinstance(target.get("installed_assets"), dict) else {}
    asset_counts = {key: len(value) for key, value in installed_assets.items() if isinstance(value, list)}
    projection = {
        "compatibility_alias": raw.get("compatibility_alias"),
        "mode": raw.get("mode"),
        "note": raw.get("note"),
        "server": raw.get("server"),
        "target_tool": raw.get("target_tool"),
        "catalog_kind": catalog_kind,
        "catalog_entry_count": len(entries),
        "catalog_entries_preview": entries[:_CATALOG_PREVIEW_LIMIT],
        "catalog_entries_omitted": max(0, len(entries) - _CATALOG_PREVIEW_LIMIT),
        "catalog_source": {
            "installation": target.get("installation"),
            "help_index_source": target.get("help_index_source"),
            "query": target.get("query"),
            "function_count": target.get("function_count"),
            "function_block_count": target.get("function_block_count"),
            "read_only": target.get("read_only"),
            "installed_asset_counts": asset_counts,
        },
    }
    return projection, raw


def _compiler_diagnostics_projection(tool_name: str, raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    reflection = raw.get("deep_reflection")
    if tool_name != "owen_logic_compiler_diagnostics_audit" or not isinstance(reflection, dict):
        return None
    assemblies = reflection.get("assemblies") if isinstance(reflection.get("assemblies"), list) else []
    assembly_summaries = []
    selected_type_count = 0
    selected_method_count = 0
    for assembly in assemblies:
        if not isinstance(assembly, dict):
            continue
        selected_types = assembly.get("selected_types") if isinstance(assembly.get("selected_types"), list) else []
        type_summaries = []
        for selected in selected_types:
            if not isinstance(selected, dict):
                continue
            methods = selected.get("methods") if isinstance(selected.get("methods"), list) else []
            constructors = selected.get("constructors") if isinstance(selected.get("constructors"), list) else []
            properties = selected.get("properties") if isinstance(selected.get("properties"), list) else []
            fields = selected.get("fields") if isinstance(selected.get("fields"), list) else []
            selected_type_count += 1
            selected_method_count += len(methods)
            type_summaries.append({
                "full_name": selected.get("full_name"),
                "found": selected.get("found"),
                "is_public": selected.get("is_public"),
                "is_class": selected.get("is_class"),
                "is_interface": selected.get("is_interface"),
                "is_abstract": selected.get("is_abstract"),
                "base_type": selected.get("base_type"),
                "constructor_count": len(constructors),
                "method_count": len(methods),
                "property_count": len(properties),
                "field_count": len(fields),
            })
        assembly_summaries.append({
            "assembly": assembly.get("assembly"),
            "path": assembly.get("path"),
            "exists": assembly.get("exists"),
            "assembly_name": assembly.get("assembly_name"),
            "type_count": assembly.get("type_count"),
            "matched_type_count": assembly.get("matched_type_count"),
            "selected_types": type_summaries,
        })
    projection = dict(raw)
    projection["deep_reflection"] = {
        "ok": reflection.get("ok"),
        "compile_api_surface_confirmed": reflection.get("compile_api_surface_confirmed"),
        "process_guard": reflection.get("process_guard"),
        "assemblies": assembly_summaries,
    }
    projection["reflection_counts"] = {
        "assembly_count": len(assembly_summaries),
        "selected_type_count": selected_type_count,
        "selected_method_count": selected_method_count,
    }
    return projection, raw


def _scalar(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    text = str(value)
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9_]*)=true\b", r"\1 set to yes", text)
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9_]*)=false\b", r"\1 set to no", text)
    return text


def _humanize(key: str) -> str:
    def humanize_segment(segment: str) -> str:
        words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", segment).replace("_", " ").strip()
        return words[:1].upper() + words[1:] if words else "Value"

    return " / ".join(humanize_segment(segment) for segment in str(key).split(" / "))


def _cell(value: Any, limit: int = 280) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        if not value:
            return "—"
        text = ", ".join(_scalar(item) for item in value) if all(not isinstance(item, (dict, list, tuple)) for item in value) else f"{len(value)} records"
    elif isinstance(value, dict):
        text = "—" if not value else f"{len(value)} fields"
    else:
        text = _scalar(value)
    text = re.sub(r"\s+", " ", text).replace("|", "\\|").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _table(rows: list[tuple[str, Any]], first: str = "Fact", second: str = "Observed value") -> list[str]:
    if not rows:
        return []
    return [f"- {_cell(label, 120)}: {_cell(value)}" for label, value in rows[:5]]


def _flatten(value: Any, prefix: str = "", depth: int = 0) -> list[tuple[str, Any]]:
    if _SENSITIVE.search(prefix):
        return [(_humanize(prefix), "[redacted]")]
    if _NOISY.search(prefix):
        size = len(value) if isinstance(value, (str, bytes, list, dict)) else 1
        return [(_humanize(prefix), f"diagnostic payload ({size}); exact data preserved")]
    if isinstance(value, dict) and depth < 3:
        rows: list[tuple[str, Any]] = []
        for key, item in value.items():
            if item in (None, "", [], {}, ()):
                continue
            label = f"{prefix} / {key}" if prefix else str(key)
            if isinstance(item, dict):
                rows.extend(_flatten(item, label, depth + 1))
            elif isinstance(item, (list, tuple)) and item and any(isinstance(child, (dict, list, tuple)) for child in item):
                rows.append((_humanize(label), f"{len(item)} records"))
            else:
                rows.append((_humanize(label), item))
        return rows
    return [(_humanize(prefix or "value"), value)]


def _record_table(key: str, values: list[Any]) -> list[str]:
    if not values:
        return []
    total = len(values)
    values = values[:_RECORD_PREVIEW_LIMIT]
    if all(not isinstance(item, dict) for item in values):
        lines = [f"- {_cell(item, 700)}" for item in values]
        if total > len(values):
            lines.append(f"… {total - len(values)} more records; complete collection is in raw_result")
        return lines
    records = [item if isinstance(item, dict) else {"value": item} for item in values]
    preferred = ["name", "title", "full_name", "type", "id", "status", "category", "path", "address", "function_code", "data_type", "value", "description", "source"]
    keys: list[str] = []
    for candidate in preferred + [field for record in records for field in record]:
        if candidate not in keys and any(candidate in record for record in records):
            keys.append(candidate)
        if len(keys) >= 5:
            break
    lines = ["| # | " + " | ".join(_humanize(field) for field in keys) + " |", "|---|" + "---|" * len(keys)]
    for index, record in enumerate(records, 1):
        lines.append("| " + str(index) + " | " + " | ".join(_cell(record.get(field), 220) for field in keys) + " |")
    if total > len(records):
        lines.append(f"… {total - len(records)} more records; complete collection is in raw_result")
    return lines


def _render_value(key: str, value: Any) -> list[str]:
    label = _humanize(key)
    if _SENSITIVE.search(key):
        return [f"### {label}", "[redacted]"]
    if key == "deep_reflection" and isinstance(value, dict):
        assemblies = value.get("assemblies") if isinstance(value.get("assemblies"), list) else []
        rows = [
            ("Compile API confirmed", value.get("compile_api_surface_confirmed")),
            ("Reflection passed", value.get("ok")),
            ("Assemblies", len(assemblies)),
            ("Selected types", sum(len(item.get("selected_types") or []) for item in assemblies if isinstance(item, dict))),
            ("Selected method count", sum(
                selected.get("method_count") if isinstance(selected.get("method_count"), int) else len(selected.get("methods") or [])
                for item in assemblies if isinstance(item, dict)
                for selected in (item.get("selected_types") or []) if isinstance(selected, dict)
            )),
        ]
        assembly_rows = [
            {field: assembly.get(field) for field in ("assembly", "exists", "type_count", "matched_type_count")}
            for assembly in assemblies[:8] if isinstance(assembly, dict)
        ]
        return [f"### {label}", *_table(rows), *(["#### Assemblies", *_record_table("assemblies", assembly_rows)] if assembly_rows else [])]
    if key == "deep_reflection" and isinstance(value, dict):
        assemblies = value.get("assemblies") if isinstance(value.get("assemblies"), list) else []
        assembly_rows: list[dict[str, Any]] = []
        type_rows: list[dict[str, Any]] = []
        for assembly in assemblies:
            if not isinstance(assembly, dict):
                continue
            assembly_rows.append({field: assembly.get(field) for field in ("assembly", "path", "exists", "type_count", "matched_type_count")})
            for selected in assembly.get("selected_types") if isinstance(assembly.get("selected_types"), list) else []:
                if isinstance(selected, dict):
                    type_rows.append({"assembly": assembly.get("assembly"), **selected})
        decision_rows = [("Compile API surface confirmed", value.get("compile_api_surface_confirmed")), ("Reflection passed", value.get("ok")), ("Detail boundary", value.get("detail_boundary"))]
        lines = [f"### {label}", *_table(decision_rows)]
        if assembly_rows:
            lines.extend(["#### Assemblies", *_record_table("assemblies", assembly_rows)])
        if type_rows:
            type_columns = [
                ("assembly", "Assembly"),
                ("full_name", "Full name"),
                ("found", "Found"),
                ("is_public", "Public"),
                ("kind", "Kind"),
                ("base_type", "Base type"),
                ("constructor_count", "Constructor count"),
                ("method_count", "Method count"),
                ("property_count", "Property count"),
                ("field_count", "Field count"),
            ]
            normalized_types: list[dict[str, Any]] = []
            for row in type_rows:
                if row.get("is_interface"):
                    kind = "interface"
                elif row.get("is_class"):
                    kind = "abstract class" if row.get("is_abstract") else "class"
                else:
                    kind = "type"
                normalized_types.append({
                    **row,
                    "kind": kind,
                    "constructor_count": row.get("constructor_count") if isinstance(row.get("constructor_count"), int) else len(row.get("constructors") or []),
                    "method_count": row.get("method_count") if isinstance(row.get("method_count"), int) else len(row.get("methods") or []),
                    "property_count": row.get("property_count") if isinstance(row.get("property_count"), int) else len(row.get("properties") or []),
                    "field_count": row.get("field_count") if isinstance(row.get("field_count"), int) else len(row.get("fields") or []),
                })
            lines.extend([
                "#### Selected types",
                "| # | " + " | ".join(label for _, label in type_columns) + " |",
                "|---|" + "---|" * len(type_columns),
                *[
                    "| " + str(index) + " | " + " | ".join(_cell(row.get(field), 220) for field, _ in type_columns) + " |"
                    for index, row in enumerate(normalized_types, 1)
                ],
            ])
        if isinstance(value.get("process_guard"), dict):
            lines.extend(["#### Process guard", *_table(_flatten(value["process_guard"]))])
        return lines
    if isinstance(value, str) and (key in {"code", "text", "source_text", "script", "st", "stdout", "stderr"} or "code" in key.lower()):
        shown = value if len(value) <= 2400 else value[:2400].rstrip() + f"\n… (+{len(value) - 2400} chars)"
        return [f"### {label}", "```text", shown, "```"]
    if isinstance(value, dict):
        return [f"### {label}", *_table(_flatten(value)[:10])]
    if isinstance(value, (list, tuple)):
        return [f"### {label}", *_record_table(key, list(value))]
    return _table([(label, value)])


def _request(arguments: dict[str, Any]) -> list[str]:
    if not arguments:
        return ["Request: defaults."]
    parts: list[str] = []
    for key, value in arguments.items():
        if _SENSITIVE.search(str(key)):
            shown = "[redacted]"
        else:
            shown = _cell(value, 140)
        parts.append(f"{_humanize(key)} = {shown}")
    return ["Request: " + "; ".join(parts) + "."]


def _section_for(key: str, value: Any) -> str:
    text = key.lower()
    if re.search(r"status|state|outcome|verdict|valid|success|passed|found|required_tools_ok|preflight|abort|issues|limitation|confirmed|detected|sufficient|available", text):
        return "Verdict and decision facts"
    if re.search(r"guard|risk|safe|read_only|allow|confirm|dry_run|executed|opened_|wrote_|backup|scratch|scope|policy|limit|permission|live_device", text):
        return "Safety and execution boundary"
    if re.search(r"path|project|file|output|destination|source|artifact|screenshot|hash|sha256|pid|hwnd|window|device|variable|element|screen|document|target|version|installation|server|operation", text):
        return "OWEN identities and artifacts"
    if re.search(r"count|total|returned|bytes|chars|duration|elapsed|coverage|depth|size|attempt", text):
        return "Measurements and coverage"
    if isinstance(value, (list, tuple)):
        return "Returned records and observations"
    return "Domain detail"


def _status(raw: Any, is_error: bool, layout: str) -> tuple[str, bool]:
    if is_error:
        return "FAILED", True
    if isinstance(raw, dict):
        text = str(raw.get("status") or raw.get("state") or raw.get("outcome") or "").lower()
        if raw.get("execution_permitted_by_this_tool") is False or raw.get("dry_run") is True or str(raw.get("decision") or "").lower() in {"guarded", "deny", "denied", "blocked"}:
            return "GUARDED", False
        if layout in _DECISION_LAYOUTS:
            if re.search(r"fail|error|blocked|abort|cancel|timeout|unavailable|partial|warn|degraded|pending|guard", text) or raw.get("ok") is False:
                return (text.upper() if text else "ATTENTION"), False
            return (text.upper() if text else "COMPLETE"), False
        if raw.get("ok") is False:
            return "FAILED", True
        if re.search(r"fail|error|blocked|abort|cancel|timeout|unavailable", text):
            return text.upper(), True
        if re.search(r"partial|warn|degraded|pending|guard", text):
            return text.upper(), False
    return "COMPLETE", False


def _summary(raw: Any, status: str, failed: bool) -> str:
    if not isinstance(raw, dict):
        return _cell(raw, 520)
    if failed:
        return _cell(raw.get("error") or raw.get("message") or raw.get("reason") or status, 520)
    for key in ("verdict", "summary", "message", "note", "decision", "status", "outcome"):
        value = raw.get(key)
        if value not in (None, "", [], {}) and not isinstance(value, (dict, list, tuple)):
            return _cell(value, 520)
    for key in ("items", "results", "entries", "records", "tools", "windows", "processes", "checks", "issues"):
        if isinstance(raw.get(key), list):
            return f"Returned {len(raw[key])} {_humanize(key).lower()}."
    return status.replace("_", " ").lower().capitalize() + "."


def _render_fields(raw: dict[str, Any], keys: list[str]) -> list[str]:
    scalar_rows: list[tuple[str, Any]] = []
    sections: list[str] = []
    complex_fields = 0
    for key in keys:
        if key not in raw or key in {"stack", "traceback"}:
            continue
        value = raw[key]
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (dict, list, tuple)) or (isinstance(value, str) and (key in {"code", "text", "source_text", "script", "st", "stdout", "stderr"} or "code" in key.lower())):
            if complex_fields >= 2:
                continue
            sections.extend(_render_value(key, value))
            complex_fields += 1
        else:
            scalar_rows.append((_humanize(key), "[redacted]" if _SENSITIVE.search(key) else value))
    return ([*_table(scalar_rows[:5])] if scalar_rows else []) + sections


_LAYOUT_KEY_PATTERNS: dict[str, tuple[str, ...]] = {
    "runtime_dashboard": (r"installation|runtime|health|version", r"asset|source|root|path", r"issue|limitation|guardrail"),
    "runtime_probe": (r"passed|ready|matched|available|detected", r"issue|warning|condition", r"target|readback|backup|abort", r"guardrail|risk"),
    "decision_gate": (r"decision|passed|permitted|matched|required", r"issue|blocker|reason", r"target|confirmation", r"guardrail|risk"),
    "protocol_frame": (r"matched|valid|crc|exception", r"issue|warning", r"request$|response$|decoded", r"guardrail|risk"),
    "audit_matrix": (r"status_count|coverage|proven.*count|partial.*count|blocked.*count", r"gap|issue|limitation", r"partial_operations|blocked_operations|matrix", r"guardrail"),
    "compiler_audit": (r"confirmed|detected|claimed", r"limitation|remaining|issue", r"compiler_surface|deep_reflection|reflection_counts"),
    "catalog": (r"count|catalog_kind|mode", r"entries|items|records|catalog", r"source|installation"),
    "component_catalog": (r"count|catalog_kind|mode", r"entries|items|records|catalog|components", r"source|installation"),
    "artifact_receipt": (r"archive|artifact|output|path|format", r"count|hash|sha256|preserved", r"validation|roundtrip|inspection|conversion", r"gap|limitation|guardrail"),
    "change_receipt": (r"changed|created|deleted|patched|saved|mutated", r"project|path|id|name", r"validation|readback|issues", r"guardrail"),
    "code_report": (r"code|source|text|st$", r"diagnostic|issue|warning|error", r"path|artifact|count"),
    "device_transaction": (r"passed|permitted|matched|ready", r"issue|warning|blocker", r"target|request|response|readback", r"guardrail|risk"),
    "variable_readback": (r"status_count|coverage|proven.*count|partial.*count|blocked.*count", r"gap|issue|limitation", r"partial_operations|blocked_operations|operations|variables", r"guardrail"),
    "display_readback": (r"status|matched|valid|count", r"display|widget|screen|readback", r"issue|gap|limitation", r"guardrail"),
    "project_readback": (r"project|path|name|id", r"count|selected|active", r"items|records|variables|elements", r"issue|limitation"),
}


def _select_visible_keys(raw: dict[str, Any], layout: str, failed: bool) -> list[str]:
    skip = re.compile(r"^(server|tool|ok|read_only|scope)$|opened_|launched_|wrote_|executed$|_executed$|live_device_action_executed|project_write_performed", re.I)
    patterns = [
        r"error|message|reason|verdict|decision|status$|outcome$|summary|gap|warning|blocker|issue|limitation|guardrail",
        *(_LAYOUT_KEY_PATTERNS.get(layout) or (r"issue|warning|limitation|guardrail", r"path|file|artifact|id|name|count|result|record")),
    ]
    selected: list[str] = []
    for pattern in patterns:
        for key, value in raw.items():
            if key in selected or skip.search(key) or value in (None, "", [], {}):
                continue
            if isinstance(value, (dict, list, tuple)) and any(value == raw.get(existing) for existing in selected):
                continue
            if re.search(pattern, key, re.I):
                selected.append(key)
            if len(selected) >= 10:
                return selected
    if not selected:
        selected = [key for key, value in raw.items() if not skip.search(key) and value not in (None, "", [], {})][:8]
    return selected


_RU_STATUS = {
    "COMPLETE": "COMPLETE",
    "READY": "READY",
    "OK": "COMPLETE",
    "GUARDED": "GUARDED",
    "ATTENTION": "NEEDS ATTENTION",
    "PARTIAL": "PARTIAL",
    "DEGRADED": "DEGRADED",
    "FAILED": "FAILED",
    "BLOCKED": "BLOCKED",
    "UNAVAILABLE": "UNAVAILABLE",
}

_COLLECTION_NAMES = {
    "items": "items",
    "results": "results",
    "entries": "entries",
    "records": "records",
    "windows": "windows",
    "processes": "processes",
    "projects": "projects",
    "documents": "documents",
    "files": "files",
    "variables": "variables",
    "elements": "elements",
    "components": "components",
    "artifacts": "artifacts",
    "issues": "issues",
    "checks": "checks",
    "matches": "matches",
}


def _first(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = raw.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _record_caption(item: Any) -> str:
    if not isinstance(item, dict):
        return _cell(item, 260)
    identity = _first(item, "name", "title", "label", "path", "file", "id", "uuid", "code", "symbol", "caption")
    if identity is None:
        identity = _cell(item, 260)
    details: list[str] = []
    for key in ("version", "status", "type", "kind", "value", "description"):
        value = item.get(key)
        if value not in (None, "", [], {}) and value != identity:
            details.append(_cell(value, 100))
        if len(details) == 2:
            break
    return _cell(identity, 260) + (" — " + "; ".join(details) if details else "")


def _returned_records(raw: dict[str, Any]) -> tuple[str, list[Any]] | None:
    preferred = ("catalog_entries_preview", "results", "matches", "items", "entries", "records", "windows", "processes", "projects", "documents", "variables", "elements", "components", "artifacts", "files", "issues", "checks")
    for key in preferred:
        value = raw.get(key)
        if isinstance(value, list):
            return key, value
    return None


_TITLE_WORDS = {
    "ACTION": "ДЕЙСТВИЕ", "ADD": "ДОБАВЛЕНИЕ", "ANALYSIS": "АНАЛИЗ", "ARCHETYPE": "АРХЕТИП",
    "ARRAY": "МАССИВ", "AUDIT": "АУДИТ", "BIND": "ПРИВЯЗКА", "BLOCK": "БЛОК", "BUILD": "СБОРКА",
    "CANVAS": "ПОЛОТНО", "CAPABILITY": "ВОЗМОЖНОСТИ", "CASE": "СЛУЧАЙ", "CATALOG": "КАТАЛОГ",
    "CHECK": "ПРОВЕРКА", "CLONE": "КЛОНИРОВАНИЕ", "CLOUD": "ОБЛАКО", "CODEX": "CODEX",
    "COMPILER": "КОМПИЛЯТОР", "COMPONENT": "КОМПОНЕНТ", "CONFIG": "КОНФИГУРАЦИЯ", "CONFIRM": "ПОДТВЕРЖДЕНИЕ",
    "CONNECTION": "ПОДКЛЮЧЕНИЕ", "CONNECT": "ПОДКЛЮЧИТЬ", "CONTROL": "УПРАВЛЕНИЕ", "COPY": "КОПИРОВАНИЕ",
    "COVERAGE": "ПОКРЫТИЕ", "CREATE": "СОЗДАНИЕ", "CRC": "CRC", "DEBUG": "ОТЛАДКА", "DELETE": "УДАЛЕНИЕ",
    "DEVICE": "УСТРОЙСТВО", "DIAGNOSTICS": "ДИАГНОСТИКА", "DIALOG": "ДИАЛОГ", "DISPLAY": "ЭКРАН",
    "DOCUMENT": "ДОКУМЕНТ", "DOWNLOAD": "ЗАГРУЗКА", "EDIT": "ИЗМЕНЕНИЕ", "ELEMENT": "ЭЛЕМЕНТ",
    "EVIDENCE": "ДОКАЗАТЕЛЬСТВА", "EXAMPLE": "ПРИМЕР", "EXAMPLES": "ПРИМЕРЫ", "EXECUTE": "ВЫПОЛНЕНИЕ",
    "EXPORT": "ЭКСПОРТ", "EXTENSION": "РАСШИРЕНИЕ", "EXTENSIONS": "РАСШИРЕНИЯ", "EXTRACT": "ИЗВЛЕЧЕНИЕ",
    "FBD": "FBD", "FILE": "ФАЙЛ", "FIND": "ПОИСК", "FOCUS": "ФОКУС", "FORMAT": "ФОРМАТ",
    "FROM": "ИЗ", "FUNCTION": "ФУНКЦИЯ", "GROUP": "ГРУППА", "GUARD": "ЗАЩИТА", "GUARDED": "ЗАЩИЩЁННЫЙ",
    "GUARDRAIL": "ОГРАНИЧИТЕЛЬ", "GUI": "ГРАФИЧЕСКИЙ ИНТЕРФЕЙС", "HELP": "СПРАВКА", "HOTKEY": "ГОРЯЧАЯ КЛАВИША",
    "IMPORT": "ИМПОРТ", "INDEX": "ИНДЕКС", "INFO": "ИНФОРМАЦИЯ", "INLINE": "ВСТРОЕННЫЙ", "INSPECT": "ПРОВЕРКА",
    "INSTALL": "УСТАНОВКА", "INSTALLATION": "УСТАНОВКА", "IO": "ВВОД-ВЫВОД", "LAUNCH": "ЗАПУСК", "LIBRARY": "БИБЛИОТЕКА",
    "LIFECYCLE": "ЖИЗНЕННЫЙ ЦИКЛ", "LINT": "ПРОВЕРКА СТИЛЯ", "LIST": "СПИСОК", "LIVE": "РЕАЛЬНОЕ",
    "LOOPBACK": "ЛОКАЛЬНОЕ СОЕДИНЕНИЕ", "MACRO": "МАКРОС", "MANAGER": "МЕНЕДЖЕР", "MANUAL": "РУКОВОДСТВО",
    "MAP": "КАРТА", "MASTER": "МАСТЕР", "MENU": "МЕНЮ", "METADATA": "МЕТАДАННЫЕ", "MODEL": "МОДЕЛЬ",
    "MODBUS": "MODBUS", "NEW": "НОВЫЙ", "ONLINE": "ОНЛАЙН", "OPEN": "ОТКРЫТИЕ", "OWENCLOUD": "OWENCLOUD",
    "PACKAGE": "ПАКЕТ", "PANEL": "ПАНЕЛЬ", "PARITY": "СООТВЕТСТВИЕ", "PARSE": "РАЗБОР", "PASTE": "ВСТАВКА",
    "PATCH": "ИЗМЕНЕНИЕ", "PLAN": "ПЛАН", "POLICY": "ПОЛИТИКА", "PORTS": "ПОРТЫ", "PREFLIGHT": "ПРЕДПРОВЕРКА",
    "PREVIEW": "ПРЕДПРОСМОТР", "PROBE": "ПРОВЕРКА", "PROCEDURE": "ПРОЦЕДУРА", "PROCESS": "ПРОЦЕСС",
    "PROCESSES": "ПРОЦЕССЫ", "PROGRAM": "ПРОГРАММА", "PROJECT": "ПРОЕКТ", "PROJECTS": "ПРОЕКТЫ",
    "PROPERTY": "СВОЙСТВО", "QUERY": "ЗАПРОС", "READ": "ЧТЕНИЕ", "READBACK": "ПРОВЕРКА РЕЗУЛЬТАТА",
    "REFERENCE": "СПРАВКА", "REQUEST": "ЗАПРОС", "RESPONSE": "ОТВЕТ", "SAFE": "БЕЗОПАСНЫЙ", "SAMPLE": "ОБРАЗЕЦ",
    "SAVE": "СОХРАНЕНИЕ", "SCRATCH": "ТЕСТОВЫЙ", "SCREEN": "ЭКРАН", "SCREENSHOT": "СНИМОК ЭКРАНА",
    "SEARCH": "ПОИСК", "SELECT": "ВЫБОР", "SEND": "ОТПРАВКА", "SENSITIVE": "ЧУВСТВИТЕЛЬНЫЙ",
    "SET": "УСТАНОВКА", "SETTINGS": "НАСТРОЙКИ", "SHORTCUT": "СОЧЕТАНИЕ КЛАВИШ", "SHORTCUTS": "СОЧЕТАНИЯ КЛАВИШ",
    "SIMULATOR": "СИМУЛЯТОР", "SLAVE": "ВЕДОМЫЙ", "SMOKE": "ДЫМОВАЯ", "SNAPSHOT": "СНИМОК", "ST": "ST",
    "START": "ЗАПУСК", "STATUS": "СОСТОЯНИЕ", "STOP": "ОСТАНОВКА", "SUMMARY": "СВОДКА", "SURFACE": "ПОВЕРХНОСТЬ",
    "TABLE": "ТАБЛИЦА", "TARGET": "ЦЕЛЬ", "TCP": "TCP", "TEST": "ТЕСТ", "TO": "В", "TOOLBAR": "ПАНЕЛЬ ИНСТРУМЕНТОВ",
    "TRANSACTION": "ТРАНЗАКЦИЯ", "UI": "ИНТЕРФЕЙС", "VALIDATE": "ПРОВЕРКА", "VALIDATION": "ВАЛИДАЦИЯ",
    "VARIABLE": "ПЕРЕМЕННАЯ", "VARIABLES": "ПЕРЕМЕННЫЕ", "VENDOR": "ПОСТАВЩИК", "VERSION": "ВЕРСИЯ", "WINDOW": "ОКНО",
    "WINDOWS": "ОКНА", "WIRE": "СОЕДИНЕНИЕ", "WRITE": "ЗАПИСЬ",
}

_TITLE_PHRASES = {
    "COMPILER DIAGNOSTICS AUDIT": "АУДИТ ДИАГНОСТИКИ КОМПИЛЯТОРА",
    "PROJECT TARGET PATCH": "ИЗМЕНЕНИЕ ЦЕЛИ ПРОЕКТА",
    "PROJECT VARIABLE PATCH": "ИЗМЕНЕНИЕ ПЕРЕМЕННОЙ ПРОЕКТА",
    "PROJECT PROPERTY PATCH": "ИЗМЕНЕНИЕ СВОЙСТВА ПРОЕКТА",
    "PROJECT ELEMENT PATCH": "ИЗМЕНЕНИЕ ЭЛЕМЕНТА ПРОЕКТА",
    "PROJECT DISPLAY PATCH": "ИЗМЕНЕНИЕ ЭКРАНА ПРОЕКТА",
}


def _display_title(title: str) -> str:
    return title


def _answer_lines(tool_name: str, spec: dict[str, Any], raw: Any, status: str, failed: bool) -> list[str]:
    """Render an answer, not a pretty-printed subset of the transport object."""
    title = _display_title(str(spec["title"]))
    lines = [f"OWEN LOGIC / {title} — {_RU_STATUS.get(status, status.lower())}"]
    if not isinstance(raw, dict):
        lines.append(f"Received result: {_cell(raw, 520)}.")
        return lines

    if failed:
        problem = _scalar(_first(raw, "error", "message", "reason", "detail") or "the tool returned no reason")
        lines.append(f"Operation did not complete: {problem}.")
        required = spec.get("required_inputs") or []
        if required:
            lines.append("Required for retry: " + ", ".join(map(str, required)) + ".")
        return lines

    family = str(spec.get("family") or "domain_operation")
    records = _returned_records(raw)
    found = _first(raw, "found", "exists", "available")
    decision = _first(raw, "decision", "preflight_passed", "execution_permitted_by_this_tool", "permitted", "allowed")
    summary = _first(raw, "verdict", "summary", "message", "note", "outcome")
    summary_text = summary if not isinstance(summary, (dict, list, tuple)) else None
    artifact = _first(raw, "output_path", "artifact_path", "file", "path", "project_path", "source_path", "destination")
    issues = _first(raw, "issues", "blockers", "gaps", "limitations", "warnings")

    if family == "catalog_or_inventory":
        if found is False:
            lines.append("Nothing was found in the checked locations.")
        elif records:
            key, values = records
            total = _first(raw, "catalog_entry_count", "result_count", "count", "returned_count")
            number = int(total) if isinstance(total, int) and total >= len(values) else len(values)
            lines.append(f"Found {number} {_COLLECTION_NAMES.get(key, 'objects')}.")
        else:
            location = _first(raw, "executable", "install_dir", "installation", "root_path", "path")
            version = _first(raw, "version", "converter_version")
            if isinstance(version, dict):
                version = _first(version, "version", "display_version", "value", "file_version")
            if isinstance(version, (list, tuple)):
                version = None
            if location:
                lines.append("Local installation found: " + _cell(location, 360) + (f" (version {_cell(version, 100)})" if version else "."))
            else:
                lines.append("Local catalog check completed.")
    elif family == "coverage_audit":
        lines.append("Coverage check completed" + (f": {_cell(summary_text, 420)}." if summary_text else "."))
        reflection = raw.get("reflection_counts") if isinstance(raw.get("reflection_counts"), dict) else {}
        selected_methods = _first(reflection, "selected_method_count", "method_count")
        if selected_methods is not None:
            lines.append(f"Methods found in the inspected surface: {_cell(selected_methods, 80)}.")
        if raw.get("compile_api_surface_confirmed") is True:
            lines.append("The available compilation API surface is confirmed; this does not replace a full compilation proof.")
    elif family == "decision_gate":
        if decision is True:
            lines.append("Preconditions passed; the action is allowed within the declared boundary.")
        elif decision is False or status == "GUARDED":
            lines.append("No automatic action ran: explicit confirmation or missing preconditions are required before continuing.")
        else:
            lines.append("Pre-action conditions and guardrails were checked.")
    elif family == "runtime_probe":
        lines.append("Environment state was observed without performing a dangerous action" + (f": {_cell(summary_text, 420)}." if summary_text else "."))
    elif family == "gui_observation":
        window = raw.get("window") if isinstance(raw.get("window"), dict) else {}
        if raw.get("focused") is True and window:
            lines.append("OWEN Logic window brought to the foreground: " + _record_caption(window) + ".")
        elif window:
            lines.append("Observed window: " + _record_caption(window) + ".")
        else:
            lines.append("The GUI was checked without changing a project.")
    elif family in {"project_create", "project_change", "project_delete", "project_lifecycle"}:
        changed = _first(raw, "changed", "created", "deleted", "saved", "mutated")
        if changed is True:
            lines.append("Project change completed and must be verified by the readback below.")
        elif status == "GUARDED":
            lines.append("Project change did not run without an explicit allowing parameter.")
        else:
            lines.append("Project operation completed without the declared change." if changed is False else "Project operation completed.")
    elif family in {"artifact_export", "artifact_import"}:
        lines.append("Artifact processing completed" + (f": {_cell(artifact, 360)}." if artifact else "."))
    elif family == "protocol_transaction":
        frame = _first(raw, "frame_hex", "response_hex", "request_hex", "crc_hex", "decoded")
        lines.append("Protocol frame check completed" + (f": {_cell(frame, 360)}." if frame else "."))
    elif family == "compatibility_alias":
        alias = _first(raw, "compatibility_alias", "target_tool")
        lines.append("Request handled through the compatible safe route" + (f": {_cell(alias, 200)}." if alias else "."))
    else:
        lines.append("Operation completed" + (f": {_cell(summary_text, 420)}." if summary_text else "."))

    if artifact and family not in {"artifact_export", "artifact_import"}:
        lines.append("Related file or object: " + _cell(artifact, 420) + ".")
    if isinstance(issues, list) and issues:
        preview = "; ".join(_record_caption(value) for value in issues[:3])
        suffix = f"; {len(issues) - 3} more" if len(issues) > 3 else ""
        lines.append("Needs attention: " + preview + suffix + ".")
    nested_summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
    for key, prefix in (("gap", "Coverage gap"), ("limitation", "Limitation"), ("warning", "Warning")):
        value = nested_summary.get(key)
        if value not in (None, "", [], {}):
            lines.append(prefix + ": " + _cell(value, 420) + ".")
    for key, prefix in (("gap", "Coverage gap"), ("limitation", "Limitation"), ("warning", "Warning")):
        value = raw.get(key)
        if value not in (None, "", [], {}):
            lines.append(prefix + ": " + _cell(value, 420) + ".")
    for key, prefix in (("gaps", "Coverage gaps"), ("limitations", "Limitations"), ("warnings", "Warnings")):
        value = raw.get(key)
        if isinstance(value, list) and value:
            shown = "; ".join(_record_caption(entry) for entry in value[:3])
            suffix = f"; {len(value) - 3} more" if len(value) > 3 else ""
            lines.append(prefix + ": " + shown + suffix + ".")
    for key, value in raw.items():
        if "requirement" not in key.lower() or not isinstance(value, list) or not value:
            continue
        shown = "; ".join(_record_caption(entry) for entry in value[:3])
        suffix = f"; {len(value) - 3} more" if len(value) > 3 else ""
        lines.append("Still required for a complete result: " + shown + suffix + ".")
    if records:
        key, values = records
        shown = values[:4]
        if shown:
            lines.append("First results:")
            lines.extend(f"- {_record_caption(value)}" for value in shown)
        if len(values) > len(shown):
            lines.append(f"Showing {len(shown)} of {len(values)}; remaining records are in _meta.raw_result.")
    return lines


def _decision_envelope(tool_name: str, spec: dict[str, Any], raw: Any, status: str, failed: bool) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {"value": raw}
    identifiers: dict[str, Any] = {}
    counts: dict[str, Any] = {}
    paths: dict[str, Any] = {}
    for key, value in source.items():
        lower = str(key).lower()
        if isinstance(value, (dict, list, tuple)):
            if isinstance(value, (list, tuple)) and re.search(r"count|items|results|entries|records|tools|windows|processes|checks|issues", lower):
                counts[key] = len(value)
            continue
        if re.search(r"(^|_)(id|uuid|pid|hwnd)$|operation_id|project_id|device_id|target_id", lower):
            identifiers[key] = value
        elif re.search(r"count|total|returned|coverage|bytes|chars|duration|elapsed|attempt", lower):
            counts[key] = value
        elif re.search(r"path|file|root|uri$|url$|artifact$|destination|source$", lower):
            paths[key] = value
    envelope: dict[str, Any] = {
        "contract": "workbench.personal-tool-output/v6",
        "tool": tool_name,
        "title": _display_title(str(spec["title"])),
        "family": spec["family"],
        "layout": spec["layout"],
        "outcome": status.lower(),
        "summary": _summary(raw, status, failed),
        "is_error": failed,
        "retryable": bool(failed and re.search(r"timeout|tempor|busy|connection|transport|network", _summary(raw, status, failed), re.I)),
        "identifiers": identifiers,
        "counts": counts,
        "paths": paths,
        "next_action": spec["next"],
    }
    if failed:
        envelope["problem"] = {
            "type": str(source.get("error_code") or source.get("error_name") or source.get("status") or "owen_tool_execution_error"),
            "title": "OWEN Logic operation did not produce its advertised result",
            "detail": _summary(raw, status, failed),
            "required_inputs": spec.get("required_inputs") or [],
        }
    return envelope


def format_owen_tool_result(*, tool_name: str, arguments: dict[str, Any], raw_result: Any, is_error: bool = False) -> dict[str, Any]:
    if tool_name not in OWEN_OUTPUT_SPECS:
        raise KeyError(f"Missing mandatory OWEN personal output specification for {tool_name}")
    spec = OWEN_OUTPUT_SPECS[tool_name]
    externalized = None
    if isinstance(raw_result, dict) and not is_error:
        externalized = _catalog_alias_projection(tool_name, raw_result) or _compiler_diagnostics_projection(tool_name, raw_result)
    visible_result, metadata_result = externalized if externalized else (raw_result, raw_result)
    if tool_name == "owen_logic_focus_window" and isinstance(visible_result, dict) and "window_before_focus" in visible_result:
        visible_result = dict(visible_result)
        visible_result.pop("window_before_focus", None)
    layout = str(spec.get("layout") or "domain_operation")
    status, failed = _status(visible_result, is_error, layout)
    lines = _answer_lines(tool_name, spec, visible_result, status, failed)
    lines.append("Full machine-readable result is available in `_meta.raw_result`.")
    envelope = _decision_envelope(tool_name, spec, visible_result, status, failed)
    return {
        "content": [{"type": "text", "text": "\n".join(lines)}],
        "isError": failed,
        "_meta": {
            "decision": envelope,
            "raw_result": metadata_result,
            "display_format_version": DISPLAY_FORMAT_VERSION,
            "output_contract_tool": tool_name,
            "output_contract_family": spec["family"],
        },
    }
