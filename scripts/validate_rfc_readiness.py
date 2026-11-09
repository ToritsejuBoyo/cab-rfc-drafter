#!/usr/bin/env python3
"""
validate_rfc_readiness.py - ITIL 4 Change Advisory Board (CAB) RFC Validation Engine.

Audits Request for Change (RFC) documents for mandatory section completeness,
4-dimension ITIL risk scoring, maintenance window arithmetic feasibility,
Go/No-Go decision cutoff viability, and procedural vagueness.

Enforces Rule 3 (Zero 3rd-party dependencies, strictly standard library)
and Rule 4 (Client-side SHA-256 data sanitization).
"""

import argparse
import datetime
import hashlib
import json
import math
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_SECTIONS = [
    "title",
    "business_justification",
    "change_category",
    "scheduled_window",
    "systems_impacted",
    "pre_checks",
    "implementation_steps",
    "rollback_plan",
    "verification_plan"
]

VAGUE_STEP_PATTERNS = [
    r"^(reboot|restart)(\s+system|\s+server)?$",
    r"^(upgrade|patch)(\s+firmware|\s+software)?$",
    r"^run\s+script$",
    r"^apply\s+config(uration)?$",
    r"^test\s+(system|service)?$",
    r"^undo(\s+all)?$",
    r"^revert(\s+changes)?$"
]

# RFC 5737 documentation test prefixes
TEST_IP_MAP: Dict[str, str] = {}
TEST_IP_COUNTER = 1


