#!/usr/bin/env python3
"""Headless regression checks for the OWEN Logic MCP surface."""

from __future__ import annotations

import os
import sys
import unittest
import base64
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import owen_logic_server as srv


class OwenLogicServerSurfaceTests(unittest.TestCase):
    def test_tools_list_exposes_required_surface(self) -> None:
        response = srv.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tools = response["result"]["tools"]
        names = {tool["name"] for tool in tools}
        self.assertIn("owen_logic_program_file_analysis", names)
        self.assertIn("owen_logic_project_create_from_scratch", names)
        self.assertIn("owen_logic_component_catalog", names)
        self.assertIn("owen_logic_display_catalog", names)
        self.assertIn("owen_logic_display_coverage_audit", names)
        self.assertIn("owen_logic_display_archetype_coverage_audit", names)
        self.assertIn("owen_logic_project_display_gui_probe", names)
        self.assertIn("owen_logic_project_display_screen_gui_edit_probe", names)
        self.assertIn("owen_logic_project_display_screen_gui_copy_paste_delete_probe", names)
        self.assertIn("owen_logic_compiler_surface_probe", names)
        self.assertIn("owen_logic_variable_table_coverage_audit", names)
        self.assertIn("owen_logic_variable_table_gui_model_parity_audit", names)
        self.assertIn("owen_logic_modbus_tcp_loopback_smoke", names)
        self.assertIn("owen_logic_modbus_coverage_audit", names)
        self.assertIn("owen_logic_modbus_gui_model_parity_audit", names)
        self.assertIn("owen_logic_vendor_macro_coverage_audit", names)
        self.assertIn("owen_logic_target_coverage_audit", names)
        self.assertIn("owen_logic_vendor_macro_from_codex_package", names)

        tools_by_name = {tool["name"]: tool for tool in tools}
        live_readback_props = tools_by_name["owen_logic_simulator_live_readback_probe"]["inputSchema"]["properties"]
        self.assertIn("exercise_watch_window", live_readback_props)
        self.assertIn("exercise_watch_window_variable_picker", live_readback_props)
        self.assertIn("watch_window_variable_name", live_readback_props)
        self.assertIn("watch_window_variable_picker_tab", live_readback_props)
        target_gui_props = tools_by_name["owen_logic_project_target_gui_probe"]["inputSchema"]["properties"]
        self.assertIn("exercise_target_family_selection", target_gui_props)
        self.assertIn("target_family_name", target_gui_props)
        self.assertIn("exercise_target_modification_selection", target_gui_props)
        self.assertIn("target_modification_text", target_gui_props)
        self.assertIn("allow_target_migration_create", target_gui_props)
        self.assertIn("confirm_target_migration_scratch_only", target_gui_props)
        self.assertIn("save_after_target_migration", target_gui_props)
        component_manager_props = tools_by_name["owen_logic_project_component_manager_gui_probe"]["inputSchema"]["properties"]
        self.assertIn("exercise_download_to_project_library", component_manager_props)
        self.assertIn("allow_component_manager_project_library_download", component_manager_props)
        self.assertIn("confirm_component_manager_project_download_scratch_only", component_manager_props)
        self.assertIn("save_after_component_manager_action", component_manager_props)
        self.assertIn("close_component_manager_after_project_library_download", component_manager_props)
        self.assertIn("save_main_project_after_component_manager_close", component_manager_props)
        self.assertIn("select_component_row_before_project_library_download", component_manager_props)
        self.assertIn("allow_component_manager_checkbox_geometry_fallback", component_manager_props)
        self.assertIn("component_row_click_wait_seconds", component_manager_props)
        self.assertIn("post_component_manager_action_wait_seconds", component_manager_props)
        self.assertIn("post_component_manager_close_wait_seconds", component_manager_props)
        self.assertIn("component_manager_max_depth", component_manager_props)
        self.assertIn("component_manager_max_children", component_manager_props)
        self.assertIn("component_manager_filtered_max_controls", component_manager_props)
        self.assertIn("component_manager_ui_timeout_seconds", component_manager_props)
        device_menu_props = tools_by_name["owen_logic_project_device_menu_dialog_probe"]["inputSchema"]["properties"]
        toolbar_props = tools_by_name["owen_logic_project_variable_table_toolbar_probe"]["inputSchema"]["properties"]
        for props in (device_menu_props, toolbar_props):
            self.assertIn("variable_table_target_tab_name", props)
            self.assertIn("require_variable_table_target_tab", props)
            self.assertIn("variable_table_target_tab_wait_seconds", props)
        self.assertIn("allow_port_settings_ok_close", device_menu_props)
        self.assertIn("confirm_port_settings_no_change", device_menu_props)
        self.assertIn("port_settings_ok_wait_seconds", device_menu_props)
        modbus_create_props = tools_by_name["owen_logic_project_modbus_variable_create"]["inputSchema"]["properties"]
        self.assertIn("create_network_variable_descriptor", modbus_create_props)
        self.assertIn("network_variable_unique_id", modbus_create_props)
        self.assertIn("mapping_parameter_unique_id", modbus_create_props)
        self.assertIn("mapping_parameter_path", modbus_create_props)
        display_edit_schema = tools_by_name["owen_logic_project_display_screen_gui_edit_probe"]["inputSchema"]
        display_edit_props = display_edit_schema["properties"]
        self.assertEqual(
            display_edit_schema["required"],
            ["project_path", "allow_safe_runtime", "allow_gui_display_edit"],
        )
        self.assertIn("description_text", display_edit_props)
        self.assertIn("save_wait_seconds", display_edit_props)
        self.assertIn("max_depth", display_edit_props)
        self.assertIn("max_children", display_edit_props)
        self.assertIn("max_display_hits", display_edit_props)
        self.assertIn("include_offscreen", display_edit_props)
        display_copy_delete_schema = tools_by_name["owen_logic_project_display_screen_gui_copy_paste_delete_probe"]["inputSchema"]
        display_copy_delete_props = display_copy_delete_schema["properties"]
        self.assertEqual(
            display_copy_delete_schema["required"],
            [
                "project_path",
                "allow_safe_runtime",
                "allow_gui_display_edit",
                "confirm_display_copy_paste_delete_scratch_only",
            ],
        )
        self.assertIn("confirm_display_copy_paste_delete_scratch_only", display_copy_delete_props)
        self.assertIn("save_wait_seconds", display_copy_delete_props)
        self.assertIn("max_depth", display_copy_delete_props)

        init = srv.handle_request({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}})
        self.assertEqual(init["result"]["serverInfo"]["version"], srv.SERVER_VERSION)
        self.assertGreaterEqual(len(tools), 90)

    def test_display_screen_gui_edit_probe_dispatch_requires_opt_in(self) -> None:
        response = srv.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "owen_logic_project_display_screen_gui_edit_probe",
                    "arguments": {"project_path": "unused.owle"},
                },
            }
        )
        result = response["result"]
        text = result["content"][0]["text"]
        self.assertTrue(result["isError"])
        self.assertIn("owen_logic_project_display_screen_gui_edit_probe", text)
        self.assertNotIn("Unknown tool", text)

    def test_display_screen_gui_copy_paste_delete_probe_dispatch_requires_opt_in(self) -> None:
        response = srv.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "owen_logic_project_display_screen_gui_copy_paste_delete_probe",
                    "arguments": {"project_path": "unused.owle"},
                },
            }
        )
        result = response["result"]
        text = result["content"][0]["text"]
        self.assertTrue(result["isError"])
        self.assertIn("owen_logic_project_display_screen_gui_copy_paste_delete_probe", text)
        self.assertNotIn("Unknown tool", text)

    def test_program_file_analysis_is_read_only_and_catalog_backed(self) -> None:
        before_pids = {
            row["pid"]
            for row in srv.tasklist_programrelay()
            if isinstance(row.get("pid"), int)
        }
        result = srv.program_file_analysis(
            {
                "max_items": 8,
                "include_hashes": False,
                "include_file_lists": False,
                "include_compiler_surface": True,
                "include_process_check": False,
            }
        )
        after_pids = {
            row["pid"]
            for row in srv.tasklist_programrelay()
            if isinstance(row.get("pid"), int)
        }
        if not result["installation"]["found"]:
            self.skipTest("OWEN Logic installation not found on this machine")

        self.assertFalse(after_pids - before_pids)
        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertGreaterEqual(result["file_counts"]["total_files"], 1)
        self.assertGreaterEqual(result["target_catalog"]["pr_count"], 1)
        self.assertTrue(result["required_tools_ok"], result["required_tool_checks"])
        module_keys = set(result["component_catalog"]["module_keys"] or [])
        self.assertTrue({"PR100.2416", "PR200.28"} & module_keys)
        self.assertTrue(result["compiler_surface"]["compiler_surface_detected"])
        self.assertFalse(result["compiler_surface"]["headless_compiler_cli_confirmed"])
        guard = result["compiler_surface"]["reflection_process_guard"]
        self.assertEqual(guard["launched_programrelayfbd_pids"], [])

    def test_compiler_surface_default_does_not_spawn_programrelay(self) -> None:
        before_pids = {
            row["pid"]
            for row in srv.tasklist_programrelay()
            if isinstance(row.get("pid"), int)
        }
        result = srv.compiler_surface_probe(
            {
                "include_strings": False,
                "run_converter_probe": False,
            }
        )
        after_pids = {
            row["pid"]
            for row in srv.tasklist_programrelay()
            if isinstance(row.get("pid"), int)
        }

        self.assertTrue(result["ok"])
        self.assertTrue(result["compiler_surface_detected"])
        self.assertTrue(result["reflection"]["skipped"])
        self.assertFalse(after_pids - before_pids)

    def test_component_manager_action_candidate_helpers(self) -> None:
        ui_tree = {
            "name": "Component Manager",
            "control_type": "ControlType.Window",
            "children": [
                {
                    "name": "\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432 \u0431\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0443 \u043f\u0440\u043e\u0435\u043a\u0442\u0430",
                    "automation_id": "toProjectNButton",
                    "control_type": "ControlType.Button",
                    "class_name": "WindowsForms10.Button",
                    "bounding_rect": {"x": 237, "y": 58, "width": 211, "height": 22},
                    "children": [],
                },
                {
                    "name": "\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u0443\u044e \u0431\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0443",
                    "automation_id": "toLibraryNButton",
                    "control_type": "ControlType.Button",
                    "class_name": "WindowsForms10.Button",
                    "bounding_rect": {"x": 458, "y": 58, "width": 229, "height": 22},
                    "children": [],
                },
                {
                    "name": "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c",
                    "automation_id": "saveButton",
                    "control_type": "ControlType.Button",
                    "class_name": "WindowsForms10.Button",
                    "children": [],
                },
                {
                    "name": "\u0421\u0442\u0440\u043e\u043a\u0430 0",
                    "automation_id": "",
                    "control_type": "ControlType.Custom",
                    "bounding_rect": {"x": 237, "y": 110, "width": 898, "height": 25},
                    "children": [],
                },
                {
                    "name": "\u0421\u0442\u0440\u043e\u043a\u0430 \u0432\u043d\u0438\u0437",
                    "automation_id": "",
                    "control_type": "ControlType.Button",
                    "children": [],
                },
                {
                    "name": "\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442 \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0439",
                    "automation_id": "",
                    "control_type": "ControlType.Pane",
                    "children": [
                        {
                            "name": "",
                            "automation_id": "",
                            "control_type": "ControlType.Text",
                            "text_pattern_text": "(1000M) - \u041c\u0430\u043a\u0440\u043e\u0441 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d \u0432 \u043f\u0440\u043e\u0435\u043a\u0442\r",
                            "children": [],
                        }
                    ],
                },
            ],
        }

        summary = srv.collect_component_manager_controls(ui_tree, max_controls=20)

        self.assertEqual(summary["button_count"], 4)
        self.assertEqual(summary["download_action_candidate_count"], 2)
        self.assertEqual(summary["state_changing_action_candidate_count"], 2)
        self.assertEqual(summary["operation_result_control_count"], 2)
        self.assertTrue(summary["project_library_macro_loaded_message_detected"])
        self.assertIn("download_to_project_library", summary["action_categories_detected"])
        self.assertIn("download_to_local_library", summary["action_categories_detected"])
        self.assertIn("operation_result_save", summary["action_categories_detected"])
        self.assertTrue(
            all(row["action_not_clicked_by_probe"] for row in summary["state_changing_action_candidates"])
        )
        project_candidate = srv.component_manager_action_candidate_by_category(
            summary,
            "download_to_project_library",
        )
        local_candidate = srv.component_manager_action_candidate_by_category(
            summary,
            "download_to_local_library",
            require_enabled=False,
        )
        self.assertIsNotNone(project_candidate)
        self.assertIsNotNone(local_candidate)
        self.assertEqual(project_candidate["automation_id"], "toProjectNButton")
        self.assertEqual(local_candidate["automation_id"], "toLibraryNButton")
        self.assertEqual(
            srv.component_manager_control_click_point(project_candidate),
            (342.5, 69.0),
        )
        row_candidate = srv.component_manager_first_visible_grid_row_candidate(ui_tree)
        self.assertIsNotNone(row_candidate)
        self.assertEqual(row_candidate["control_type"], "ControlType.Custom")
        self.assertEqual(
            srv.component_manager_control_click_point(row_candidate),
            (686.0, 122.5),
        )
        fallback = srv.component_manager_checkbox_geometry_fallback(
            project_candidate,
            {"rect": {"left": 0, "top": 0, "right": 1200, "bottom": 900}},
        )
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback["source"], "project_library_button_relative_checkbox_geometry_fallback")
        self.assertEqual(fallback["derived_from_action_candidate"]["automation_id"], "toProjectNButton")
        self.assertEqual(
            srv.component_manager_control_click_point(fallback),
            (251.0, 122.0),
        )
        self.assertIsNone(
            srv.component_manager_checkbox_geometry_fallback(
                project_candidate,
                {"rect": {"left": 0, "top": 0, "right": 240, "bottom": 100}},
            )
        )

    def test_fbd_element_model_with_path_accepts_macro_block_model(self) -> None:
        direct = {"ElementModel": {"UniqueId": "direct"}}
        store = {"ElementBlockStoreModel": {"ElementModel": {"UniqueId": "store"}}}
        macro = {"ElementBlockModel": {"ElementModel": {"UniqueId": "macro"}}}

        self.assertEqual(srv.fbd_element_model_with_path(direct), (direct["ElementModel"], "ElementModel"))
        self.assertEqual(
            srv.fbd_element_model_with_path(store),
            (store["ElementBlockStoreModel"]["ElementModel"], "ElementBlockStoreModel/ElementModel"),
        )
        self.assertEqual(
            srv.fbd_element_model_with_path(macro),
            (macro["ElementBlockModel"]["ElementModel"], "ElementBlockModel/ElementModel"),
        )

    def test_variable_table_target_tab_candidate_helpers(self) -> None:
        ui_tree = {
            "name": "\u041f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0435",
            "control_type": "ControlType.Window",
            "bounding_rect": {"x": 100, "y": 40, "width": 900, "height": 540},
            "children": [
                {
                    "name": "\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0435",
                    "automation_id": "",
                    "class_name": "WindowsForms10.Window",
                    "control_type": "ControlType.TabItem",
                    "is_enabled": True,
                    "is_offscreen": False,
                    "bounding_rect": {"x": 112, "y": 50, "width": 132, "height": 24},
                    "children": [],
                },
                {
                    "name": "Slave",
                    "automation_id": "",
                    "class_name": "WindowsForms10.Window",
                    "control_type": "ControlType.TabItem",
                    "is_enabled": True,
                    "is_offscreen": False,
                    "bounding_rect": {"x": 244, "y": 50, "width": 96, "height": 24},
                    "children": [],
                },
                {
                    "name": "SlaveCounter",
                    "automation_id": "",
                    "class_name": "WindowsForms10.Window",
                    "control_type": "ControlType.DataItem",
                    "is_enabled": True,
                    "is_offscreen": False,
                    "bounding_rect": {"x": 244, "y": 210, "width": 180, "height": 24},
                    "children": [],
                },
            ],
        }

        candidate = srv.variable_table_target_tab_candidate(ui_tree, "Slave")

        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate["name"], "Slave")
        self.assertIn("slave", candidate["matched_terms"])
        self.assertEqual(srv.variable_table_control_click_point(candidate), (292.0, 62.0))
        self.assertIn("\u0441\u0435\u0442\u0435\u0432", srv.variable_table_target_tab_terms("\u0421\u0435\u0442\u0435\u0432\u044b\u0435"))

        child_candidate = srv.variable_table_target_tab_child_window_candidate(
            [
                {
                    "text": "\u0421\u0435\u0442\u0435\u0432\u044b\u0435, \u0421\u043b\u043e\u0442 1",
                    "class_name": "WindowsForms10.SysTabControl32",
                    "visible": True,
                    "enabled": True,
                    "rect": {"left": 270, "top": 88, "width": 122, "height": 24},
                }
            ],
            "Slave",
        )
        self.assertIsNotNone(child_candidate)
        assert child_candidate is not None
        self.assertEqual(child_candidate["source"], "win32_child_window")
        self.assertEqual(srv.variable_table_control_click_point(child_candidate), (331.0, 100.0))

        geometry_candidate = srv.variable_table_target_tab_geometry_fallback(
            {"rect": {"left": 100, "top": 40, "width": 900, "height": 540}},
            "Slave",
        )
        self.assertIsNotNone(geometry_candidate)
        assert geometry_candidate is not None
        self.assertEqual(geometry_candidate["source"], "network_tab_geometry_fallback")
        self.assertEqual(srv.variable_table_control_click_point(geometry_candidate), (331.0, 86.0))

    def test_modbus_map_rows_for_variable_name_matches_exact_marker(self) -> None:
        modbus_map = {
            "rows": [
                {"row_type": "device", "device_name": "\u0421\u0430\u043c"},
                {"row_type": "variable", "variable_name": "CODEX_NET_LONG_IMPORT"},
                {"row_type": "variable", "variable_name": "CODEX_NET_LONG_IMPORT_EXTRA"},
                {"row_type": "variable", "variable_name": ""},
            ]
        }

        rows = srv.modbus_map_rows_for_variable_name(modbus_map, "CODEX_NET_LONG_IMPORT")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["variable_name"], "CODEX_NET_LONG_IMPORT")
        self.assertEqual(srv.modbus_map_rows_for_variable_name(modbus_map, ""), [])

    def test_select_dialog_ok_button_uses_only_enabled_visible_ok(self) -> None:
        children = [
            {
                "hwnd": 1001,
                "class_name": "Button",
                "text": "\u041e\u0442\u043c\u0435\u043d\u0430",
                "visible": True,
                "enabled": True,
                "rect": {"left": 220, "top": 300, "right": 300, "bottom": 324, "width": 80, "height": 24},
            },
            {
                "hwnd": 1002,
                "class_name": "Button",
                "text": "OK",
                "visible": True,
                "enabled": True,
                "rect": {"left": 120, "top": 300, "right": 200, "bottom": 324, "width": 80, "height": 24},
            },
            {
                "hwnd": 1003,
                "class_name": "Button",
                "text": "\u041e\u041a",
                "visible": False,
                "enabled": True,
                "rect": {"left": 20, "top": 300, "right": 100, "bottom": 324, "width": 80, "height": 24},
            },
        ]

        button = srv.select_dialog_ok_button(children)

        self.assertIsNotNone(button)
        assert button is not None
        self.assertEqual(button["hwnd"], 1002)
        self.assertIsNone(
            srv.select_dialog_ok_button(
                [
                    {
                        "hwnd": 2001,
                        "class_name": "Button",
                        "text": "\u041e\u0442\u043c\u0435\u043d\u0430",
                        "visible": True,
                        "enabled": True,
                        "rect": {"width": 80, "height": 24},
                    }
                ]
            )
        )

    def test_network_modbus_variable_descriptor_helpers(self) -> None:
        existing_ids: set[str] = set()
        device = {"UniqueId": "11111111-1111-1111-1111-111111111111", "Rs485Mode": 1}
        args = {
            "variable_name": "CODEX_NET_LONG",
            "data_type": 3,
            "register_address": 520,
            "comment": "network table seed",
        }

        variable, metadata, descriptor = srv.build_network_rs485_variable_model(
            args,
            existing_ids,
            set(),
            device,
            "22222222-2222-2222-2222-222222222222",
        )

        self.assertEqual(variable["Name"], "CODEX_NET_LONG")
        self.assertEqual(variable["Register"], 520)
        self.assertEqual(variable["RegisterCount"], 1)
        self.assertEqual(variable["ReadFunction"], 1)
        self.assertEqual(variable["WriteFunction"], 5)
        self.assertNotIn("VariableId", variable)
        self.assertIsNone(metadata)
        self.assertEqual(descriptor["Discriminator"], 2)
        self.assertEqual(descriptor["VariableModel"]["UniqueId"], variable["UniqueId"])
        self.assertEqual(descriptor["VariableModelByModbus"], variable["UniqueId"])
        self.assertTrue(descriptor["IsRetain"])

        document = {"DocumentModel": {"Variables": []}}
        result = srv.append_network_variable_descriptor(document, "22222222-2222-2222-2222-222222222222", descriptor)
        self.assertEqual(result["document_variable_count_after"], 1)
        self.assertTrue(result["descriptor_created"])

        base = {"row_type": "device"}
        row = srv.modbus_variable_row(base, 0, variable, metadata)
        self.assertEqual(row["function_code"], 1)
        self.assertEqual(row["register_address"], 520)
        self.assertEqual(row["read_write"], "read_write")

        with self.assertRaises(ValueError):
            srv.build_network_rs485_variable_model(
                {"variable_name": "BAD_BOOL", "data_type": 0, "register_address": 1},
                set(),
                set(),
                device,
                "22222222-2222-2222-2222-222222222222",
            )

    def test_variable_table_coverage_audit_is_read_only_and_explicit(self) -> None:
        result = srv.variable_table_coverage_audit({})

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertEqual(result["remaining_gap_bucket"], "variable_table_gui_dialog_parity")
        self.assertGreaterEqual(result["proven_operation_count"], 11)
        self.assertGreaterEqual(result["partial_operation_count"], 3)
        self.assertIn("create_one_marker_variable_via_gui", result["proven_operations"])
        self.assertIn("network_register_csv_import_export_gui_parity", result["proven_operations"])
        self.assertIn("variable_table_gui_model_field_parity_audit", result["proven_operations"])
        self.assertIn("project_variable_table_array_authoring_via_gui", result["partial_operations"])
        self.assertIn("network_register_wizard_or_live_parity", result["partial_operations"])
        self.assertIn("live_variable_table_or_modbus_controller_interaction", result["blocked_operations"])
        statuses = {row["operation"]: row["status"] for row in result["operations"]}
        self.assertEqual(statuses["network_register_csv_import_export_gui_parity"], "proven_current_safe_scope")
        self.assertEqual(statuses["variable_table_gui_model_field_parity_audit"], "proven_current_safe_scope")
        self.assertEqual(statuses["network_register_wizard_or_live_parity"], "partial_semantic_gap")
        self.assertIn("do not promote", result["guardrail"])

    def test_variable_table_gui_model_parity_audit_is_read_only(self) -> None:
        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found")
        project = (
            workbench
            / "20_PRIVATE_UNSAFE"
            / "engineering"
            / "automation_pr200"
            / "project"
            / "owen_project_files"
            / "AVR_3IN1_PR200"
            / "AVR_3IN1_FBD_REAL_RUNTIME_TEST.owle"
        )
        if not project.exists():
            self.skipTest(f"OWEN fixture not found: {project}")
        source_hash = srv.sha256_file(project)
        result = srv.call_tool_data(
            "owen_logic_variable_table_gui_model_parity_audit",
            {"project_path": str(project), "max_examples": 5},
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["project_write_performed"])
        self.assertFalse(result["controller_contact_attempted"])
        self.assertEqual(result["source_hash_before"], source_hash)
        self.assertEqual(result["source_hash_after"], source_hash)
        self.assertTrue(result["source_hash_preserved"])
        self.assertIn("st_function_block_array_authoring", result["proven_gui_or_model_scopes"])
        self.assertIn("GUI variable-table array-tree create/edit/save/readback", result["unproven_gui_operations"])
        statuses = {row["concept"]: row["status"] for row in result["concept_matrix"]}
        self.assertEqual(statuses["st_array_declaration"], "proven_current_safe_scope")
        self.assertEqual(statuses["variable_table_array_tree"], "partial_semantic_gap")
        self.assertEqual(statuses["live_variable_or_controller_interaction"], "blocked_without_explicit_live_preflight")
        self.assertTrue(result["array_model_audit"]["read_only"])

    def test_display_coverage_audit_is_read_only_and_explicit(self) -> None:
        result = srv.display_coverage_audit({})

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["project_mutated"])
        self.assertEqual(result["remaining_gap_bucket"], "display_gui_editor_or_live_parity")
        self.assertGreaterEqual(result["proven_operation_count"], 13)
        self.assertGreaterEqual(result["partial_operation_count"], 2)
        self.assertIn("installed_display_widget_catalog_inventory", result["proven_operations"])
        self.assertIn("display_factory_archetype_compatibility_audit", result["proven_operations"])
        self.assertIn("bounded_display_gui_surface_probe", result["proven_operations"])
        self.assertIn("display_screen_manager_existing_screen_open_probe", result["proven_operations"])
        self.assertIn("display_screen_gui_description_edit_save_readback", result["proven_operations"])
        self.assertIn("display_screen_gui_copy_paste_delete_save_readback", result["proven_operations"])
        self.assertIn("owen_gui_display_editor_create_edit_delete_parity", result["partial_operations"])
        self.assertIn("live_display_visualization_or_controller_execution", result["blocked_operations"])
        statuses = {row["operation"]: row["status"] for row in result["operations"]}
        self.assertEqual(statuses["offline_display_preview_export"], "proven_current_safe_scope")
        self.assertNotIn("display_gui_editor_action_candidate_audit", statuses)
        self.assertEqual(statuses["display_screen_manager_existing_screen_open_probe"], "proven_current_safe_scope")
        self.assertEqual(statuses["display_screen_gui_description_edit_save_readback"], "proven_current_safe_scope")
        self.assertEqual(statuses["display_screen_gui_copy_paste_delete_save_readback"], "proven_current_safe_scope")
        self.assertEqual(statuses["display_factory_archetype_compatibility_audit"], "proven_current_safe_scope")
        self.assertEqual(statuses["arbitrary_display_widget_synthesis_without_archetype"], "partial_semantic_gap")
        self.assertIn("do not promote", result["guardrail"])

    def test_display_editor_action_candidates_are_surface_only(self) -> None:
        controls = [
            {
                "name": "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u044d\u043a\u0440\u0430\u043d",
                "control_type": "ControlType.Button",
                "localized_control_type": "\u043a\u043d\u043e\u043f\u043a\u0430",
                "path": "\u0412\u0438\u0437\u0443\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f/\u042d\u043a\u0440\u0430\u043d\u044b/\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u044d\u043a\u0440\u0430\u043d",
                "is_enabled": True,
                "bounding_rect": {"x": 10, "y": 20, "width": 90, "height": 24},
            },
            {
                "name": "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u044d\u043b\u0435\u043c\u0435\u043d\u0442",
                "control_type": "ControlType.MenuItem",
                "path": "\u042d\u043a\u0440\u0430\u043d/\u042d\u043b\u0435\u043c\u0435\u043d\u0442/\u0423\u0434\u0430\u043b\u0438\u0442\u044c",
                "is_enabled": True,
                "bounding_rect": {"x": 10, "y": 50, "width": 110, "height": 24},
            },
            {
                "name": "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c",
                "control_type": "ControlType.Button",
                "path": "\u041e\u0431\u0449\u0430\u044f \u043f\u0430\u043d\u0435\u043b\u044c/\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c",
                "is_enabled": True,
            },
        ]
        result = srv.display_editor_action_candidates(controls, max_candidates=10)

        self.assertEqual(result["candidate_count"], 2)
        self.assertTrue(result["state_changing_candidate_detected"])
        self.assertEqual(result["category_counts"]["create_or_add"], 1)
        self.assertEqual(result["category_counts"]["delete_or_remove"], 1)
        self.assertIn("does not click", result["limitation"])

    def test_display_archetype_coverage_audit_is_read_only(self) -> None:
        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found")
        project = (
            workbench
            / "20_PRIVATE_UNSAFE"
            / "engineering"
            / "automation_pr200"
            / "project"
            / "owen_project_files"
            / "AVR_3IN1_PR200"
            / "AVR_3IN1_FBD_REAL_RUNTIME_TEST.owle"
        )
        if not project.exists():
            self.skipTest(f"OWEN fixture not found: {project}")

        result = srv.display_archetype_coverage_audit(
            {
                "project_path": str(project),
                "max_factories": 40,
                "include_factory_details": False,
            }
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["project_write_performed"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertTrue(result["source_hash_preserved"])
        self.assertGreaterEqual(result["installed_factory_count_scored"], 1)
        self.assertIn("missing_compatible_archetype_type_names", result)

    def test_target_coverage_audit_is_read_only_and_explicit(self) -> None:
        result = srv.target_coverage_audit({})

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["project_mutated"])
        self.assertFalse(result["target_platform_migration_executed"])
        self.assertEqual(result["remaining_gap_bucket"], "target_gui_migration_or_live_parity")
        self.assertGreaterEqual(result["proven_operation_count"], 6)
        self.assertGreaterEqual(result["partial_operation_count"], 1)
        self.assertIn("installed_target_catalog_inventory", result["proven_operations"])
        self.assertIn("bounded_target_platform_gui_command_wizard_surface", result["proven_operations"])
        self.assertIn("full_gui_target_migration_create_save_readback", result["proven_operations"])
        self.assertIn("broad_vendor_backup_version_target_dialog_parity", result["partial_operations"])
        self.assertIn("live_target_download_or_controller_execution", result["blocked_operations"])
        statuses = {row["operation"]: row["status"] for row in result["operations"]}
        self.assertEqual(statuses["scratch_target_metadata_patch"], "proven_current_safe_scope")
        self.assertEqual(statuses["full_gui_target_migration_create_save_readback"], "proven_current_safe_scope")
        self.assertEqual(statuses["broad_vendor_backup_version_target_dialog_parity"], "partial_semantic_gap")
        self.assertIn("do not promote", result["guardrail"])

    def test_modbus_tcp_loopback_smoke_is_localhost_only(self) -> None:
        with self.assertRaises(ValueError):
            srv.modbus_tcp_loopback_smoke({})

        result = srv.call_tool_data(
            "owen_logic_modbus_tcp_loopback_smoke",
            {
                "allow_localhost_loopback": True,
                "cases": [
                    {
                        "name": "read_holding_registers",
                        "unit_id": 16,
                        "function_code": 3,
                        "start_address": 0,
                        "quantity": 2,
                        "register_values": [0x1234, 0x5678],
                    },
                    {
                        "name": "write_multiple_registers",
                        "unit_id": 16,
                        "function_code": 16,
                        "start_address": 10,
                        "values": [1, 2],
                    },
                ],
            },
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["host"], "127.0.0.1")
        self.assertEqual(result["case_count"], 2)
        self.assertEqual(result["matched_case_count"], 2)
        self.assertTrue(result["opened_loopback_socket"])
        self.assertTrue(result["opened_network_socket"])
        self.assertFalse(result["opened_external_network_socket"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["controller_contact_attempted"])
        self.assertEqual(result["risk_class"], "safe_localhost_loopback")
        self.assertIn("not evidence of real OWEN controller", result["limitation"])

    def test_modbus_coverage_audit_is_read_only_and_explicit(self) -> None:
        result = srv.call_tool_data("owen_logic_modbus_coverage_audit", {})

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["opened_external_network_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["controller_contact_attempted"])
        self.assertEqual(result["remaining_gap_bucket"], "modbus_gui_or_live_parity")
        self.assertGreaterEqual(result["proven_operation_count"], 10)
        self.assertGreaterEqual(result["partial_operation_count"], 2)
        self.assertGreaterEqual(result["blocked_operation_count"], 1)
        self.assertIn("modbus_tcp_localhost_loopback_execution", result["proven_operations"])
        self.assertIn("modbus_gui_model_field_parity_audit", result["proven_operations"])
        self.assertIn("modbus_port_settings_dialog_no_change_ok_completion", result["proven_operations"])
        self.assertIn("network_register_csv_import_export_gui_parity", result["proven_operations"])
        self.assertIn("modbus_master_slave_gui_wizard_edit_completion", result["partial_operations"])
        self.assertIn("broader_modbus_register_map_gui_or_wizard_parity", result["partial_operations"])
        self.assertIn("real_controller_modbus_com_tcp_execution", result["blocked_operations"])
        statuses = {row["operation"]: row["status"] for row in result["operations"]}
        self.assertEqual(statuses["modbus_gui_model_field_parity_audit"], "proven_current_safe_scope")
        self.assertEqual(statuses["modbus_port_settings_dialog_no_change_ok_completion"], "proven_current_safe_scope")
        self.assertEqual(statuses["network_register_csv_import_export_gui_parity"], "proven_current_safe_scope")
        self.assertEqual(statuses["broader_modbus_register_map_gui_or_wizard_parity"], "partial_semantic_gap")
        self.assertIn("do not promote localhost", result["guardrail"])

    def test_modbus_gui_model_parity_audit_is_read_only(self) -> None:
        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found")
        project = (
            workbench
            / "20_PRIVATE_UNSAFE"
            / "engineering"
            / "automation_pr200"
            / "project"
            / "owen_project_files"
            / "AVR_3IN1_PR200"
            / "AVR_3IN1_FBD_REAL_RUNTIME_TEST.owle"
        )
        if not project.exists():
            self.skipTest(f"OWEN fixture not found: {project}")

        result = srv.call_tool_data(
            "owen_logic_modbus_gui_model_parity_audit",
            {"project_path": str(project), "include_map_rows": False, "max_rows": 80},
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["project_write_performed"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["controller_contact_attempted"])
        self.assertTrue(result["project_summary"]["source_hash_preserved"])
        self.assertIn("Address", result["patchable_device_fields"])
        self.assertIn("Speed", result["patchable_setting_fields"])
        self.assertIn("GUI master/slave wizard edit/save/readback", " ".join(result["unproven_gui_operations"]))

    def test_vendor_macro_coverage_audit_is_read_only_and_explicit(self) -> None:
        result = srv.call_tool_data("owen_logic_vendor_macro_coverage_audit", {})

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["opened_http_catalog_socket"])
        self.assertFalse(result["live_device_action_executed"])
        self.assertFalse(result["vendor_import_export_executed"])
        self.assertFalse(result["component_install_update_executed"])
        self.assertFalse(result["project_mutated"])
        self.assertEqual(result["remaining_gap_bucket"], "proprietary_vendor_macro_format")
        self.assertGreaterEqual(result["proven_operation_count"], 5)
        self.assertGreaterEqual(result["partial_operation_count"], 3)
        self.assertIn("component_manager_gui_surface_and_action_candidates", result["proven_operations"])
        self.assertIn("component_manager_project_library_download_execution", result["proven_operations"])
        self.assertIn("bounded_gui_validation_after_project_library_download", result["proven_operations"])
        self.assertIn("owen_gui_vendor_macro_import_export_execution", result["partial_operations"])
        self.assertIn("component_manager_install_update_download_execution", result["partial_operations"])
        statuses = {row["operation"]: row["status"] for row in result["operations"]}
        self.assertEqual(statuses["codex_package_to_vendor_like_template_archive"], "proven_current_safe_scope")
        self.assertEqual(statuses["component_manager_project_library_download_execution"], "proven_current_safe_scope")
        self.assertEqual(statuses["bounded_gui_validation_after_project_library_download"], "proven_current_safe_scope")
        self.assertEqual(statuses["compiler_validation_after_gui_vendor_actions"], "partial_semantic_gap")
        self.assertIn("Do not promote Codex JSON package evidence", result["guardrail"])

    def test_compiler_diagnostics_case_requires_differential_or_visible_marker(self) -> None:
        marker = "CODEX_BROKEN_MARKER"
        valid_signal = {"error_control_count_total": 2}
        generic_broken_signal = {"error_control_count_total": 2, "project_load_error_signal": False}

        self.assertFalse(
            srv.diagnostics_case_authoritative_broken_confirmed(
                valid_signal,
                generic_broken_signal,
                {"ui_text": "generic critical project message"},
                marker,
            )
        )
        self.assertTrue(
            srv.diagnostics_case_authoritative_broken_confirmed(
                valid_signal,
                {"error_control_count_total": 3, "project_load_error_signal": False},
                {"ui_text": "generic critical project message"},
                marker,
            )
        )
        self.assertTrue(
            srv.diagnostics_case_authoritative_broken_confirmed(
                valid_signal,
                generic_broken_signal,
                {"ui_text": f"compiler diagnostic includes {marker}"},
                marker,
            )
        )
        self.assertFalse(
            srv.diagnostics_case_authoritative_broken_confirmed(
                valid_signal,
                {"error_control_count_total": 5, "project_load_error_signal": True},
                {"ui_text": f"load failure includes {marker}"},
                marker,
            )
        )

    def test_vendor_macro_from_codex_package_writes_scratch_archive_roundtrip(self) -> None:
        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found for scratch output")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scratch_dir = (
            workbench
            / "30_LOCAL_HEAVY"
            / "sandbox_tmp"
            / "owen_logic_mcp_selftest"
            / f"vendor_roundtrip_{stamp}"
        )
        scratch_dir.mkdir(parents=True, exist_ok=True)
        document_id = "11111111-1111-1111-1111-111111111111"
        package_path = scratch_dir / "codex_macro_package.json"
        package = {
            "format": srv.MACRO_PACKAGE_FORMAT,
            "vendor_macro_file": False,
            "source_vendor_macro_file": False,
            "source_document_id": document_id,
            "source_component_metadata": {
                "name": "CODEX_ROUNDTRIP",
                "group_name": "Codex",
                "author": "Codex",
                "description": "Targeted self-test package",
            },
            "elements": [
                {
                    "ElementModel": {
                        "UniqueId": "22222222-2222-2222-2222-222222222222",
                        "Title": "CODEX",
                        "Descriptor": "Codex test element",
                        "Location": {"IsEmpty": False, "X": 0, "Y": 0},
                        "Ports": [],
                    }
                }
            ],
            "connectors": [],
            "variables": [],
            "comment_blocks": [],
        }
        package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = srv.call_tool_data(
            "owen_logic_vendor_macro_from_codex_package",
            {
                "package_path": str(package_path),
                "output_dir": str(scratch_dir / "archive"),
                "file_name": "codex_roundtrip.tple",
                "verify_roundtrip": True,
            },
        )

        archive_path = Path(result["archive"]["path"])
        self.assertTrue(result["ok"], result)
        self.assertTrue(archive_path.exists())
        self.assertEqual(archive_path.suffix.lower(), ".tple")
        self.assertTrue(result["vendor_macro_file"])
        self.assertFalse(result["official_owen_export"])
        self.assertTrue(result["source_package_hash_preserved"])
        self.assertFalse(result["opened_gui"])
        self.assertFalse(result["opened_serial_port"])
        self.assertFalse(result["opened_network_socket"])
        self.assertFalse(result["vendor_import_export_executed"])
        self.assertFalse(result["component_install_update_executed"])
        self.assertFalse(result["project_mutated"])
        self.assertTrue(result["roundtrip_inspection"]["template_summary"]["parseable"])
        self.assertTrue(result["roundtrip_inspection"]["component_metadata_summary"]["parseable"])
        self.assertTrue(result["roundtrip_conversion"]["source_vendor_macro_file"])
        self.assertTrue(result["roundtrip_conversion"]["import_supported"])

        with self.assertRaises(ValueError):
            srv.vendor_macro_from_codex_package(
                {
                    "package_path": str(package_path),
                    "output_dir": str(Path(__file__).resolve().parent / "not_scratch_vendor_archive"),
                }
            )

    def test_from_scratch_generation_accepts_installed_pr_targets(self) -> None:
        catalog = srv.installed_target_catalog(500)
        pr_targets = [value for value in catalog.get("valid_dev_values") or [] if str(value).upper().startswith("PR")]
        if not pr_targets:
            self.skipTest("Installed OWEN PR target catalog is empty")

        requested_samples = ["PR-DEMO", "PR100EA1", "PR110", "PR120", "PR200ADA"]
        available = {str(value).upper(): str(value) for value in pr_targets}
        if os.environ.get("OWEN_LOGIC_TEST_ALL_TARGETS") == "1":
            sample_targets = pr_targets
        else:
            sample_targets = [available[value] for value in requested_samples if value in available]
            if not sample_targets:
                sample_targets = pr_targets[:3]

        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found for scratch output")
        scratch_dir = (
            workbench
            / "30_LOCAL_HEAVY"
            / "sandbox_tmp"
            / "owen_logic_mcp_selftest"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )

        for target in sample_targets:
            with self.subTest(target=target):
                result = srv.project_create_from_scratch(
                    {
                        "target_dev_value": target,
                        "output_dir": str(scratch_dir),
                        "file_name": f"selftest_{target.lower().replace('-', '_')}.owle",
                        "macro_count": 2,
                        "write_manifest": True,
                        "validate_after": True,
                    }
                )
                self.assertTrue(result["ok"])
                self.assertTrue(Path(result["created_project"]["path"]).exists())
                self.assertTrue(Path(result["manifest"]["path"]).exists())
                self.assertTrue(result["source_policy"]["created_new_owle_zip"])
                self.assertFalse(result["source_policy"]["copied_existing_owle_as_base"])
                self.assertFalse(result["opened_gui"])
                self.assertEqual(result["target"]["dev_value"], target)
                self.assertGreaterEqual(result["totals"]["document_count"], 1)
                self.assertGreaterEqual(result["totals"]["element_count"], 10)
                self.assertEqual(result["totals"]["macro_count"], 2)
                validation = result["validation_after"]
                self.assertTrue(validation["ok"], validation)
                self.assertEqual(validation["error_count"], 0)

    def test_from_scratch_generated_runtime_schema_fields(self) -> None:
        catalog = srv.installed_target_catalog(500)
        available = {str(value).upper(): str(value) for value in catalog.get("valid_dev_values") or []}
        target = available.get("PR200ADA")
        if not target:
            self.skipTest("Installed OWEN PR200ADA target is unavailable")

        workbench = srv.find_workbench_root()
        if workbench is None:
            self.skipTest("Workbench root not found for scratch output")
        scratch_dir = (
            workbench
            / "30_LOCAL_HEAVY"
            / "sandbox_tmp"
            / "owen_logic_mcp_selftest"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )

        result = srv.project_create_from_scratch(
            {
                "target_dev_value": target,
                "output_dir": str(scratch_dir),
                "file_name": "selftest_pr200ada_runtime_schema.owle",
                "macro_count": 0,
                "write_manifest": True,
                "validate_after": True,
            }
        )
        validation = result["validation_after"]
        self.assertTrue(validation["ok"], validation)

        loaded = srv.read_owle_sections(Path(result["created_project"]["path"]), include_hashes=False)
        project = loaded["sections"]["Project"]
        point_type_rows = []
        connected_rows = []
        for document in project.values():
            model = document.get("DocumentModel") if isinstance(document, dict) else None
            if not isinstance(model, dict):
                continue
            for element in model.get("Elements") or []:
                if not isinstance(element, dict):
                    continue
                element_model = element.get("ElementModel") if isinstance(element.get("ElementModel"), dict) else None
                if not isinstance(element_model, dict):
                    continue
                if int(element.get("Discriminator") or 0) == 1 and element.get("VariableInfoUId"):
                    connected_rows.append(element.get("ConnectedElements"))
                for primitive in element_model.get("Primitives") or []:
                    if not isinstance(primitive, dict):
                        continue
                    points = primitive.get("Points")
                    point_types = primitive.get("PointTypes")
                    if isinstance(points, list) and isinstance(point_types, str):
                        decoded = base64.b64decode(point_types.encode("ascii"), validate=True)
                        point_type_rows.append((len(points), len(decoded)))

        self.assertGreater(point_type_rows, [])
        self.assertTrue(all(point_count == type_count for point_count, type_count in point_type_rows))
        self.assertGreater(connected_rows, [])
        self.assertTrue(all(isinstance(row, list) for row in connected_rows))

    def test_simulator_watch_window_button_candidate_uses_panel_geometry(self) -> None:
        ui_tree = {
            "name": "root",
            "control_type": "ControlType.Window",
            "children": [
                {
                    "name": "\u041f\u0430\u043d\u0435\u043b\u044c \u0441\u0438\u043c\u0443\u043b\u044f\u0442\u043e\u0440\u0430",
                    "control_type": "ControlType.Pane",
                    "automation_id": "sim-panel",
                    "class_name": "WindowsForms10.Window",
                    "bounding_rect": {"x": 34, "y": 197, "width": 548, "height": 37},
                    "children": [],
                },
            ],
        }

        candidate = srv.find_simulator_watch_window_button_candidate(ui_tree)
        surface = srv.detect_simulator_watch_window_surface(
            {
                "name": "root",
                "control_type": "ControlType.Window",
                "children": [
                    {
                        "name": "\u041e\u043a\u043d\u043e \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0430",
                        "control_type": "ControlType.Pane",
                        "automation_id": "watch-pane",
                        "class_name": "WindowsForms10.Window",
                        "bounding_rect": {"x": 10, "y": 600, "width": 700, "height": 120},
                        "children": [
                            {
                                "name": "",
                                "control_type": "ControlType.DataGrid",
                                "automation_id": "VariablesDataGrid",
                                "class_name": "DataGrid",
                                "bounding_rect": {"x": 10, "y": 630, "width": 700, "height": 80},
                                "children": [],
                            }
                        ],
                    },
                ],
            }
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["method"], "simulator_panel_right_watch_window_button")
        self.assertEqual(candidate["click_x"], 559.0)
        self.assertEqual(candidate["click_y"], 215.5)
        self.assertTrue(surface["confirmed"])
        self.assertGreaterEqual(surface["control_count"], 1)
        self.assertIsNone(
            srv.find_simulator_watch_window_button_candidate(
                {
                    "name": "root",
                    "control_type": "ControlType.Window",
                    "children": [],
                }
            )
        )

    def test_simulator_watch_window_picker_helpers_and_row_readback(self) -> None:
        ui_tree = {
            "name": "root",
            "control_type": "ControlType.Window",
            "children": [
                {
                    "name": "",
                    "automation_id": "VariablesDataGrid",
                    "class_name": "DataGrid",
                    "control_type": "ControlType.DataGrid",
                    "bounding_rect": {"x": 60, "y": 600, "width": 700, "height": 120},
                    "children": [
                        {
                            "name": "ProgramRelayFBD.InfrastructureLayer.Adapters.Simulation.ViewModels.VariableViewModel",
                            "class_name": "DataGridRow",
                            "control_type": "ControlType.DataItem",
                            "bounding_rect": {"x": 62, "y": 625, "width": 690, "height": 20},
                            "children": [
                                {
                                    "name": "CODEX_IN_START",
                                    "class_name": "TextBlock",
                                    "control_type": "ControlType.Text",
                                    "bounding_rect": {"x": 68, "y": 627, "width": 200, "height": 14},
                                    "children": [],
                                },
                                {
                                    "name": "0",
                                    "class_name": "TextBlock",
                                    "control_type": "ControlType.Text",
                                    "bounding_rect": {"x": 303, "y": 627, "width": 200, "height": 14},
                                    "children": [],
                                },
                                {
                                    "name": "...",
                                    "class_name": "Button",
                                    "control_type": "ControlType.Button",
                                    "bounding_rect": {"x": 280, "y": 627, "width": 20, "height": 15},
                                    "children": [],
                                },
                            ],
                        }
                    ],
                },
                {
                    "name": "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u0443\u044e",
                    "control_type": "ControlType.Window",
                    "bounding_rect": {"x": 427, "y": 254, "width": 1066, "height": 524},
                    "children": [
                        {
                            "name": "OK",
                            "automation_id": "okButton",
                            "class_name": "WindowsForms10.Button",
                            "control_type": "ControlType.Button",
                            "bounding_rect": {"x": 1363, "y": 732, "width": 88, "height": 27},
                            "children": [],
                        },
                        {
                            "name": "\u0418\u043c\u044f \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0439 \u0421\u0442\u0440\u043e\u043a\u0430 0",
                            "control_type": "ControlType.DataItem",
                            "value_pattern_value": "CODEX_IN_START",
                            "bounding_rect": {"x": 689, "y": 382, "width": 132, "height": 22},
                            "children": [],
                        },
                    ],
                },
            ],
        }

        ellipsis = srv.find_watch_window_variable_ellipsis_candidate(ui_tree)
        dialog = srv.find_variable_picker_dialog_candidate(ui_tree)
        variable = srv.find_variable_picker_variable_candidate(ui_tree, "CODEX_IN_START")
        ok_button = srv.find_variable_picker_ok_button_candidate(ui_tree)
        summary = srv.collect_runtime_readback_controls(
            ui_tree,
            [{"name": "CODEX_IN_START", "expected_value_token": "0"}],
            20,
        )

        self.assertIsNotNone(ellipsis)
        self.assertEqual(ellipsis["click_x"], 290.0)
        self.assertIsNotNone(dialog)
        self.assertEqual(srv.variable_picker_tab_click_candidate(dialog, "standard")["click_x"], 573.0)
        self.assertIsNotNone(variable)
        self.assertIsNotNone(ok_button)
        self.assertEqual(summary["model_value_match_count"], 1)
        self.assertEqual(srv.detect_simulator_blocking_messages(ui_tree), [])

        blocking_tree = {
            "name": "Owen Logic - scratch.owle",
            "control_type": "ControlType.Window",
            "children": [
                {
                    "name": "Some modal dialog",
                    "control_type": "ControlType.Window",
                    "children": [
                        {
                            "name": "OK",
                            "automation_id": "okButton",
                            "control_type": "ControlType.Button",
                            "children": [],
                        },
                    ],
                }
            ],
        }
        blocking_messages = srv.detect_simulator_blocking_messages(blocking_tree)
        self.assertEqual(len(blocking_messages), 1)
        self.assertEqual(blocking_messages[0]["reason"], "modal_ok_button_visible")

    def test_target_selection_wizard_helpers(self) -> None:
        ui_tree = {
            "name": "\u0412\u044b\u0431\u043e\u0440 \u043c\u043e\u0434\u0435\u043b\u0438",
            "control_type": "ControlType.Window",
            "children": [
                {
                    "name": "",
                    "control_type": "ControlType.List",
                    "children": [
                        {
                            "name": "ProgramRelayFBD.InfrastructureLayer.Adapters.DeviceLineViewModel",
                            "class_name": "ListBoxItem",
                            "control_type": "ControlType.ListItem",
                            "bounding_rect": {"x": 172, "y": 325, "width": 298, "height": 85},
                            "children": [
                                {
                                    "name": "\u041f\u0420100",
                                    "class_name": "TextBlock",
                                    "control_type": "ControlType.Text",
                                    "children": [],
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "",
                    "automation_id": "targetsDataGrid",
                    "class_name": "DataGrid",
                    "control_type": "ControlType.DataGrid",
                    "children": [
                        {
                            "name": "ProgramRelayFBD.InfrastructureLayer.Adapters.TargetViewModel",
                            "class_name": "DataGridRow",
                            "control_type": "ControlType.DataItem",
                            "bounding_rect": {"x": 472, "y": 564, "width": 939, "height": 24},
                            "children": [
                                {
                                    "name": "PR100-24.8",
                                    "class_name": "TextBlock",
                                    "control_type": "ControlType.Text",
                                    "children": [],
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "\u0421\u043e\u0437\u0434\u0430\u0442\u044c",
                    "class_name": "Button",
                    "control_type": "ControlType.Button",
                    "is_enabled": True,
                    "bounding_rect": {"x": 1202, "y": 899, "width": 102, "height": 36},
                    "children": [],
                },
            ],
        }
        family = srv.find_target_family_list_item_candidate(ui_tree, "\u041f\u0420100")
        modification = srv.find_target_modification_row_candidate(ui_tree, "PR100-24.8")
        controls = srv.flatten_ui_tree(ui_tree)
        create_button = srv.find_target_create_button_candidate(controls)

        self.assertIsNotNone(family)
        self.assertEqual(family["click_x"], 321.0)
        self.assertIsNotNone(modification)
        self.assertEqual(modification["click_x"], 941.5)
        self.assertIsNotNone(create_button)
        self.assertEqual(create_button["click_x"], 1253.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
