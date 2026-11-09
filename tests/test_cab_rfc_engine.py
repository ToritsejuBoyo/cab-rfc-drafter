#!/usr/bin/env python3
"""
test_cab_rfc_engine.py - Functional Unit Tests for CAB RFC Validation Engine.
"""

import json
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
    format_markdown_report,
    parse_duration_minutes,
    sanitize_bundle,
    validate_timing_headroom
)


class TestCabRfcEngine(unittest.TestCase):

    def test_duration_parsing(self):
        """Test flexible parsing of duration strings and numeric values."""
        self.assertEqual(parse_duration_minutes(30), 30)
        self.assertEqual(parse_duration_minutes("45m"), 45)
        self.assertEqual(parse_duration_minutes("45 mins"), 45)
        self.assertEqual(parse_duration_minutes("2h"), 120)
        self.assertEqual(parse_duration_minutes("1.5 hours"), 90)
        self.assertEqual(parse_duration_minutes("0"), 0)
        self.assertEqual(parse_duration_minutes(-10), 0)
        self.assertEqual(parse_duration_minutes("invalid"), 0)

    def test_risk_scoring_matrix(self):
        """Test standard 4-dimension scoring calculation."""
        data = {
            "risk_assessment": {
                "scope_score": 1,
                "redundancy_score": 1,
                "reversibility_score": 1,
                "precedent_score": 1
            },
            "rollback_plan": {"commands": ["revert"]}
        }
        res = calculate_risk(data)
        self.assertEqual(res["total_risk_score"], 4)
        self.assertEqual(res["risk_tier"], "LOW")
        self.assertEqual(res["recommended_category"], "STANDARD")

        # High risk major change
        data_major = {
            "risk_assessment": {
                "scope_score": 3,
                "redundancy_score": 3,
                "reversibility_score": 2,
                "precedent_score": 3
            },
            "rollback_plan": {"commands": ["revert"]}
        }
        res_major = calculate_risk(data_major)
        self.assertEqual(res_major["total_risk_score"], 11)
        self.assertEqual(res_major["risk_tier"], "HIGH")
        self.assertEqual(res_major["recommended_category"], "MAJOR")

    def test_automatic_high_risk_escalation(self):
        """Test automatic escalation to High Risk on missing rollback commands or destructive actions."""
        # Missing rollback
        data_no_rb = {
            "risk_assessment": {"scope_score": 1, "redundancy_score": 1, "reversibility_score": 1, "precedent_score": 1},
            "rollback_plan": {}
        }
        res_no_rb = calculate_risk(data_no_rb)
        self.assertEqual(res_no_rb["risk_tier"], "HIGH")
        self.assertGreaterEqual(res_no_rb["total_risk_score"], 10)
        self.assertTrue(any("Zero documented rollback commands" in e for e in res_no_rb["escalations"]))

        # Destructive SQL command
        data_drop = {
            "implementation_steps": [{"action": "DROP TABLE critical_ledger"}]
        }
        res_drop = calculate_risk(data_drop)
        self.assertEqual(res_drop["risk_tier"], "HIGH")
        self.assertTrue(any("Destructive command" in e for e in res_drop["escalations"]))

    def test_window_arithmetic_overrun(self):
        """Test window overrun detection when implementation + rollback > window."""
        data_overrun = {
            "scheduled_window": {"duration_minutes": 60},
            "implementation_steps": [
                {"duration_minutes": 40},
                {"duration_minutes": 15}
            ],
            "rollback_plan": {
                "duration_minutes": 20,
                "decision_cutoff_point": "2026-11-15T02:00:00Z"
            }
        }
        timing = validate_timing_headroom(data_overrun)
        self.assertFalse(timing["timing_feasible"])
        self.assertEqual(timing["total_active_minutes"], 75)
        self.assertTrue(any("Guaranteed Window Overrun" in d for d in timing["timing_defects"]))

    def test_window_arithmetic_headroom(self):
        """Test window calculation with acceptable headroom."""
        data_ok = {
            "scheduled_window": {"duration_minutes": 120},
            "implementation_steps": [
                {"duration_minutes": 30},
                {"duration_minutes": 20}
            ],
            "rollback_plan": {
                "duration_minutes": 20,
                "decision_cutoff_point": "2026-11-15T02:00:00Z"
            }
        }
        timing = validate_timing_headroom(data_ok)
        self.assertTrue(timing["timing_feasible"])
        self.assertEqual(timing["total_active_minutes"], 70)
        self.assertEqual(timing["headroom_buffer_minutes"], 50)
        self.assertGreater(timing["headroom_buffer_pct"], 40.0)

    def test_vague_step_rejection(self):
        """Test rejection of generic single-word step descriptions."""
        vague_data = {
            "implementation_steps": [
                {"action": "reboot", "command": ""},
                {"action": "apply config", "command": ""}
            ]
        }
        defects = audit_procedural_quality(vague_data)
        self.assertTrue(any("contains generic placeholder" in d for d in defects))

    def test_markdown_report_generation(self):
        """Test formatting of audit Markdown report."""
        sample_data = {
            "title": "Core Router Upgrade",
            "business_justification": "Upgrade BGP peering engine",
            "change_category": "NORMAL",
            "scheduled_window": {"duration_minutes": 60},
            "systems_impacted": ["rtr-01"],
            "pre_checks": [{"command": "show ip bgp sum"}],
            "implementation_steps": [{"action": "Upgrade IOS-XE", "command": "install activate", "duration_minutes": 20}],
            "rollback_plan": {"trigger_conditions": "Peer down", "decision_cutoff_point": "15m prior", "duration_minutes": 10, "commands": ["install rollback"]},
            "verification_plan": [{"command": "show ip bgp sum"}]
        }
        audit = audit_rfc(sample_data)
        report = format_markdown_report(audit, sample_data)
        self.assertIn("# CAB Readiness Evaluation: Core Router Upgrade", report)
        self.assertIn("Risk Assessment Breakdown", report)
        self.assertIn("Maintenance Window & Headroom Audit", report)


if __name__ == "__main__":
    unittest.main()