def hash_identifier(val: str, prefix: str = "ID") -> str:
    """Generate deterministic SHA-256 masked identifier (idempotent)."""
    if not val:
        return ""
    if val.startswith(f"{prefix}-") and len(val) == len(prefix) + 9:
        return val
    h = hashlib.sha256(val.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{h}"


def sanitize_ip(ip_str: str) -> str:
    """Map IPv4 addresses to RFC 5737 test subnets (192.0.2.x) (idempotent)."""
    global TEST_IP_COUNTER
    if ip_str.startswith("192.0.2."):
        return ip_str
    if ip_str not in TEST_IP_MAP:
        TEST_IP_MAP[ip_str] = f"192.0.2.{TEST_IP_COUNTER % 250 + 1}"
        TEST_IP_COUNTER += 1
    return TEST_IP_MAP[ip_str]


def sanitize_text(text: str) -> str:
    """Mask emails, hostnames, IPs, and internal domains (idempotent)."""
    if not isinstance(text, str):
        return text

    # Mask email addresses
    def _replace_email(m):
        addr = m.group(0)
        if addr.startswith("eng-") and addr.endswith("@corp.example.internal"):
            return addr
        h = hashlib.sha256(addr.encode()).hexdigest()[:6]
        return f"eng-{h}@corp.example.internal"

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    text = re.sub(email_pattern, _replace_email, text)

    # Mask IPv4 addresses
    ipv4_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    text = re.sub(ipv4_pattern, lambda m: sanitize_ip(m.group(0)), text)

    # Mask standard FQDNs ending in internal or corp
    def _replace_fqdn(m):
        fqdn = m.group(0)
        if fqdn.startswith("node-") and fqdn.endswith(".corp.example.internal"):
            return fqdn
        h = hashlib.sha256(fqdn.encode()).hexdigest()[:6]
        return f"node-{h}.corp.example.internal"

    fqdn_pattern = r"\b[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.(?:corp|local|internal|lan)\b"
    text = re.sub(fqdn_pattern, _replace_fqdn, text)

    return text


def sanitize_bundle(data: Any) -> Any:
    """Recursively sanitize dictionary or list telemetry data."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if k in ("lead_engineer", "peer_reviewer", "service_owner", "cab_chair", "executing_engineer"):
                if isinstance(v, str):
                    sanitized[k] = hash_identifier(v, "ENG")
                else:
                    sanitized[k] = v
            elif k in ("rfc_id", "change_id"):
                if isinstance(v, str):
                    sanitized[k] = hash_identifier(v, "RFC")
                else:
                    sanitized[k] = v
            else:
                sanitized[k] = sanitize_bundle(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_bundle(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    else:
        return data


def parse_duration_minutes(val: Any) -> int:
    """Extract integer minutes from integers, floats, or strings like '45 mins' or '2h'."""
    if isinstance(val, (int, float)):
        return max(0, int(val))
    if not val or not isinstance(val, str):
        return 0

    s = val.strip().lower()
    # Check if negative
    if s.startswith("-"):
        return 0

    # Check for hours e.g. "2h" or "2 hours"
    m_h = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:h|hr|hour|hours)", s)
    if m_h:
        return max(0, int(float(m_h.group(1)) * 60))

    # Check for minutes e.g. "45m" or "45 mins"
    m_m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:m|min|mins|minute|minutes)", s)
    if m_m:
        return max(0, int(float(m_m.group(1))))

    # Direct integer string
    try:
        return max(0, int(float(s)))
    except (ValueError, TypeError):
        return 0


def calculate_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate 4-dimension ITIL change risk score and tier."""
    risk_info = data.get("risk_assessment", {})
    if not isinstance(risk_info, dict):
        risk_info = {}

    # Dimensions: 1=Low, 2=Medium, 3=High
    scope = risk_info.get("scope_score")
    redundancy = risk_info.get("redundancy_score")
    reversibility = risk_info.get("reversibility_score")
    precedent = risk_info.get("precedent_score")

    # Fallback heuristic calculation if not provided explicitly
    if scope is None:
        scope_text = str(data.get("systems_impacted", "")).lower() + " " + str(data.get("business_justification", "")).lower()
        if any(term in scope_text for term in ["all", "customer", "company-wide", "production core", "global", "multi-tenant"]):
            scope = 3
        elif any(term in scope_text for term in ["department", "branch", "internal team"]):
            scope = 2
        else:
            scope = 1

    if redundancy is None:
        redundancy_text = str(data.get("systems_impacted", "")).lower() + " " + str(risk_info.get("redundancy_notes", "")).lower()
        if any(term in redundancy_text for term in ["standalone", "spof", "single point", "non-redundant", "primary db"]):
            redundancy = 3
        elif any(term in redundancy_text for term in ["cluster", "failover", "active-passive", "standby"]):
            redundancy = 2
        else:
            redundancy = 1

    if reversibility is None:
        rollback_data = data.get("rollback_plan", {})
        if not rollback_data:
            reversibility = 3
        else:
            r_text = json.dumps(rollback_data).lower()
            if any(term in r_text for term in ["irreversible", "drop", "truncate", "flash", "cannot revert"]):
                reversibility = 3
            elif any(term in r_text for term in ["snapshot", "toggle", "instant", "zero downtime"]):
                reversibility = 1
            else:
                reversibility = 2

    if precedent is None:
        prec_text = str(data.get("change_category", "")).lower() + " " + str(risk_info.get("precedent_notes", "")).lower()
        if any(term in prec_text for term in ["first time", "novel", "new architecture", "major version"]):
            precedent = 3
        elif any(term in prec_text for term in ["standard", "routine", "weekly", "recurrent"]):
            precedent = 1
        else:
            precedent = 2

    # Clamp scores between 1 and 3
    scope = max(1, min(3, int(scope)))
    redundancy = max(1, min(3, int(redundancy)))
    reversibility = max(1, min(3, int(reversibility)))
    precedent = max(1, min(3, int(precedent)))

    total_score = scope + redundancy + reversibility + precedent

    # Automatic high-risk escalators
    escalations = []
    rollback_plan = data.get("rollback_plan", {})
    if not rollback_plan or (isinstance(rollback_plan, dict) and not rollback_plan.get("commands")):
        escalations.append("Automatic High-Risk: Zero documented rollback commands.")
        total_score = max(total_score, 10)

    # Check for destructive SQL
    impl_text = json.dumps(data.get("implementation_steps", [])).lower()
    if any(kw in impl_text for kw in ["drop table", "drop database", "truncate", "rm -rf /"]):
        escalations.append("Automatic High-Risk: Destructive command detected in implementation plan.")
        total_score = max(total_score, 10)

    if total_score <= 6:
        tier = "LOW"
        recommended_cat = "STANDARD"
    elif total_score <= 9:
        tier = "MEDIUM"
        recommended_cat = "NORMAL"
    else:
        tier = "HIGH"
        recommended_cat = "MAJOR"

    return {
        "dimensions": {
            "scope_score": scope,
            "redundancy_score": redundancy,
            "reversibility_score": reversibility,
            "precedent_score": precedent
        },
        "total_risk_score": total_score,
        "risk_tier": tier,
        "recommended_category": recommended_cat,
        "escalations": escalations
    }


def validate_timing_headroom(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate implementation time, rollback time, and window feasibility."""
    window = data.get("scheduled_window", {})
    if not isinstance(window, dict):
        window = {}

    window_duration = parse_duration_minutes(window.get("duration_minutes", 0))

    # Calculate implementation time
    impl_steps = data.get("implementation_steps", [])
    total_impl_mins = 0
    if isinstance(impl_steps, list):
        for s in impl_steps:
            if isinstance(s, dict):
                total_impl_mins += parse_duration_minutes(s.get("duration_minutes", 0))
            elif isinstance(s, (int, float)):
                total_impl_mins += int(s)

    # Calculate rollback duration
    rollback = data.get("rollback_plan", {})
    rollback_mins = 0
    if isinstance(rollback, dict):
        rollback_mins = parse_duration_minutes(rollback.get("duration_minutes", 0))

    total_active_mins = total_impl_mins + rollback_mins
    headroom_mins = window_duration - total_active_mins
    headroom_pct = round((headroom_mins / window_duration) * 100, 1) if window_duration > 0 else 0.0

    defects = []
    if window_duration <= 0:
        defects.append("Maintenance window duration is 0 or not specified.")
    elif total_active_mins > window_duration:
        defects.append(
            f"Guaranteed Window Overrun: Implementation ({total_impl_mins}m) + Rollback ({rollback_mins}m) "
            f"= {total_active_mins}m exceeds allocated window of {window_duration}m."
        )
    elif headroom_pct < 15.0:
        defects.append(
            f"Tight Maintenance Window: Safety headroom buffer is only {headroom_mins}m ({headroom_pct}%). "
            f"CAB guidelines require at least 15% contingency buffer."
        )

    # Validate Go/No-Go Decision Cutoff Point
    cutoff = None
    if isinstance(rollback, dict):
        cutoff = rollback.get("decision_cutoff_point") or rollback.get("decision_cutoff_time")
    if not cutoff and window_duration > 0:
        defects.append("Missing explicit Go / No-Go Decision Cutoff Point in rollback plan.")

    return {
        "window_duration_minutes": window_duration,
        "total_implementation_minutes": total_impl_mins,
        "rollback_duration_minutes": rollback_mins,
        "total_active_minutes": total_active_mins,
        "headroom_buffer_minutes": headroom_mins,
        "headroom_buffer_pct": headroom_pct,
        "decision_cutoff_point": cutoff,
        "timing_feasible": total_active_mins <= window_duration and window_duration > 0,
        "timing_defects": defects
    }


def audit_procedural_quality(data: Dict[str, Any]) -> List[str]:
    """Inspect implementation, rollback, and verification steps for vagueness and quality gaps."""
    defects = []

    # Check pre-checks
    pre_checks = data.get("pre_checks")
    if not pre_checks or (isinstance(pre_checks, list) and len(pre_checks) == 0):
        defects.append("Pre-implementation baseline checks are missing or empty.")

    # Check implementation steps
    impl_steps = data.get("implementation_steps")
    if not impl_steps or not isinstance(impl_steps, list) or len(impl_steps) == 0:
        defects.append("Implementation steps are missing or empty.")
    else:
        for idx, step in enumerate(impl_steps, 1):
            if isinstance(step, dict):
                desc = str(step.get("action", "") or step.get("description", "")).strip()
                cmd = str(step.get("command", "")).strip()
            else:
                desc = str(step).strip()
                cmd = ""

            # Check for vague action descriptions
            combined = f"{desc} {cmd}".strip().lower()
            if len(combined.split()) < 3 and not cmd:
                defects.append(f"Step {idx} is vague ('{desc}'). Must include explicit commands or procedural detail.")
            for pattern in VAGUE_STEP_PATTERNS:
                if re.match(pattern, combined):
                    defects.append(f"Step {idx} contains generic placeholder ('{desc}'). Detail exact syntax, targets, and expected outputs.")
                    break

    # Check rollback plan
    rollback = data.get("rollback_plan")
    if not rollback:
        defects.append("Rollback plan is completely absent.")
    elif isinstance(rollback, dict):
        trigger = str(rollback.get("trigger_conditions") or rollback.get("trigger") or "").strip()
        cmds = rollback.get("commands") or rollback.get("steps")
        if not trigger:
            defects.append("Rollback plan lacks objective trigger conditions (e.g. latency > 50ms for > 5m).")
        if not cmds or (isinstance(cmds, list) and len(cmds) == 0):
            defects.append("Rollback plan lacks executable backout commands or steps.")
    else:
        defects.append("Rollback plan must be a structured dictionary with trigger, commands, and duration.")

    # Check verification plan
    verify = data.get("verification_plan")
    if not verify or (isinstance(verify, list) and len(verify) == 0):
        defects.append("Post-change verification plan is missing or empty.")

    return defects


def audit_rfc(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform full 5-layer RFC readiness audit and scoring."""
    title = data.get("title", "Untitled Request for Change")
    missing_sections = []

    for section in MANDATORY_SECTIONS:
        val = data.get(section)
        if val is None or (isinstance(val, (list, dict, str)) and len(val) == 0):
            missing_sections.append(section)

    risk_result = calculate_risk(data)
    timing_result = validate_timing_headroom(data)
    quality_defects = audit_procedural_quality(data)

    all_defects = []
    if missing_sections:
        all_defects.append(f"Missing mandatory sections: {', '.join(missing_sections)}")
    all_defects.extend(timing_result["timing_defects"])
    all_defects.extend(quality_defects)
    all_defects.extend(risk_result["escalations"])

    # Score calculation
    # Base: 50% from sections present (9 sections)
    section_pct = ((len(MANDATORY_SECTIONS) - len(missing_sections)) / len(MANDATORY_SECTIONS)) * 50.0

    # Timing feasibility: 25%
    timing_pct = 25.0 if timing_result["timing_feasible"] and len(timing_result["timing_defects"]) == 0 else (
        10.0 if timing_result["timing_feasible"] else 0.0
    )

    # Procedural quality: 25% minus penalties for quality defects
    quality_penalties = min(25.0, len(quality_defects) * 5.0)
    quality_pct = max(0.0, 25.0 - quality_penalties)

    readiness_score = round(section_pct + timing_pct + quality_pct, 1)
    cab_ready = (readiness_score >= 85.0) and (len(missing_sections) == 0) and timing_result["timing_feasible"] and (len(quality_defects) == 0)

    recommendation = "Approved for CAB Submission" if cab_ready else (
        "Conditional / Minor Revisions Required" if readiness_score >= 70.0 else "Rejected: Critical RFC Deficiencies"
    )

    return {
        "rfc_title": title,
        "readiness_score_pct": readiness_score,
        "cab_ready": cab_ready,
        "recommendation": recommendation,
        "missing_mandatory_sections": missing_sections,
        "risk_assessment": risk_result,
        "maintenance_window_audit": timing_result,
        "procedural_defects": quality_defects,
        "all_defects": all_defects
    }


def format_markdown_report(result: Dict[str, Any], data: Dict[str, Any]) -> str:
    """Generate professional Markdown CAB Evaluation Report."""
    risk = result["risk_assessment"]
    timing = result["maintenance_window_audit"]

    lines = [
        f"# CAB Readiness Evaluation: {result['rfc_title']}",
        "",
        "## Executive Summary",
        f"- **Readiness Score:** {result['readiness_score_pct']}%",
        f"- **CAB Recommendation:** **{result['recommendation'].upper()}**",
        f"- **CAB Ready:** `{'YES' if result['cab_ready'] else 'NO'}`",
        f"- **Calculated Risk Tier:** **{risk['risk_tier']} RISK** (Score: {risk['total_risk_score']}/12)",
        f"- **Recommended Change Category:** `{risk['recommended_category']}`",
        "",
        "---",
        "",
        "## Risk Assessment Breakdown",
        "| Risk Dimension | Score (1-3) | Classification Criteria |",
        "| :--- | :--- | :--- |",
        f"| **User Impact Scope** | {risk['dimensions']['scope_score']} | 1=Internal IT, 2=Dept, 3=Enterprise |",
        f"| **Service Redundancy** | {risk['dimensions']['redundancy_score']} | 1=Active-Active, 2=Cluster/Failover, 3=SPOF |",
        f"| **Reversibility** | {risk['dimensions']['reversibility_score']} | 1=Instant (<5m), 2=Tested (<20m), 3=Irreversible/Complex |",
        f"| **Operational Precedent** | {risk['dimensions']['precedent_score']} | 1=Standard/Routine, 2=Staging Tested, 3=Novel/First-time |",
        f"| **Total Risk Score** | **{risk['total_risk_score']} / 12** | **Tier: {risk['risk_tier']}** |",
        ""
    ]

    if risk["escalations"]:
        lines.append("### Automatic Risk Escalations")
        for esc in risk["escalations"]:
            lines.append(f"- {esc}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Maintenance Window & Headroom Audit",
        "| Timing Metric | Duration | Evaluation Note |",
        "| :--- | :--- | :--- |",
        f"| **Scheduled Window Duration** | {timing['window_duration_minutes']} mins | Total approved outage/change window |",
        f"| **Planned Implementation Time** | {timing['total_implementation_minutes']} mins | Sum of all implementation steps |",
        f"| **Estimated Rollback Time** | {timing['rollback_duration_minutes']} mins | Time required to execute complete backout |",
        f"| **Total Active Duration** | {timing['total_active_minutes']} mins | Implementation + Rollback duration |",
        f"| **Safety Headroom Buffer** | {timing['headroom_buffer_minutes']} mins ({timing['headroom_buffer_pct']}%) | Target buffer $\\ge 15\\%$ |",
        f"| **Go / No-Go Decision Cutoff** | `{timing['decision_cutoff_point'] or 'NOT SPECIFIED'}` | Mandatory operational deadline |",
        ""
    ])

    if result["all_defects"]:
        lines.extend([
            "---",
            "",
            "## Identified Defects & Required Remediations",
            "The following items must be resolved before this RFC can be approved by the CAB:"
        ])
        for idx, defect in enumerate(result["all_defects"], 1):
            lines.append(f"{idx}. {defect}")
        lines.append("")
    else:
        lines.extend([
            "---",
            "",
            "## Audit Findings",
            "Zero defects identified. All mandatory ITIL 4 sections, timing constraints, and rollback procedures are fully satisfied.",
            ""
        ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit and validate RFC document readiness for Change Advisory Board (CAB).")
    parser.add_argument("--input", "-i", required=True, help="Path to RFC JSON file")
    parser.add_argument("--output", "-o", default=None, help="Output file path (JSON or Markdown)")
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--sanitize", action="store_true", help="Sanitize PII, emails, hostnames, and IP addresses")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
            raw_data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error loading input file '{args.input}': {e}\n")
        sys.exit(1)

    if args.sanitize:
        data = sanitize_bundle(raw_data)
    else:
        data = raw_data

    audit_result = audit_rfc(data)

    if args.format == "markdown":
        output_content = format_markdown_report(audit_result, data)
    else:
        output_content = json.dumps(audit_result, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Audit report saved to: {args.output}")
    else:
        print(output_content)

    # Return exit code 0 if CAB ready or conditionally ready, 2 if critical defects
    if not audit_result["cab_ready"] and audit_result["readiness_score_pct"] < 60.0:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
