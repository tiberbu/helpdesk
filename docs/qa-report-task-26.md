# QA Report: Story 2.1 — Automation Rule DocType and Engine Core

**Task**: #26
**QA Task**: #216
**Date**: 2026-03-23
**Reviewer Model**: opus (adversarial review)
**Method**: Code review + unit test execution + API endpoint testing (Playwright MCP unavailable)

---

## Test Execution Summary

| Test Suite | Tests | Result |
|---|---|---|
| test_hd_automation_rule | 13 | PASS |
| test_conditions | 26 | PASS |
| test_actions | 7 | PASS |
| test_safety | 7 | PASS |
| test_engine | 7 | PASS |
| **Total** | **53** | **ALL PASS** |

---

## Acceptance Criteria Results

### AC1: HD Automation Rule DocType with all specified fields
**PASS**

DocType JSON defines: `rule_name` (Data, unique, reqd), `description` (Small Text), `enabled` (Check, default=1), `trigger_type` (Select, reqd), `conditions` (JSON), `actions` (JSON), `priority_order` (Int, default=10), `failure_count` (Int, read_only). All required fields present.

API test confirmed: created rule successfully via `POST /api/resource/HD Automation Rule` with all fields populated and correct defaults.

### AC2: Conditions evaluated and actions executed on ticket_created
**PASS**

`test_matching_rule_executes_action` confirms that a rule with `priority equals Urgent` condition correctly fires `set_priority` action when an Urgent ticket is created. `test_non_matching_rule_does_not_execute_action` confirms non-matching conditions are skipped.

### AC3: Multiple matching rules execute in priority order
**PASS**

`test_rules_execute_in_priority_order` creates two rules (priority_order=1 and 2) both matching the same ticket. Final state reflects rule B (priority_order=2) firing last, confirming ascending order execution.

### AC4: Loop detection blocks after 5 executions within 1 minute
**PASS**

`test_loop_detection_blocks_execution` confirms that after `MAX_EXECUTIONS_PER_WINDOW` (5) calls to `evaluate()`, the 6th call is blocked and no action fires. Redis-backed with 60s TTL.

---

## Adversarial Findings

### Issue 1 (P1): DocType validator rejects nested condition groups that the engine supports

- **Severity**: P1 — Feature broken
- **File**: `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`, lines 50-60
- **Description**: The `_validate_conditions()` method checks every dict in the conditions array for `"field"` and `"operator"` keys. However, the `ConditionEvaluator` explicitly supports nested condition groups with `{"logic": "OR", "conditions": [...]}` format (documented in conditions.py docstring, tested in `test_nested_group`). These nested groups have `"logic"` and `"conditions"` keys — NOT `"field"` and `"operator"` — so the validator rejects them.
- **Reproduction**: `curl -X POST .../api/resource/HD%20Automation%20Rule -d '{"conditions":"[{\"logic\":\"OR\",\"conditions\":[{\"field\":\"priority\",\"operator\":\"equals\",\"value\":\"Urgent\"}]}]",...}'` returns `ValidationError: Condition #1 must have 'field' and 'operator' keys`
- **Impact**: Users cannot create rules with OR logic groups via the API or UI.

### Issue 2 (P1): `resolve_trigger_type` returns only ONE trigger type, losing `ticket_updated` rules when specialized triggers fire

- **Severity**: P1 — Logic flaw
- **File**: `helpdesk/helpdesk/automation/triggers.py`, lines 36-87
- **Description**: When a ticket is resolved, `resolve_trigger_type` returns `"ticket_resolved"` but NOT `"ticket_updated"`. This means rules configured for `trigger_type=ticket_updated` will NOT fire when the update happens to be a resolution. A rule like "on any ticket update, add tag 'modified'" would silently miss resolution events. The same applies to `ticket_assigned` and `ticket_reopened` — all shadow `ticket_updated`.
- **Impact**: Rules using `ticket_updated` trigger type are unreliable — they miss a subset of updates. No test covers this interaction.

