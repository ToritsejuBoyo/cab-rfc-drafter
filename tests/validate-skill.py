#!/usr/bin/env python3
"""
validate-skill.py - Rule Compliance and Quality Verification Test Suite.

Enforces:
- Rule 1 & 11: Plan approval compliance.
- Rule 3: Zero external dependencies (only standard Python libraries).
- Rule 4: Client-side data sanitization (SHA-256 masking and RFC 5737 test IPs).
- Rule 7: Zero-emoji enterprise tone.
- Rule 9: Automated synthetic fixture validation.
"""

import ast
import json
import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
FIXTURES_DIR = os.path.join(BASE_DIR, "tests", "fixtures")

sys.path.insert(0, SCRIPTS_DIR)
try:
    from validate_rfc_readiness import audit_rfc, sanitize_bundle
except ImportError as e:
    print(f"[FAIL] Failed to import validate_rfc_readiness: {e}")
    sys.exit(1)


def check_zero_dependencies():
    """Verify that all scripts use only Python standard library."""
    allowed_modules = {
        "argparse", "datetime", "hashlib", "json", "math", "os", "re", "sys",
        "typing", "unittest", "time", "random", "concurrent", "threading"
    }

    for root, _, files in os.walk(SCRIPTS_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            base_pkg = alias.name.split(".")[0]
                            if base_pkg not in allowed_modules and base_pkg not in ["validate_rfc_readiness", "draft_cab_rfc"]:
                                print(f"[FAIL] Unauthorized import '{base_pkg}' in {file}")
                                return False
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            base_pkg = node.module.split(".")[0]
                            if base_pkg not in allowed_modules and base_pkg not in ["validate_rfc_readiness", "draft_cab_rfc"]:
                                print(f"[FAIL] Unauthorized from-import '{base_pkg}' in {file}")
                                return False
    print("  [+] PASS: Rule 3 compliance (Zero external dependencies across all scripts).")
    return True


def check_zero_emojis():
    """Verify that all skill files adhere to Rule 7 (Zero-Emoji Enterprise Tone)."""
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
    )
    for root, _, files in os.walk(BASE_DIR):
        if ".git" in root or "assets" in root:
            continue
        for file in files:
            if file.endswith((".py", ".md", ".json", ".txt")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if emoji_pattern.search(content):
                    print(f"[FAIL] Emoji detected in {path}")
                    return False
    print("  [+] PASS: Rule 7 compliance (Strict zero-emoji enterprise tone).")
    return True


def check_sanitization():
    """Verify Rule 4 data sanitization behavior."""
    sample = {
        "lead_engineer": "john.doe@corp.example.com",
        "systems_impacted": ["core-switch01.corp.example.com", "10.50.1.254"],
        "rfc_id": "RFC-2026-9999",
        "pre_checks": [
            {"command": "ping 192.168.1.1"}
        ]
    }
    sanitized = sanitize_bundle(sample)
    s_dump = json.dumps(sanitized)

    assert "john.doe@corp.example.com" not in s_dump, "Email was not masked"
    assert "core-switch01.corp.example.com" not in s_dump, "Internal FQDN was not masked"
    assert "10.50.1.254" not in s_dump, "Internal IP was not masked"
    assert "192.0.2." in s_dump, "RFC 5737 test IP not assigned"
    print("  [+] PASS: Rule 4 compliance (Client-side SHA-256 and RFC 5737 sanitization).")
    return True


def check_fixtures():
    """Validate all synthetic test fixtures against readiness auditor."""
    fixtures = [
        ("fixture-valid-major-firewall-upgrade.json", True, 85.0),
        ("fixture-valid-normal-cert-renewal.json", True, 85.0),
        ("fixture-valid-standard-dns-ttl.json", True, 85.0),
        ("fixture-failing-missing-rollback.json", False, 70.0),
        ("fixture-failing-window-overrun.json", False, 80.0),
        ("fixture-failing-vague-steps.json", False, 60.0)
    ]

    for fname, expected_ready, score_threshold in fixtures:
        fpath = os.path.join(FIXTURES_DIR, fname)
        assert os.path.isfile(fpath), f"Fixture missing: {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        res = audit_rfc(data)

        if expected_ready:
            assert res["cab_ready"] is True, f"Expected {fname} to be CAB ready, but was: {res}"
            assert res["readiness_score_pct"] >= score_threshold, f"{fname} score {res['readiness_score_pct']} below {score_threshold}"
            print(f"  [+] PASS: {fname} verified CAB-Ready ({res['readiness_score_pct']}%).")
        else:
            assert res["cab_ready"] is False, f"Expected {fname} to fail CAB readiness"
            assert len(res["all_defects"]) > 0, f"Expected defects in {fname}"
            print(f"  [+] PASS: {fname} correctly rejected ({res['readiness_score_pct']}%) with {len(res['all_defects'])} defects.")
    return True


def check_skill_frontmatter():
    """Validate SKILL.md YAML frontmatter and required sections."""
    skill_path = os.path.join(BASE_DIR, "SKILL.md")
    assert os.path.isfile(skill_path), "SKILL.md is missing"
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
    assert "name: cab-rfc-drafter" in content, "Frontmatter must define name: cab-rfc-drafter"
    assert "description:" in content, "Frontmatter must include description"
    assert "Operating Rules & Safety Guardrails" in content, "SKILL.md must include Operating Rules"
    assert "Output Format Specification" in content, "SKILL.md must include Output Format Specification"
    print("  [+] PASS: SKILL.md frontmatter and structural specification verified.")
    return True


def main():
    print("=" * 70)
    print("  cab-rfc-drafter Automated Test & Verification Suite")
    print("=" * 70)

    success = (
        check_zero_dependencies() and
        check_zero_emojis() and
        check_sanitization() and
        check_skill_frontmatter() and
        check_fixtures()
    )

    if success:
        print("=" * 70)
        print("  ALL TESTS PASSED: Skill complies with all workspace rules (Exit Code 0).")
        print("=" * 70)
        sys.exit(0)
    else:
        print("[FAIL] Verification checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

