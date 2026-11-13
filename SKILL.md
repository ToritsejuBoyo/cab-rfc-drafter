---
name: cab-rfc-drafter
description: >-
  Conducts structured change management interviews, audits proposed maintenance windows,
  calculates 4-dimension ITIL risk scores, and drafts audit-ready Change Advisory Board (CAB)
  Request for Change (RFC) packages with explicit rollback plans. Use whenever drafting an RFC,
  preparing production changes for CAB review, auditing change risk, or evaluating maintenance
  window headroom.
license: Apache-2.0
version: 1.0.0
metadata:
  standard: agentskills.io
  dependencies: none (Python standard library only)
  access: read-only collectors; no state is modified on target systems
---

# Change Advisory Board (CAB) Risk & Rollback RFC Drafter (`cab-rfc-drafter`)

## Purpose & Target Roles
Designed for **Change Managers, Release Managers, Systems Engineers, DevOps/SRE Leads, and IT Infrastructure Consultants**.

In enterprise IT operations, up to 75% of major outages (P1/P2) originate from poorly planned or improperly vetted production changes. Infrastructure engineers routinely submit vague, rushed Change Requests lacking concrete backout commands, realistic maintenance windows, or pre-change baseline checks. This skill pairs an interactive CLI interview wizard (`scripts/draft_cab_rfc.py`) with a deterministic 5-layer validation engine (`scripts/validate_rfc_readiness.py`) to eliminate change rejection loops and guarantee that every approved RFC is technically sound and CAB-ready.

## Operating Rules & Safety Guardrails
1. **Read-Only First Principle:** All companion validation scripts and telemetry collectors are strictly read-only. Never execute or propose destructive commands or state-mutating actions without explicit human approval and documented rollback steps.
2. **Mandatory Rollback Criteria:** An RFC cannot be approved without an explicit, time-bounded rollback plan, executable backout commands, and objective trigger conditions (e.g., "If ping packet loss exceeds 5% for > 3 minutes, initiate rollback").
3. **Temporal Window Discipline:** The maintenance window duration must strictly exceed the planned implementation time plus the rollback duration with at least a 15% safety buffer ($\text{Headroom} \ge 15\%$).
4. **Zero Secrets & Data Sanitization:** Never collect credentials, API tokens, passwords, or private keys. Client-side `--sanitize` mode masks engineer emails, internal hostnames, and RFC 5737 test IP addresses.
5. **Propose, Do Not Apply:** Always propose technical changes for human review and CAB evaluation. Never apply configuration changes autonomously.

---

## Step 1: Telemetry Acquisition & Pre-Flight Checks

Determine how the engineer or change owner is providing change telemetry:

### Mode A: Automated RFC Readiness Audit (Recommended)
If the engineer has an existing draft RFC in JSON format:
```bash
python3 ./scripts/validate_rfc_readiness.py --input draft_change.json --format markdown --sanitize
```
Examine the calculated readiness score ($\ge 85\%$ required for CAB submission), risk tier, and identified defects.

### Mode B: Interactive Engineer Interview Wizard
If an engineer needs to draft a change proposal from scratch, execute the interactive interview wizard:
```bash
python3 ./scripts/draft_cab_rfc.py --interactive --output proposed_rfc.json --report cab_readiness_report.md
```
Answer the guided questions regarding title, justification, impacted CIs, window duration, step durations, and rollback commands.

### Mode C: Reference Template Generation
To generate a clean, audit-compliant starter JSON template conforming to ITIL 4 standards:
```bash
python3 ./scripts/draft_cab_rfc.py --sample --output starter_rfc.json
```

---

## Step 2: 5-Domain Diagnostic & Analysis Workflow

Execute the structured RFC analysis across five sequential domains:

