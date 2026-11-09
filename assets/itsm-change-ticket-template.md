# ITSM Change Request Ticket Template

Use this format when submitting or updating Change Records in ServiceNow, Jira Service Management, Remedy, or ConnectWise.

```text
================================================================================
ITIL CHANGE ADVISORY BOARD (CAB) REQUEST FOR CHANGE (RFC)
================================================================================
Change Number       : {{RFC_ID}}
Change Title        : {{CHANGE_TITLE}}
Category            : {{CHANGE_CATEGORY}}
Assigned Risk Level : {{RISK_LEVEL}} (Risk Score: {{RISK_SCORE}}/12)
Requested Window    : {{WINDOW_START}} to {{WINDOW_END}} ({{WINDOW_DURATION_MINS}} mins)
Change Owner / Lead : {{LEAD_ENGINEER}}
Target System / CI  : {{SYSTEMS_IMPACTED}}

1. BUSINESS JUSTIFICATION & SCOPE:
{{BUSINESS_PURPOSE}}
Technical Driver: {{TECHNICAL_DRIVER}}
Risk of Inaction: {{RISK_OF_INACTION}}

2. TIMING & HEADROOM ANALYSIS:
- Total Implementation Time : {{TOTAL_IMPL_MINS}} mins
- Estimated Rollback Time   : {{ROLLBACK_DURATION_MINS}} mins
- Total Required Duration   : {{TOTAL_ACTIVE_MINS}} mins
- Maintenance Window Margin : {{HEADROOM_BUFFER_MINS}} mins ({{HEADROOM_PCT}}% buffer)
- Go / No-Go Decision Cutoff: {{DECISION_CUTOFF_TIME}}

3. PRE-IMPLEMENTATION BASELINE:
{{PRE_CHECK_SUMMARY}}

4. IMPLEMENTATION PROCEDURE SUMMARY:
{{IMPLEMENTATION_SUMMARY}}

5. ROLLBACK & BACKOUT PLAN:
Trigger Conditions: {{ROLLBACK_TRIGGER_CONDITIONS}}
Backout Commands:
{{ROLLBACK_SUMMARY}}

6. POST-CHANGE VERIFICATION:
{{VERIFICATION_SUMMARY}}

7. CAB STATUS & APPROVALS:
Readiness Audit Score : {{READINESS_SCORE}}%
CAB Recommendation    : {{CAB_RECOMMENDATION}}
Approvers: Peer ({{PEER_REVIEWER}}), Owner ({{SERVICE_OWNER}}), CAB Chair ({{CAB_CHAIR}})
================================================================================
```

