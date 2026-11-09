# Change Risk Scoring & Evaluation Rubric

This document defines the 4-dimension ITIL risk evaluation model used to objectively classify changes into Standard (Low), Normal (Medium), and Major (High) risk categories.

---

## 4-Dimension Change Risk Calculation Matrix

Each change is evaluated across four distinct dimensions. Each dimension is scored from 1 (lowest risk) to 3 (highest risk).

| Impact Dimension | Low Risk (1 point) | Medium Risk (2 points) | High Risk (3 points) |
| :--- | :--- | :--- | :--- |
| **1. User Impact Scope** | Internal IT staff only, non-production environments, or fewer than 10 internal users. | Departmental impact, single non-critical branch office, or 10 to 250 internal users. | Enterprise-wide, external customers, core transaction systems, or more than 250 users. |
| **2. Service Redundancy** | High-availability active-active pair, seamless automated load balancer failover, zero downtime. | Failover cluster with momentary pause (< 30 seconds), standby node available. | Standalone host, single point of failure (SPOF), non-redundant core switch or primary database. |
| **3. Reversibility & Rollback** | Instant rollback (< 5 minutes), configuration toggle, snapshot revert, zero data loss. | Clean rollback feasible in 5 to 20 minutes; tested backout script available. | Irreversible, destructive data schema migration, physical firmware re-flash, rollback > 30 minutes. |
| **4. Operational Precedent** | Standard routine change executed repeatedly with documented operational runbook. | Tested previously in staging or lab environment with documented results. | First-time deployment, novel architecture, major vendor version jump, or zero staging precedent. |

---

## Risk Tier Classification & Governance Thresholds

$$\text{Total Risk Score} = \text{Scope} + \text{Redundancy} + \text{Reversibility} + \text{Precedent}$$

| Total Score Range | Risk Level | Change Category | Approval Authority & CAB Requirement |
| :--- | :--- | :--- | :--- |
| **4 – 6 points** | **Low Risk** | **Standard Change** | Pre-approved by Change Management; delegated to peer engineer; fast-track deployment. |
| **7 – 9 points** | **Medium Risk** | **Normal Change** | Requires formal peer technical review, Service Owner sign-off, and standard weekly CAB approval. |
| **10 – 12 points** | **High Risk** | **Major Change** | Mandatory full CAB review, Head of Infrastructure / IT Director sign-off, and live on-call bridge. |

---

## Automatic Disqualifiers (Elevates Directly to High Risk)

A change is automatically escalated to **High Risk (Major Change)** regardless of points if any of the following conditions are present:
1. **Zero Rollback Plan:** No documented backout procedure or rollback commands.
2. **Untested Data Loss Potential:** Database schema alteration involving `DROP`, `TRUNCATE`, or column conversions without a verified point-in-time backup.
3. **Core Network Perimeter:** Core edge firewall, border BGP router, or root PKI Certificate Authority modification during business operational hours.
4. **Maintenance Window Overrun Risk:** Planned implementation duration + rollback duration exceeds 80% of the allocated maintenance window duration.