### Domain 1: Schema & Mandatory Completeness Verification
1. Inspect the input RFC for the 9 mandatory ITIL sections:
   - `title`, `business_justification`, `change_category`, `scheduled_window`, `systems_impacted`, `pre_checks`, `implementation_steps`, `rollback_plan`, `verification_plan`.
2. Reject immediately if critical sections (implementation steps, rollback plan, verification tests) are absent.

### Domain 2: 4-Dimension ITIL Risk Scoring & Automatic Escalators
1. Calculate the 4-dimension risk score using `references/cab-risk-rubric.md`:
   - **User Impact Scope (1–3 pts):** 1 = Internal IT (< 10 users); 2 = Departmental (10–250 users); 3 = Enterprise / Customer-facing.
   - **Service Redundancy (1–3 pts):** 1 = Active-Active HA; 2 = Failover cluster (< 30s pause); 3 = Standalone / SPOF.
   - **Reversibility (1–3 pts):** 1 = Instant (< 5m); 2 = Tested (< 20m); 3 = Irreversible / Complex.
   - **Operational Precedent (1–3 pts):** 1 = Standard routine; 2 = Tested in staging; 3 = Novel / First-time.
2. Sum the scores ($4 \le \text{Total Score} \le 12$):
   - **4–6 pts:** **Low Risk (Standard Change)**.
   - **7–9 pts:** **Medium Risk (Normal Change)**.
   - **10–12 pts:** **High Risk (Major Change)**.
3. Check for Automatic High-Risk Escalators:
   - Zero documented rollback commands -> Automatically escalate to High Risk ($Score \ge 10$).
   - Destructive commands detected (`DROP TABLE`, `TRUNCATE`, `rm -rf`) -> Automatically escalate to High Risk.

### Domain 3: Temporal Maintenance Window & Cutoff Arithmetic
1. Evaluate window headroom using `references/maintenance-window-guidelines.md`:
   $$\text{Total Active Duration} = \sum T_{\text{impl}} + T_{\text{rollback}}$$
   $$\text{Headroom Buffer} = T_{\text{window}} - \text{Total Active Duration}$$
2. Assert $\text{Total Active Duration} \le T_{\text{window}}$. If active duration exceeds window duration, flag **CRITICAL DEFECT: Guaranteed Maintenance Window Overrun**.
3. Assert that $\text{Headroom Buffer} \ge 15\% \times T_{\text{window}}$. If buffer is $< 15\%$, flag **Warning: Tight Maintenance Window**.
4. Validate that the **Go / No-Go Decision Cutoff Point** is scheduled before:
   $$\text{Cutoff Timestamp} \le \text{Window End Time} - T_{\text{rollback}} - 10\text{ minutes}$$

### Domain 4: Blast-Radius & Dependency Verification
1. Inspect `systems_impacted` to ensure all affected Configuration Items (CIs), VIPs, and hostnames are enumerated.
2. Evaluate downstream dependencies:
   - DNS TTL caching expiration prior to cutover.
   - Database connection draining and active session timeouts.
   - Upstream firewall and VPN state table sync.
3. Confirm stakeholder communication plan (Service Desk notification, escalation bridge, customer notices).

### Domain 5: Procedural Quality & Vagueness Auditing
1. Inspect implementation and rollback steps for generic placeholders (`reboot`, `upgrade firmware`, `run script`, `apply config`).
2. Require every operational step to detail:
   - Executable command line syntax.
   - Target hostname or IP.
   - Estimated step duration in minutes.
   - Expected positive response / terminal output.

---

## Step 3: Decision Points & Escalation Matrix

Evaluate the overall audit findings against the operational decision matrix:

- **Decision Point A (Standard Change Pre-Approval):**
  - *Criteria:* Risk Score 4–6, proven operational precedent, zero downtime, reversible in < 5m.
  - *Action:* Recommend delegated approval to peer engineer without full CAB review.
- **Decision Point B (Normal Change CAB Submission):**
  - *Criteria:* Risk Score 7–9, readiness score $\ge 85\%$, zero critical defects, verified rollback plan, window headroom $\ge 15\%$.
  - *Action:* Approve for standard weekly CAB review agenda.
