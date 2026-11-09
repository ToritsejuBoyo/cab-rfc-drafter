#!/usr/bin/env python3
"""
draft_cab_rfc.py - Interactive & Automated Change Advisory Board (CAB) RFC Drafter.

Conducts structured engineer interviews or converts draft technical change outlines
into audit-compliant, ITIL 4-aligned Request for Change (RFC) packages.

Zero external dependencies (Python standard library only).
Includes client-side data sanitization (--sanitize).
"""

import argparse
import datetime
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional

from validate_rfc_readiness import audit_rfc, format_markdown_report, sanitize_bundle


def generate_sample_rfc() -> Dict[str, Any]:
    """Generate a clean, CAB-compliant reference RFC structure."""
    return {
        "rfc_id": "RFC-2026-11-049",
        "title": "Core Edge Firewall HA Firmware Upgrade from 7.0.12 to 7.2.6",
        "business_justification": "Remediates critical CVE-2026-4428 zero-day authentication bypass vulnerability on edge perimeter.",
        "change_category": "MAJOR",
        "lead_engineer": "eng-secops@corp.example.internal",
        "peer_reviewer": "eng-netlead@corp.example.internal",
        "service_owner": "sec-director@corp.example.internal",
        "cab_chair": "it-change-manager@corp.example.internal",
        "executing_team": "Network & Perimeter Security Engineering",
        "scheduled_window": {
            "start_time": "2026-11-15T01:00:00Z",
            "end_time": "2026-11-15T03:00:00Z",
            "duration_minutes": 120,
            "timezone": "UTC"
        },
        "systems_impacted": [
            "fw-edge-node01.corp.example.internal (Primary)",
            "fw-edge-node02.corp.example.internal (Secondary Standby)",
            "Corporate Edge IPsec VPN Gateway"
        ],
        "risk_assessment": {
            "scope_score": 3,
            "redundancy_score": 1,
            "reversibility_score": 1,
            "precedent_score": 2,
            "redundancy_notes": "Active-passive stateful HA cluster with zero-loss session failover.",
            "precedent_notes": "Upgraded secondary staging firewall successfully on Nov 10."
        },
        "pre_checks": [
            {
                "description": "Capture active BGP neighbor sessions and routes count",
                "command": "get router info bgp summary",
                "target_host": "fw-edge-node01"
            },
            {
                "description": "Verify HA cluster synchronization status and checksums",
                "command": "diagnose sys ha checksum cluster",
                "target_host": "fw-edge-node01"
            },
            {
                "description": "Create offline system configuration backup to secure TFTP",
                "command": "execute backup config tftp fw-backup-pre-726.cfg 192.0.2.50",
                "target_host": "fw-edge-node01"
            }
        ],
        "implementation_steps": [
            {
                "step_number": 1,
                "action": "Upload firmware image to standby node02 and verify SHA-256 hash",
                "command": "execute restore image tftp fortios-7.2.6.bin 192.0.2.50",
                "executing_engineer": "eng-secops",
                "duration_minutes": 15,
                "target_host": "fw-edge-node02"
            },
            {
                "step_number": 2,
                "action": "Reboot standby node02 into 7.2.6 and monitor post-boot HA rejoin",
                "command": "execute reboot",
                "executing_engineer": "eng-secops",
                "duration_minutes": 15,
                "target_host": "fw-edge-node02"
            },
            {
                "step_number": 3,
                "action": "Initiate graceful HA failover to transfer active traffic to node02",
                "command": "diagnose sys ha reset-uptime",
                "executing_engineer": "eng-secops",
                "duration_minutes": 10,
                "target_host": "fw-edge-node01"
            },
            {
                "step_number": 4,
                "action": "Upgrade node01 to 7.2.6 and confirm cluster re-synchronization",
                "command": "execute restore image tftp fortios-7.2.6.bin 192.0.2.50",
                "executing_engineer": "eng-secops",
                "duration_minutes": 20,
                "target_host": "fw-edge-node01"
            }
        ],
        "rollback_plan": {
            "trigger_conditions": "Continuous ping packet loss > 5% for > 3 minutes, IPsec tunnels fail to renegotiate, or BGP route flapping detected on node02.",
            "decision_cutoff_point": "2026-11-15T02:15:00Z (45 mins prior to window close)",
            "duration_minutes": 20,
            "commands": [
                {
                    "step": 1,
                    "action": "Force cluster failback immediately to node01 running verified 7.0.12",
                    "command": "diagnose sys ha reset-uptime",
                    "target_host": "fw-edge-node02"
                },
                {
                    "step": 2,
                    "action": "Restore pre-change config from TFTP if state is inconsistent",
                    "command": "execute restore config tftp fw-backup-pre-726.cfg 192.0.2.50",
                    "target_host": "fw-edge-node02"
                }
            ]
        },
        "verification_plan": [
            {
                "test_number": 1,
                "description": "Verify HA cluster state and full sync checksum match",
                "command": "diagnose sys ha status"
            },
            {
                "test_number": 2,
                "description": "Confirm all 24 branch IPsec VPN tunnels are established (Phase 2 UP)",
                "command": "diagnose vpn tunnel list | grep 'status=up'"
            },
            {
                "test_number": 3,
                "description": "Execute synthetic HTTP/HTTPS external connectivity tests from DMZ web cluster",
                "command": "curl -Iv --connect-timeout 5 https://login.microsoftonline.com"
            }
        ]
    }


