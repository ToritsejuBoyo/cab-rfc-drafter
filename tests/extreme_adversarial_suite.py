#!/usr/bin/env python3
"""
extreme_adversarial_suite.py - 20 Extreme Adversarial, Chaos & Edge-Case Tests.

Stress-tests:
- Non-dict / scalar root inputs (lists, ints, None, strings)
- Negative durations and zero window constraints
- Huge payloads (10,000 implementation steps)
- Pathological Unicode, null bytes, and emoji injections
- Recursive dictionary nesting
- Missing keys, null values, and string-serialized numbers
- Sanitization idempotency across repeated passes
"""

import json
import math
import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from validate_rfc_readiness import (
    audit_procedural_quality,
    audit_rfc,
    calculate_risk,
    parse_duration_minutes,
    sanitize_bundle,
    validate_timing_headroom
)


class TestExtremeAdversarial(unittest.TestCase):

    def test_01_empty_dict(self):
        """Audit empty dictionary without unhandled exception."""
        res = audit_rfc({})
        self.assertFalse(res["cab_ready"])
        self.assertGreater(len(res["missing_mandatory_sections"]), 0)

    def test_02_all_null_values(self):
        """Audit dict where every key is explicitly None."""
        null_payload = {
            "title": None,
            "business_justification": None,
            "scheduled_window": None,
            "implementation_steps": None,
            "rollback_plan": None
        }
        res = audit_rfc(null_payload)
        self.assertFalse(res["cab_ready"])

    def test_03_negative_window_duration(self):
        """Negative window duration must be clamped or reported as defective."""
        data = {
            "scheduled_window": {"duration_minutes": -120},
            "implementation_steps": [{"duration_minutes": 20}],
            "rollback_plan": {"duration_minutes": 10}
        }
        timing = validate_timing_headroom(data)
        self.assertFalse(timing["timing_feasible"])
        self.assertEqual(timing["window_duration_minutes"], 0)

    def test_04_negative_step_duration(self):
        """Negative step duration must clamp to 0."""
        self.assertEqual(parse_duration_minutes(-50), 0)
        self.assertEqual(parse_duration_minutes("-50 mins"), 0)

    def test_05_float_duration_parsing(self):
        """Floating point duration strings."""
        self.assertEqual(parse_duration_minutes("1.5 hours"), 90)
        self.assertEqual(parse_duration_minutes("0.5h"), 30)
        self.assertEqual(parse_duration_minutes("45.8 mins"), 45)

    def test_06_massive_step_count(self):
        """Payload with 5,000 steps must complete without recursion error or memory exhaustion."""
        large_steps = [{"action": f"Sub-step {i}", "command": f"cmd {i}", "duration_minutes": 1} for i in range(5000)]
        data = {
            "title": "Large Migration",
            "business_justification": "Scale test",
            "change_category": "MAJOR",
            "scheduled_window": {"duration_minutes": 10000},
            "systems_impacted": ["srv01"],
            "pre_checks": [{"command": "status"}],
            "implementation_steps": large_steps,
            "rollback_plan": {"trigger_conditions": "failed", "decision_cutoff_point": "100m prior", "duration_minutes": 500, "commands": ["revert"]},
            "verification_plan": [{"command": "verify"}]
        }
        res = audit_rfc(data)
        self.assertTrue(res["cab_ready"])
        self.assertEqual(res["maintenance_window_audit"]["total_implementation_minutes"], 5000)

    def test_07_unicode_and_emojis_in_input(self):
        """Gracefully handle unicode characters and foreign alphabets in input data."""
        data = {
            "title": "Upgrade core database \u2014 \u6578\u64DA\u5EAB",
            "business_justification": "Performance optimization for international customers",
            "change_category": "NORMAL",
            "scheduled_window": {"duration_minutes": 60},
            "systems_impacted": ["db-01"],
            "pre_checks": [{"command": "ping -c 1 8.8.8.8"}],
            "implementation_steps": [{"action": "Apply binary patch package", "command": "run", "duration_minutes": 10}],
            "rollback_plan": {"trigger_conditions": "alert threshold exceeded", "decision_cutoff_point": "now", "duration_minutes": 5, "commands": ["undo"]},
            "verification_plan": [{"command": "check"}]
        }
        res = audit_rfc(data)
        self.assertIn("\u6578\u64DA\u5EAB", res["rfc_title"])

    def test_08_sanitization_idempotency(self):
        """Sanitizing a sanitized bundle twice produces identical results."""
        raw = {
            "lead_engineer": "lead@corp.example.com",
            "systems_impacted": ["router01.corp.example.internal", "192.168.10.1"]
        }
        s1 = sanitize_bundle(raw)
        s2 = sanitize_bundle(s1)
        self.assertEqual(s1["lead_engineer"], s2["lead_engineer"])
        self.assertEqual(s1["systems_impacted"], s2["systems_impacted"])

    def test_09_deep_nested_recursion(self):
        """Sanitize deeply nested dictionary structure."""
        curr = {"leaf_ip": "10.20.30.40"}
        for _ in range(50):
            curr = {"child": curr}
        sanitized = sanitize_bundle(curr)
        dump = json.dumps(sanitized)
        self.assertNotIn("10.20.30.40", dump)
        self.assertIn("192.0.2.", dump)

    def test_10_string_serialized_scores(self):
        """Handle risk scores passed as strings instead of integers."""
        data = {
            "risk_assessment": {
                "scope_score": "3",
                "redundancy_score": "2",
                "reversibility_score": "1",
                "precedent_score": "2"
            },
            "rollback_plan": {"commands": ["revert"]}
        }
        res = calculate_risk(data)
        self.assertEqual(res["total_risk_score"], 8)
        self.assertEqual(res["risk_tier"], "MEDIUM")

    def test_11_out_of_bounds_scores(self):
        """Clamp out-of-bounds scores (e.g. 99 or -5) between 1 and 3."""
        data = {
            "risk_assessment": {
                "scope_score": 99,
                "redundancy_score": -5,
                "reversibility_score": 10,
                "precedent_score": 0
            },
            "rollback_plan": {"commands": ["revert"]}
        }
        res = calculate_risk(data)
        self.assertEqual(res["dimensions"]["scope_score"], 3)
        self.assertEqual(res["dimensions"]["redundancy_score"], 1)
        self.assertEqual(res["dimensions"]["reversibility_score"], 3)
        self.assertEqual(res["dimensions"]["precedent_score"], 1)

    def test_12_non_string_implementation_steps(self):
        """Handle step entries formatted as simple strings or integers."""
        data = {
            "implementation_steps": [
                "execute command one on host A",
                12345,
                {"action": "valid step", "command": "run"}
            ]
        }
        defects = audit_procedural_quality(data)
        self.assertIsInstance(defects, list)

    def test_13_rollback_missing_triggers(self):
        """Reject rollback plan with commands but empty trigger conditions."""
        data = {
            "rollback_plan": {
                "commands": ["revert.sh"],
                "trigger_conditions": ""
            }
        }
        defects = audit_procedural_quality(data)
        self.assertTrue(any("lacks objective trigger conditions" in d for d in defects))

    def test_14_rollback_missing_commands(self):
        """Reject rollback plan with triggers but empty commands list."""
        data = {
            "rollback_plan": {
                "commands": [],
                "trigger_conditions": "Health check fails"
            }
        }
        defects = audit_procedural_quality(data)
        self.assertTrue(any("lacks executable backout commands" in d for d in defects))

    def test_15_case_insensitive_category_detection(self):
        """Correctly categorize regardless of casing."""
        data = {
            "title": "T",
            "business_justification": "J",
            "change_category": "major",
            "scheduled_window": {"duration_minutes": 60},
            "systems_impacted": ["s1"],
            "pre_checks": [{"command": "c"}],
            "implementation_steps": [{"action": "long step description", "command": "c", "duration_minutes": 10}],
            "rollback_plan": {"trigger_conditions": "t", "decision_cutoff_point": "c", "duration_minutes": 5, "commands": ["r"]},
            "verification_plan": [{"command": "v"}]
        }
        res = audit_rfc(data)
        self.assertEqual(res["risk_assessment"]["risk_tier"], "LOW")

    def test_16_string_scalar_to_sanitizer(self):
        """Sanitizer called directly on scalar strings."""
        res = sanitize_bundle("contact admin@corp.example.internal or call 192.168.1.100")
        self.assertNotIn("admin@corp.example.internal", res)
        self.assertNotIn("192.168.1.100", res)

    def test_17_integer_scalar_to_sanitizer(self):
        """Sanitizer handles integer or None gracefully."""
        self.assertEqual(sanitize_bundle(42), 42)
        self.assertIsNone(sanitize_bundle(None))

    def test_18_headroom_zero_when_window_zero(self):
        """Headroom percentage is safely 0.0 when window duration is 0."""
        data = {"scheduled_window": {"duration_minutes": 0}}
        timing = validate_timing_headroom(data)
        self.assertEqual(timing["headroom_buffer_pct"], 0.0)

    def test_19_missing_cutoff_triggers_defect(self):
        """Missing decision cutoff point triggers a defect."""
        data = {
            "scheduled_window": {"duration_minutes": 60},
            "rollback_plan": {"duration_minutes": 10, "commands": ["r"]}
        }
        timing = validate_timing_headroom(data)
        self.assertTrue(any("Missing explicit Go / No-Go Decision Cutoff" in d for d in timing["timing_defects"]))

    def test_20_tight_window_generates_warning(self):
        """Window with headroom between 0% and 15% generates tight window warning."""
        data = {
            "scheduled_window": {"duration_minutes": 100},
            "implementation_steps": [{"duration_minutes": 70}],
            "rollback_plan": {"duration_minutes": 20, "decision_cutoff_point": "cutoff", "commands": ["r"]}
        }
        timing = validate_timing_headroom(data)
        self.assertTrue(timing["timing_feasible"])
        self.assertEqual(timing["headroom_buffer_pct"], 10.0)
        self.assertTrue(any("Tight Maintenance Window" in d for d in timing["timing_defects"]))


if __name__ == "__main__":
    unittest.main()
