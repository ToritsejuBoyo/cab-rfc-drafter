# ITIL 4 Change Enablement & RFC Category Definitions

This reference outlines the operational definitions, governance workflows, lead times, and audit requirements for the three ITIL 4 change types.

---

## Change Classification Table

| Classification | Definition & Operational Context | Minimum Lead Time | Required Sign-Offs | Audit Evidence Required |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Change** | Low-risk, pre-authorized, repetitive, and well-understood operational tasks following a strict Standard Operating Procedure (SOP). | 24 hours notice | Peer engineer / Technical Team Lead | Executed runbook checklist, ticket logging, post-verification check. |
| **Normal Change** | Non-emergency change requiring risk assessment, technical review, stakeholder communication, and CAB evaluation. | 5 business days | Service Owner, Technical Reviewer, CAB Committee | Complete RFC document, rollback test evidence, stakeholder notice, validation tests. |
| **Emergency Change** | Urgent change required to restore degraded or offline critical production services (P1/P2 incident) or patch an active zero-day vulnerability. | Immediate (Retrospective documentation within 24h) | Emergency CAB (eCAB), Incident Commander, IT Director | Incident number link, emergency review minutes, root cause summary, post-implementation audit. |

---

## Mandatory RFC Section Quality Criteria

To pass CAB review, every RFC must fulfill the following criteria:

### 1. Business Justification
- Must state **why** the change is happening and **what business risk** is introduced by deferring it.
- Must cite an associated Problem record, Project ID, Security Vulnerability Advisory, or Incident ticket.

### 2. Pre-Implementation Baseline Checks
- Must capture quantifiable metrics immediately prior to change execution.
- Examples: BGP route table counts, API response latency, disk free space, database active connections, ping loss baseline.

### 3. Step-by-Step Implementation Plan
- Must be written so that a secondary on-call engineer can execute the steps if the primary engineer is incapacitated.
- Every step must list:
  1. Target hostname or IP.
  2. Executable command or explicit UI interaction.
  3. Expected terminal output or status confirmation.
  4. Estimated completion duration in minutes.

### 4. Rollback & Backout Plan
- Must have an objective **Rollback Trigger** (e.g., "Health check endpoint returns HTTP 500 for > 3 minutes").
- Must have a hard **Go / No-Go Decision Cutoff Time**.
- Must contain explicit, copy-pasteable backout commands.
- Vague statements like "undo changes" or "call vendor" result in immediate RFC rejection.

### 5. Post-Change Verification Plan
- Must verify both technical integrity (service daemon active, ports listening) and functional integrity (end-user login, synthetic transaction, data write/read).
