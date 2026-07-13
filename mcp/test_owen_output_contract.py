from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import owen_logic_server as srv
from owen_logic_output import OWEN_OUTPUT_SPECS, _LAYOUT_HEADINGS, format_owen_tool_result


class OwenPersonalOutputContractTests(unittest.TestCase):
    def test_every_tool_has_one_explicit_personal_spec(self) -> None:
        names = [str(tool["name"]) for tool in srv.TOOLS]
        self.assertEqual(len(names), 170)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(OWEN_OUTPUT_SPECS))
        for name in names:
            spec = OWEN_OUTPUT_SPECS[name]
            self.assertTrue(spec["title"])
            self.assertTrue(spec["purpose"])
            self.assertTrue(spec["family"])
            self.assertIn(spec["layout"], _LAYOUT_HEADINGS)
            self.assertTrue(spec["next"])
            self.assertGreaterEqual(len(spec["visible_contract"]), 6)

    def test_each_spec_renders_unique_identity_and_lossless_minimal_model_result(self) -> None:
        for name, spec in OWEN_OUTPUT_SPECS.items():
            raw = {
                "status": "partial",
                "project_path": f"C:/scratch/{name}.owle",
                "summary": {"checked": 3, "passed": 2, "gap": f"gap-for-{name}"},
                "records": [{"name": f"record-for-{name}", "value": 17}],
                "guardrail": {"read_only": True, "live_device_action_executed": False},
                "limitation": f"limit-for-{name}",
            }
            result = format_owen_tool_result(tool_name=name, arguments={"project_path": raw["project_path"]}, raw_result=raw)
            text = result["content"][0]["text"]
            self.assertIn(spec["title"], text)
            self.assertIn(f"gap-for-{name}", text)
            self.assertIn(f"limit-for-{name}", text)
            self.assertIn("_meta.raw_result", text)
            self.assertNotIn("## Next", text)
            self.assertNotIn(_LAYOUT_HEADINGS[spec["layout"]], text)
            self.assertNotRegex(text, r"(?m)^\s{2,}[a-z][a-z0-9_]*:")
            self.assertNotIn("Action:", text)
            self.assertNotIn("Input:", text)
            self.assertNotIn("Result:", text)
            self.assertNotIn("result fields", text)
            self.assertIs(result["_meta"]["raw_result"], raw)
            self.assertEqual(result["_meta"]["output_contract_tool"], name)
            self.assertEqual(result["_meta"]["display_format_version"], "workbench-personal-v6")
            self.assertNotIn("structuredContent", result)
            self.assertIs(result["_meta"]["raw_result"], raw)
            self.assertEqual(result["_meta"]["raw_result"]["records"][0]["name"], f"record-for-{name}")
            self.assertIn("_meta.raw_result", text)
            self.assertNotIn("| Fact | Observed value |", text)

    def test_failure_is_personal_actionable_and_does_not_print_stack_or_secret(self) -> None:
        name = "owen_logic_project_target_patch"
        result = format_owen_tool_result(
            tool_name=name,
            arguments={"project_path": "C:/scratch/demo.owle", "confirmation_token": "never-print"},
            raw_result={"error": "target migration confirmation is required", "tool": name, "stack": "NOISY STACK"},
            is_error=True,
        )
        text = result["content"][0]["text"]
        self.assertIn("PROJECT TARGET PATCH — FAILED", text)
        self.assertIn("target migration confirmation is required", text)
        self.assertIn("Operation did not complete", text)
        self.assertIn("_meta.raw_result", text)
        self.assertNotIn("never-print", text)
        self.assertNotIn("NOISY STACK", text)
        self.assertTrue(result["isError"])

    def test_catalog_alias_keeps_compact_preview_and_full_model_payload(self) -> None:
        raw = {
            "ok": True,
            "compatibility_alias": True,
            "mode": "delegate",
            "note": "Function catalog compatibility alias",
            "server": "owen_logic",
            "target_tool": "owen_logic_library_catalog",
            "target_result": {
                "installation": {"install_dir": "C:/Owen"},
                "help_index_source": "C:/Owen/help",
                "query": "",
                "function_count": 2,
                "function_block_count": 1,
                "catalogs": {
                    "function": [{"name": "ABS", "description": "absolute"}, {"name": "MIN", "description": "minimum"}],
                    "function_block": [{"name": "TON", "description": "timer"}],
                    "modbus": [{"name": "MB"}],
                },
                "installed_assets": {"st_language": ["a", "b"], "modbus": ["m1", "m2", "m3"]},
                "read_only": True,
            },
        }
        result = format_owen_tool_result(tool_name="owen_logic_function_catalog", arguments={}, raw_result=raw)
        text = result["content"][0]["text"]
        self.assertIn("ABS", text)
        self.assertIn("MIN", text)
        self.assertNotIn("TON", text)
        self.assertIn("Found 2", text)
        self.assertNotIn("artifact_path", text)
        self.assertIs(result["_meta"]["raw_result"], raw)
        self.assertIs(result["_meta"]["raw_result"], raw)

    def test_compiler_diagnostics_compacts_signatures_but_keeps_full_model_payload(self) -> None:
        raw = {
            "ok": True,
            "compile_api_surface_confirmed": True,
            "full_compiler_diagnostics_claimed": False,
            "remaining_requirements_for_full_closure": ["authoritative compile case"],
            "deep_reflection": {
                "ok": True,
                "compile_api_surface_confirmed": True,
                "process_guard": {"launched_programrelayfbd_pids": []},
                "assemblies": [{
                    "assembly": "Owen.Compiling.dll",
                    "path": "C:/Owen/Owen.Compiling.dll",
                    "exists": True,
                    "assembly_name": "Owen.Compiling",
                    "type_count": 10,
                    "matched_type_count": 1,
                    "selected_types": [{
                        "full_name": "Owen.Compiling.Compiler",
                        "found": True,
                        "is_public": True,
                        "is_class": True,
                        "is_interface": False,
                        "is_abstract": False,
                        "base_type": "System.Object",
                        "constructors": [".ctor()"],
                        "methods": ["Compile()", "Validate()"],
                        "properties": ["Errors"],
                        "fields": [],
                    }],
                }],
            },
        }
        result = format_owen_tool_result(tool_name="owen_logic_compiler_diagnostics_audit", arguments={}, raw_result=raw)
        text = result["content"][0]["text"]
        self.assertIn("Methods found in the inspected surface: 2", text)
        self.assertIn("authoritative compile case", text)
        self.assertNotIn("Compile()", text)
        self.assertIs(result["_meta"]["raw_result"], raw)
        self.assertEqual(result["_meta"]["raw_result"]["deep_reflection"]["assemblies"][0]["selected_types"][0]["methods"], ["Compile()", "Validate()"])

    def test_missing_spec_is_a_hard_registration_contract_failure(self) -> None:
        with self.assertRaises(KeyError):
            format_owen_tool_result(tool_name="owen_logic_unknown", arguments={}, raw_result={"ok": True})

    def test_focus_window_does_not_repeat_the_same_window_snapshot(self) -> None:
        window = {"hwnd": 42, "pid": 7, "title": "Owen Logic", "visible": True}
        raw = {"focused": True, "foreground_before_hwnd": 1, "foreground_after_hwnd": 42, "window": window, "window_before_focus": dict(window)}
        result = format_owen_tool_result(tool_name="owen_logic_focus_window", arguments={}, raw_result=raw)
        text = result["content"][0]["text"]
        self.assertEqual(text.count("Owen Logic"), 1)
        self.assertIs(result["_meta"]["raw_result"], raw)


if __name__ == "__main__":
    unittest.main()