def interactive_interview() -> Dict[str, Any]:
    """Conduct interactive terminal interview to draft an RFC."""
    print("=" * 70)
    print("  ITIL Change Advisory Board (CAB) Interactive RFC Drafter")
    print("=" * 70)
    print("Please answer the following operational questions to build a CAB-ready RFC.\n")

    title = input("Change Title [e.g. Core Switch Firmware Upgrade]: ").strip()
    if not title:
        title = "Production Infrastructure Change"

    justification = input("Business Justification & Problem Driver: ").strip()
    systems = input("Impacted Systems / CIs (comma-separated): ").strip()
    systems_list = [s.strip() for s in systems.split(",") if s.strip()] if systems else ["Core-System-01"]

    window_dur = input("Maintenance Window Duration in Minutes [e.g. 120]: ").strip()
    try:
        window_minutes = int(window_dur) if window_dur else 60
    except ValueError:
        window_minutes = 60

    print("\n--- Implementation Steps ---")
    steps = []
    step_num = 1
    while True:
        action = input(f"Step {step_num} Action Description (or press Enter to finish): ").strip()
        if not action:
            break
        cmd = input(f"Step {step_num} Exact Command / CLI Syntax: ").strip()
        dur = input(f"Step {step_num} Duration in Minutes [e.g. 10]: ").strip()
        try:
            dur_mins = int(dur) if dur else 10
        except ValueError:
            dur_mins = 10
        steps.append({
            "step_number": step_num,
            "action": action,
            "command": cmd,
            "duration_minutes": dur_mins
        })
        step_num += 1

    print("\n--- Rollback & Backout Plan ---")
    trigger = input("Rollback Trigger Conditions [e.g. Latency > 50ms for > 5 mins]: ").strip()
    rb_cmd = input("Rollback Execution Commands: ").strip()
    rb_dur = input("Rollback Execution Duration in Minutes [e.g. 15]: ").strip()
    try:
        rollback_mins = int(rb_dur) if rb_dur else 15
    except ValueError:
        rollback_mins = 15

    print("\n--- Post-Change Verification ---")
    verify_test = input("Primary Health Check / Verification Test Command: ").strip()

    rfc = {
        "rfc_id": f"RFC-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M')}",
        "title": title,
        "business_justification": justification or "Routine operational upgrade and maintenance.",
        "change_category": "NORMAL",
        "lead_engineer": "engineer@corp.example.internal",
        "scheduled_window": {
            "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "duration_minutes": window_minutes
        },
        "systems_impacted": systems_list,
        "pre_checks": [
            {"description": "Record baseline metrics prior to change", "command": "netstat -an | grep LISTEN"}
        ],
        "implementation_steps": steps if steps else [
            {"step_number": 1, "action": "Apply targeted change", "command": "systemctl restart target", "duration_minutes": 10}
        ],
        "rollback_plan": {
            "trigger_conditions": trigger or "Health checks fail post-deployment.",
            "decision_cutoff_point": "30 mins before window close",
            "duration_minutes": rollback_mins,
            "commands": [{"step": 1, "action": "Revert to pre-change state", "command": rb_cmd or "systemctl restart target"}]
        },
        "verification_plan": [
            {"test_number": 1, "description": "Verify service health", "command": verify_test or "curl -Iv http://localhost"}
        ]
    }

    return rfc


def main():
    parser = argparse.ArgumentParser(description="Draft and evaluate ITIL CAB Request for Change (RFC) packages.")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive interview wizard in console")
    parser.add_argument("--sample", action="store_true", help="Output a clean, reference CAB RFC JSON template")
    parser.add_argument("--input", "-i", default=None, help="Input draft RFC JSON or outline")
    parser.add_argument("--output", "-o", default=None, help="Output RFC JSON path")
    parser.add_argument("--report", "-r", default=None, help="Output CAB Audit Markdown report path")
    parser.add_argument("--sanitize", action="store_true", help="Apply Rule 4 client-side data sanitization")
    args = parser.parse_args()

    if args.sample:
        sample_rfc = generate_sample_rfc()
        if args.sanitize:
            sample_rfc = sanitize_bundle(sample_rfc)
        out = json.dumps(sample_rfc, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"Sample RFC saved to: {args.output}")
        else:
            print(out)
        return

    if args.interactive:
        rfc_data = interactive_interview()
    elif args.input:
        with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
            rfc_data = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)

    if args.sanitize:
        rfc_data = sanitize_bundle(rfc_data)

    # Perform immediate readiness audit
    audit = audit_rfc(rfc_data)
    md_report = format_markdown_report(audit, rfc_data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(rfc_data, f, indent=2)
        print(f"RFC package written to: {args.output}")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"CAB readiness report written to: {args.report}")
    elif not args.output:
        print("\n" + md_report)

    print(f"\n[CAB Audit Result] Score: {audit['readiness_score_pct']}% | Verdict: {audit['recommendation']}")


if __name__ == "__main__":
    main()

