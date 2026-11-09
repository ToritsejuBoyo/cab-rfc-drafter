# Maintenance Window & Temporal Headroom Guidelines

This reference defines mathematical formulas for evaluating maintenance window durations, implementation step allocations, rollback margins, and Go / No-Go decision deadlines.

---

## The Golden Formula of Change Windows

To guarantee zero maintenance window overruns, the total planned implementation time, rollback time, and safety contingency buffer must not exceed the scheduled window duration:

$$\text{Total Required Window} = T_{\text{impl}} + T_{\text{rollback}} + T_{\text{buffer}} \le T_{\text{window}}$$

Where:
- $T_{\text{impl}} = \sum_{i=1}^{n} t_i$: Sum of durations for all planned implementation steps.
- $T_{\text{rollback}}$: Time required to completely execute all rollback commands and return the system to its pre-change baseline state.
- $T_{\text{buffer}}$: Mandatory contingency safety margin ($\ge 20\%$ of $T_{\text{window}}$ or at least 15 minutes, whichever is greater).
- $T_{\text{window}}$: The approved duration between change start time and scheduled completion time.

---

## Go / No-Go Decision Cutoff Point

The Go / No-Go Decision Cutoff Point is the absolute latest wall-clock timestamp at which the change owner must decide whether to commit or abort and execute rollback:

$$\text{Cutoff Timestamp} = \text{Window End Time} - T_{\text{rollback}} - T_{\text{post-rollback-verify}} - 10\text{ minutes}$$

### Operational Rule
If implementation tasks are not 100% completed and initial post-change verification is not successful prior to the **Cutoff Timestamp**, **the rollback procedure must be initiated immediately without exception**.

---

## Timing Feasibility Thresholds

The validation engine evaluates temporal metrics against the following constraints:

| Metric | Condition | Evaluation Result |
| :--- | :--- | :--- |
| **Window Headroom** | $(T_{\text{impl}} + T_{\text{rollback}}) > T_{\text{window}}$ | **CRITICAL DEFECT: Guaranteed Overrun.** RFC rejected immediately. |
| **Headroom Buffer** | $(T_{\text{impl}} + T_{\text{rollback}}) > 0.85 \times T_{\text{window}}$ | **WARNING: Tight Buffer.** Less than 15% contingency reserve. |
| **Cutoff Viability** | $\text{Cutoff Time} \le \text{Start Time} + T_{\text{impl}}$ | **CRITICAL DEFECT:** Implementation steps cannot complete before cutoff. |
| **Rollback Duration** | $T_{\text{rollback}} == 0$ OR missing | **CRITICAL DEFECT:** Rollback time unaccounted for. |