- **Decision Point C (Major Change Escalation):**
  - *Criteria:* Risk Score 10–12, enterprise impact, or automatic high-risk escalators present.
  - *Action:* Require Service Owner and IT Director sign-off, live bridge, and emergency rollback dry-run.
- **Decision Point D (RFC Rejection & Remediation):**
  - *Criteria:* Readiness score $< 85\%$, missing rollback plan, guaranteed window overrun, or vague steps.
  - *Action:* Reject RFC; return detailed remediation requirements to the change owner.

---

## Output Format Specification

All deliverables generated by this skill must conform to `assets/cab-rfc-document-template.md` and `assets/itsm-change-ticket-template.md`:

1. **CAB Executive Summary:** Change ID, Title, Category, Risk Score, Maintenance Window, Lead Engineer.
2. **Risk & Dependency Matrix:** 4-dimension breakdown, operational dependencies, and stakeholder notification plan.
3. **Pre-Implementation Baseline Checks:** Concrete read-only baseline commands.
4. **Step-by-Step Implementation Procedure:** Numbered operational steps with target hosts and durations.
5. **Rollback & Backout Plan:** Explicit trigger conditions, Go/No-Go cutoff timestamp, and executable backout steps.
6. **Post-Change Verification Plan:** Technical and functional health verification tests.
7. **ITSM Change Request Brief:** Pre-formatted copy-paste ticket block for ServiceNow or Jira Service Management.

---

## Bundled Resources

- **Analysis Engine:** [`scripts/draft_cab_rfc.py`](scripts/draft_cab_rfc.py) — Drafts the RFC package from the interview payload.
- **Readiness Validator:** [`scripts/validate_rfc_readiness.py`](scripts/validate_rfc_readiness.py) — Gates an RFC against CAB submission requirements before it is filed.
- **ITIL Change Categories:** [`references/itil-change-categories.md`](references/itil-change-categories.md) — Operational definitions, governance workflows, lead times, and audit requirements for the three ITIL 4 change types. **Consult before assigning a change category, since category drives the required lead time.**
- **CAB Risk Rubric:** [`references/cab-risk-rubric.md`](references/cab-risk-rubric.md) — The 4-dimension risk scoring model.
- **Maintenance Window Guidelines:** [`references/maintenance-window-guidelines.md`](references/maintenance-window-guidelines.md) — Window headroom and blackout period rules.
- **RFC Document Template:** [`assets/cab-rfc-document-template.md`](assets/cab-rfc-document-template.md)
- **ITSM Change Ticket Template:** [`assets/itsm-change-ticket-template.md`](assets/itsm-change-ticket-template.md)

---

## Data Handling & Sanitization

Sanitization runs **client-side, before any output is produced**, so credentials and
personal data are removed on the operator's machine rather than being sent to a model
or pasted into a ticket.

Two layers apply:

1. This skill's own domain-aware masking (hostnames, accounts, and the identifiers
   specific to this domain).
2. A shared residual pass, [`scripts/sanitizer.py`](scripts/sanitizer.py), vendored
   identically across every skill in the library. It is the common floor: private keys,
   cloud provider keys, JWTs and bearer tokens, connection-string passwords, assigned
   secrets, emails, IPv4/IPv6 addresses, MAC addresses, GUIDs, SSNs, payment card
   numbers, and phone numbers.

The contract is enforced by `tests/sanitizer_conformance_test.py`, which runs the same
adversarial corpus in every skill. Documentation placeholders (RFC 5737/3849 addresses,
RFC 7042 MAC ranges, `example.com` names, and existing `[REDACTED-*]` tokens) are
preserved, so the pass is safe to apply more than once.

Sanitization is thorough and tested, but it is not a substitute for reading output
before sharing it outside your organization.