### Issue 3 (P2): No unit tests for `triggers.py` — specialized trigger resolution is untested

- **Severity**: P2 — Missing test coverage
- **File**: No `test_triggers.py` exists
- **Description**: The `resolve_trigger_type()` function contains non-trivial logic for deriving `ticket_resolved`, `ticket_reopened`, and `ticket_assigned` from `_doc_before_save` state. None of this is tested. The engine integration tests only test `ticket_created` and `ticket_updated` — never the specialized triggers.
- **Impact**: Regressions in trigger resolution would go undetected.

### Issue 4 (P2): No tests for `add_tag` and `assign_to_agent` action handlers

- **Severity**: P2 — Missing test coverage
- **File**: `helpdesk/helpdesk/automation/test_actions.py`
- **Description**: `test_actions.py` tests `assign_to_team`, `set_priority`, `set_status`, `add_internal_note`, and unknown action type. But `add_tag` and `assign_to_agent` — two of the six supported action types — have zero test coverage.
- **Impact**: If `assign_to_agent` integration with `frappe.desk.form.assign_to.add` breaks, or `add_tag` has issues, there's no regression safety net.

### Issue 5 (P2): `_action_add_tag` reloads the full ticket document from DB — performance concern

- **Severity**: P2 — Performance
- **File**: `helpdesk/helpdesk/automation/actions.py`, line 131
- **Description**: `frappe.get_doc("HD Ticket", ticket.name).add_tag(tag)` loads the entire HD Ticket document just to call `add_tag()`, which ultimately inserts into the `tabTag Link` table. The dev notes say "All DB writes in actions use `frappe.db.set_value()` (no doc.save()) to avoid re-triggering on_update hooks" — but this action violates that pattern by loading a full document. While `add_tag()` may not trigger `save()`, it's inconsistent and fragile.
- **Impact**: Unnecessary DB load per tag action; inconsistent with stated design pattern.

### Issue 6 (P2): `is_set` / `is_not_set` operators treat `0` as "not set" — wrong for numeric fields

- **Severity**: P2 — Logic flaw
- **File**: `helpdesk/helpdesk/automation/conditions.py`, lines 121-125
- **Description**: `is_set` returns `False` when `actual == 0`, and `is_not_set` returns `True` when `actual == 0`. For numeric fields like `feedback_rating`, a value of `0` is a legitimate value (zero rating), not "unset". This means a condition `{"field": "feedback_rating", "operator": "is_set"}` would incorrectly return False for a ticket with `feedback_rating=0`.
- **Impact**: Rules using `is_set`/`is_not_set` on numeric fields produce incorrect results.

### Issue 7 (P2): Race condition in `safety.py` loop counter — read-then-write is not atomic

- **Severity**: P2 — Concurrency bug
- **File**: `helpdesk/helpdesk/automation/safety.py`, lines 49-69
- **Description**: `check_loop()` does a `get_value` then `set_value` on Redis — two separate operations. Under concurrent requests (multiple gunicorn workers processing events for the same ticket simultaneously), both workers could read `current=4`, both increment to `5`, and both proceed. This defeats the loop guard's purpose. Redis `INCR` would be atomic and correct.
- **Impact**: Under concurrent load, loop detection may allow more than 5 executions.

### Issue 8 (P2): Race condition in `record_failure` — non-atomic read-increment-write

- **Severity**: P2 — Concurrency bug
- **File**: `helpdesk/helpdesk/automation/safety.py`, lines 86-115
- **Description**: `record_failure()` reads `failure_count` via `frappe.db.get_value`, increments in Python, then writes back via `frappe.db.set_value`. Two concurrent workers could read the same count, both increment to the same value, and the auto-disable threshold is reached later than expected (or a count is lost). Should use `frappe.db.sql("UPDATE ... SET failure_count = failure_count + 1 ...")` for atomicity.
- **Impact**: Under concurrent load, failure count may be inaccurate and auto-disable delayed.

