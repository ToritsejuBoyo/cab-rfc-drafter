# Request for Change (RFC) Submission Package

**RFC Identifier:** `{{RFC_ID}}`  
**Change Title:** `{{CHANGE_TITLE}}`  
**Change Category:** `{{CHANGE_CATEGORY}}` (STANDARD / NORMAL / MAJOR / EMERGENCY)  
**Assigned Risk Level:** `{{RISK_LEVEL}}` (Score: `{{RISK_SCORE}}`/12)  
**Change Owner / Lead Engineer:** `{{LEAD_ENGINEER}}`  
**Executing Team:** `{{EXECUTING_TEAM}}`  
**Scheduled Window:** `{{WINDOW_START}}` to `{{WINDOW_END}}` (`{{WINDOW_DURATION_MINS}}` mins)  

---

## 1. Executive Summary & Business Justification
- **Business Purpose:** `{{BUSINESS_PURPOSE}}`
- **Technical Problem / Driver:** `{{TECHNICAL_DRIVER}}`
- **Business Impact of Not Implementing:** `{{RISK_OF_INACTION}}`
- **Scope & Affected Systems:** `{{SYSTEMS_IMPACTED}}`
- **User Impact & Outage Expectation:** `{{OUTAGE_EXPECTATION}}`

---

## 2. Risk Assessment & Mitigations

### 2.1 4-Dimension Risk Breakdown
| Risk Dimension | Score (1-3) | Rationale |
| :--- | :--- | :--- |
| **User Impact Scope** | `{{SCORE_SCOPE}}` | `{{RATIONALE_SCOPE}}` |
| **Service Redundancy** | `{{SCORE_REDUNDANCY}}` | `{{RATIONALE_REDUNDANCY}}` |
| **Reversibility** | `{{SCORE_REVERSIBILITY}}` | `{{RATIONALE_REVERSIBILITY}}` |
| **Operational Precedent** | `{{SCORE_PRECEDENT}}` | `{{RATIONALE_PRECEDENT}}` |
| **Total Weighted Score** | **`{{RISK_SCORE}}` / 12** | **Category: `{{RISK_LEVEL}}`** |

### 2.2 Operational Dependencies & Blast-Radius Controls
- **Upstream Dependencies:** `{{UPSTREAM_DEPENDENCIES}}`
- **Downstream Services Impacted:** `{{DOWNSTREAM_SERVICES}}`
- **Communication & Stakeholder Notifications:** `{{COMMUNICATION_PLAN}}`

---

## 3. Pre-Implementation Baseline Checks
Execute these commands immediately prior to commencing changes to capture healthy state:

```bash
{{PRE_CHECK_COMMANDS}}
```

---

## 4. Step-by-Step Implementation Procedure

| Step # | Action Description & Exact Command | Executing Engineer | Est. Duration | Target Host / Device |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `{{STEP_1_CMD}}` | `{{STEP_1_ENG}}` | `{{STEP_1_DUR}}` mins | `{{STEP_1_HOST}}` |
| 2 | `{{STEP_2_CMD}}` | `{{STEP_2_ENG}}` | `{{STEP_2_DUR}}` mins | `{{STEP_2_HOST}}` |
| 3 | `{{STEP_3_CMD}}` | `{{STEP_3_ENG}}` | `{{STEP_3_DUR}}` mins | `{{STEP_3_HOST}}` |

- **Total Planned Implementation Time ($T_{\text{impl}}$):** `{{TOTAL_IMPL_MINS}}` minutes

---

## 5. Rollback & Backout Plan (Mandatory)
- **Rollback Trigger Conditions:** `{{ROLLBACK_TRIGGER_CONDITIONS}}`
- **Go / No-Go Decision Cutoff Time:** `{{DECISION_CUTOFF_TIME}}`
- **Estimated Rollback Duration ($T_{\text{rollback}}$):** `{{ROLLBACK_DURATION_MINS}}` minutes
- **Window Safety Headroom Margin:** `{{HEADROOM_BUFFER_MINS}}` minutes
- **Backout Execution Steps:**
```bash
{{ROLLBACK_COMMANDS}}
```

---

## 6. Post-Change Verification & Acceptance Sign-Off
Execute these tests immediately after implementation (or rollback) to verify service health:

1. **Service Daemon & Port Check:** `{{VERIFY_DAEMON_CMD}}`
2. **Functional Transaction Test:** `{{VERIFY_TRANSACTION_CMD}}`
3. **End-to-End User Experience Validation:** `{{VERIFY_USER_EXP_CMD}}`

---

## 7. Change Approvals & CAB Sign-Off
- **Peer Technical Reviewer:** `{{PEER_REVIEWER}}` - `[APPROVED]`
- **Service Owner:** `{{SERVICE_OWNER}}` - `[APPROVED]`
- **CAB Chair / Authority:** `{{CAB_CHAIR}}` - `[PENDING / APPROVED]`
