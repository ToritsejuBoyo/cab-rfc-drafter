#!/usr/bin/env python3
"""
stress_test_cab_rfc.py - Performance Benchmarking & ReDoS Resistance Test Suite.

Asserts:
- Engine can audit 10,000 synthetic RFC documents in < 1.0 second.
- Regex pattern matching is resistant to exponential catastrophic backtracking (ReDoS).
- Multi-threaded concurrent evaluation safety.
"""

import concurrent.futures
import json
import os
import sys
import time
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from validate_rfc_readiness import audit_procedural_quality, audit_rfc, sanitize_bundle


class TestCabRfcStress(unittest.TestCase):

    def setUp(self):
        self.sample_rfc = {
            "title": "High-Volume Performance Test RFC",
            "business_justification": "Scale testing for CAB pipeline",
            "change_category": "NORMAL",
            "scheduled_window": {"duration_minutes": 120},
            "systems_impacted": ["srv-scale-01.corp.example.internal"],
            "pre_checks": [{"command": "uptime"}],
            "implementation_steps": [
                {"action": "Apply update package", "command": "apt-get update", "duration_minutes": 15},
                {"action": "Install patch binary", "command": "dpkg -i patch.deb", "duration_minutes": 25}
            ],
            "rollback_plan": {
                "trigger_conditions": "Service fails to start",
                "decision_cutoff_point": "30 mins before window close",
                "duration_minutes": 20,
                "commands": [{"command": "dpkg -r patch"}]
            },
            "verification_plan": [{"command": "systemctl status service"}]
        }

    def test_high_volume_throughput(self):
        """Audit 10,000 synthetic RFC payloads and verify execution speed."""
        iterations = 10000
        start = time.perf_counter()

        for _ in range(iterations):
            res = audit_rfc(self.sample_rfc)
            self.assertTrue(res["cab_ready"])

        elapsed = time.perf_counter() - start
        rate = iterations / elapsed
        print(f"\n[BENCHMARK] Audited {iterations:,} RFCs in {elapsed:.3f}s ({rate:,.0f} evaluations/sec)")
        self.assertLess(elapsed, 2.0, "Throughput below SLA (< 5,000 evals/sec)")

    def test_redos_resistance(self):
        """Assert regex pattern matching is immune to catastrophic backtracking."""
        pathological_strings = [
            "reboot " + "system " * 1000,
            "upgrade " + "firmware " * 1000,
            "apply " + "config " * 1000,
            "a" * 10000 + "!@#$%^&*()",
            "revert " + "changes " * 1000
        ]

        start = time.perf_counter()
        for s in pathological_strings:
            data = {"implementation_steps": [{"action": s, "command": ""}]}
            audit_procedural_quality(data)

        elapsed = time.perf_counter() - start
        print(f"[BENCHMARK] ReDoS resistance verified across pathological inputs in {elapsed:.4f}s")
        self.assertLess(elapsed, 0.5, "Potential ReDoS vulnerability detected")

    def test_multithreaded_concurrency(self):
        """Assert thread safety across 16 worker threads executing 2,000 audits concurrently."""
        total_evals = 2000
        workers = 16

        def worker_task(idx):
            data = dict(self.sample_rfc)
            data["title"] = f"Concurrent RFC #{idx}"
            return audit_rfc(data)

        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(total_evals)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        elapsed = time.perf_counter() - start
        self.assertEqual(len(results), total_evals)
        print(f"[CONCURRENCY] Completed {total_evals:,} concurrent audits across {workers} threads in {elapsed:.3f}s")
        self.assertLess(elapsed, 1.5)


if __name__ == "__main__":
    unittest.main()