### Issue 9 (P3): `tearDown` in `test_hd_automation_rule.py` calls both `commit()` and `rollback()` — contradictory

- **Severity**: P3 — Test hygiene
- **File**: `helpdesk/helpdesk/doctype/hd_automation_rule/test_hd_automation_rule.py`, lines 26-27
- **Description**: The tearDown method calls `frappe.db.commit()` (to persist the `delete_doc`) then immediately calls `frappe.db.rollback()`. The rollback after commit is a no-op for the committed transaction. While this "works" (the explicit deletes handle cleanup), it's confusing and suggests the author was uncertain about the cleanup strategy. The comment from MEMORY.md explains the pattern — but `rollback()` after `commit()` is still dead code.
- **Impact**: Misleading code; no functional issue.

### Issue 10 (P3): No migration patch in `patches.txt` for the new DocType

- **Severity**: P3 — Deployment risk
- **File**: `helpdesk/patches.txt`
- **Description**: The new `HD Automation Rule` DocType was created and migrated via `bench migrate` on the dev site. However, no patch entry was added to `patches.txt`. For Frappe framework, new DocTypes are typically auto-detected by `bench migrate` via the JSON fixtures, so this may work without a patch. However, if any data migration or initial setup is needed (e.g., default rules, ensuring `automation_enabled` field exists in HD Settings), there's no migration entry.
- **Impact**: Low — Frappe auto-migrates DocType schema from JSON, but there's no documentation that this was considered.

### Issue 11 (P3): `_check_write_permission` in DocType validate is redundant with DocType permissions

- **Severity**: P3 — Over-engineering
- **File**: `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`, lines 20-30
- **Description**: The DocType JSON already defines granular permissions: System Manager and HD Admin get create/write/delete, Agent gets only read. Frappe's permission system enforces this automatically. The `_check_write_permission()` in `validate()` duplicates this enforcement and could diverge from the JSON permissions if they're updated independently.
- **Impact**: Maintenance burden; two permission systems to keep in sync.

### Issue 12 (P2): `evaluate()` catches the loop guard once before the rule loop — a failing action that triggers re-save could bypass it

- **Severity**: P2 — Design gap
- **File**: `helpdesk/helpdesk/automation/engine.py`, lines 63-88
- **Description**: The loop guard `check_loop()` is called once at the start of `evaluate()`, incrementing the counter by 1. Then ALL matching rules execute. If rule A's action triggers an HD Ticket `on_update` (e.g., through an indirect mechanism like `assign_to_agent` which calls `frappe.get_doc().check_permission()` then modifies assignment metadata), this could re-enter `on_ticket_updated` → `evaluate()` recursively within the same request. The counter would increment again, but since it happens within nested Python calls (not separate requests), the Redis read in the inner call may or may not see the outer call's write depending on Redis pipeline behavior.
- **Impact**: Potential for recursive execution within a single request if any action indirectly triggers doc events.

---

## Summary

| Severity | Count | Issues |
|---|---|---|
| P0 | 0 | — |
| P1 | 2 | #1 (nested conditions rejected), #2 (trigger type shadowing) |
| P2 | 6 | #3 (no trigger tests), #4 (missing action tests), #5 (add_tag perf), #6 (is_set/0), #7 (loop race), #8 (failure race), #12 (re-entrant loop) |
| P3 | 3 | #9 (tearDown hygiene), #10 (no migration patch), #11 (redundant permission check) |

**Overall Assessment**: The core implementation is solid — all 53 tests pass, the architecture is clean, and the code is well-documented. However, there are two P1 issues that break advertised functionality: nested condition groups are rejected at save time despite being supported at evaluation time, and specialized trigger types shadow `ticket_updated` rules. The concurrency issues (P2) are real but unlikely to cause problems at current scale.
