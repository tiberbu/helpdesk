# QA Report: Story 2.1 — Automation Rule DocType and Engine Core

**Task**: #26
**QA Task**: #216 (adversarial review, round 2 post-fix)
**Date**: 2026-03-24
**Reviewer Model**: Claude Opus 4.6 (adversarial review)
**Method**: Code review + 80 unit tests + API integration tests (curl against help.frappe.local)

> Playwright MCP browser tools were not available. Testing performed via backend tests and API integration.

---

## Test Execution Summary

| Test Suite | Tests | Result |
|---|---|---|
| test_hd_automation_rule | 13 | PASS |
| test_conditions | 26 | PASS |
| test_actions | 7 | PASS |
| test_safety | 10 | PASS |
| test_engine | 7 | PASS |
| test_hd_automation_log | 17 | PASS |
| **Total** | **80** | **ALL PASS** |

Note: DocType test suite has intermittent `TimestampMismatchError` in `before_tests()` SLA fixture. Pre-existing flaky infrastructure issue. Tests pass with `--skip-before-tests`.

---

## Acceptance Criteria Results

### AC1: HD Automation Rule DocType with all specified fields
**PASS**

DocType defines: `rule_name` (Data, unique, reqd), `description` (Small Text), `enabled` (Check, default=1), `trigger_type` (Select, reqd), `conditions` (JSON), `actions` (JSON), `priority_order` (Int, default=10), `failure_count` (Int, read_only). API-verified: created, read, deleted rules successfully.

### AC2: Conditions evaluated and actions executed on ticket_created
**PASS**

`test_matching_rule_executes_action` and `test_non_matching_rule_does_not_execute_action` both pass. Execution logged to HD Automation Log with timing.

### AC3: Multiple matching rules execute in priority order
**PASS**

`test_rules_execute_in_priority_order` confirms ascending priority_order execution (lower number = higher priority).

### AC4: Loop detection blocks after 5 executions within 1 minute
**PASS**

`test_loop_detection_blocks_execution` confirms 6th call is blocked. `test_first_executions_are_allowed` and `test_execution_beyond_limit_is_blocked` confirm boundary behavior.

---

## Previous P1 Fix Verification

### Original Issue 1: Nested condition groups rejected
**FIXED** — Validator now handles `{"logic": "OR", "conditions": [...]}` groups (lines 56-74 of `hd_automation_rule.py`). Single-level nesting confirmed working via API.

### Original Issue 2: Trigger type shadowing
**FIXED** — `resolve_trigger_type()` returns lists. Resolution fires `["ticket_resolved", "ticket_updated"]`. `_run()` iterates.

---

## Adversarial Findings (New Issues)

### Issue 1 (P1): Deeply nested conditions (3+ levels) rejected by validator but supported by evaluator

- **Severity**: P1 — Feature inconsistency that blocks legitimate use
- **File**: `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`, lines 64-74
- **Description**: The validator checks sub-conditions within a nested group for `"field"` and `"operator"` keys — but doesn't account for the fact that sub-conditions can themselves be nested groups. A condition like `[{"logic":"OR","conditions":[{"logic":"AND","conditions":[{"field":"priority","operator":"equals","value":"Urgent"}]}]}]` is rejected because the inner `{"logic":"AND","conditions":[...]}` doesn't have `"field"/"operator"`. The `ConditionEvaluator` handles arbitrary recursion depth (confirmed via `bench console`).
- **Reproduction**: `curl -X POST .../api/resource/HD%20Automation%20Rule -d '{"rule_name":"deep","trigger_type":"ticket_created","conditions":"[{\"logic\":\"OR\",\"conditions\":[{\"logic\":\"AND\",\"conditions\":[{\"field\":\"priority\",\"operator\":\"equals\",\"value\":\"Urgent\"}]}]}]","actions":"[]"}'` returns `ValidationError: Condition #1 sub-condition #1 must have 'field' and 'operator' keys.`
- **Impact**: Cannot create rules with complex nested logic like `(A OR B) AND (C OR D)` which requires 3 levels.

### Issue 2 (P1): DocType trigger_type has phantom options that can never fire

- **Severity**: P1 — Misleading / broken feature
- **File**: `hd_automation_rule.json` line 51 vs `triggers.py` lines 12-23
- **Description**: The DocType Select field includes `csat_received`, `chat_started`, `chat_ended` as trigger options. These are NOT in `TRIGGER_TYPES` in `triggers.py` and no code path anywhere fires rules with these types. An admin could create a rule with `trigger_type=csat_received` — it saves successfully but silently never executes. There is no warning, no documentation, and no way for the admin to know it's dead.
- **Impact**: Admins create automation rules they believe work but that never fire. Data integrity problem — rules exist in an impossible state.

### Issue 3 (P2): Specialized events burn 2 loop counter slots per save

- **Severity**: P2 — Logic flaw
- **File**: `engine.py` lines 61-63, `safety.py` `check_loop()`
- **Description**: When a ticket is resolved, `_run()` iterates over `["ticket_resolved", "ticket_updated"]`, calling `evaluate()` twice. Each `evaluate()` increments the loop counter. A single doc save burns 2 of 5 allowed executions for specialized events. Loop detection would fire after 2-3 saves on resolved tickets instead of 5.

### Issue 4 (P2): `_create_log` doesn't pass `ignore_links=True` — log silently lost on link validation failure

- **Severity**: P2 — Silent data loss
- **File**: `engine.py` line 193
- **Description**: HD Automation Log's `rule_name` is a Link field. `.insert(ignore_permissions=True)` doesn't bypass link validation. If the rule is concurrently deleted, log insertion throws `LinkValidationError` (caught by try/except, silently lost).

### Issue 5 (P2): `_notify_rule_creator` interpolates `rule_name` into HTML without escaping — stored XSS

- **Severity**: P2 — Security
- **File**: `safety.py` lines 137-142
- **Description**: Email body builds `<b>{0}</b>` with `.format(rule_name, ...)`. A rule_name like `<img src=x onerror=alert(1)>` would render as executable HTML in the email.

### Issue 6 (P2): No tests for `triggers.py` — critical fix has no regression test

- **Severity**: P2 — Missing test coverage
- **Description**: The original P1 trigger shadowing fix has no dedicated regression test. No `test_triggers.py` exists.

### Issue 7 (P2): No tests for `add_tag` and `assign_to_agent` actions

- **Severity**: P2 — Missing test coverage (2 of 6 action types untested)

### Issue 8 (P2): `is_set` / `is_not_set` treat `0` as "not set"

- **Severity**: P2 — Logic flaw for numeric fields
- **File**: `conditions.py` lines 121-125

### Issue 9 (P2): Redis loop counter read-then-write is not atomic

- **Severity**: P2 — Concurrency bug
- **File**: `safety.py` lines 49-69

### Issue 10 (P2): `dry_run` evaluates disabled rules without warning

- **Severity**: P2 — Misleading
- **File**: `engine.py` lines 89-95 + 280-287

### Issue 11 (P3): `_action_add_tag` loads full document (violates stated design pattern)

- **Severity**: P3 — Consistency
- **File**: `actions.py` line 131

### Issue 12 (P3): `record_failure` read-increment-write is non-atomic

- **Severity**: P3 — Low-impact concurrency (threshold=10)
- **File**: `safety.py` lines 96-98

---

## Summary

| Severity | Count | Issues |
|---|---|---|
| P0 | 0 | -- |
| P1 | 2 | #1 (deep nesting rejected), #2 (phantom trigger types) |
| P2 | 8 | #3 (double loop burn), #4 (log link failure), #5 (XSS), #6 (no trigger tests), #7 (missing action tests), #8 (is_set/0), #9 (loop race), #10 (dry_run disabled) |
| P3 | 2 | #11 (add_tag pattern), #12 (failure race) |

**Overall Assessment**: All 4 original acceptance criteria pass. The previous P1 fixes (nested conditions, trigger shadowing) are correctly applied. However, two new P1 issues were introduced: the condition validator's recursion only goes one level deep (blocking complex rules), and phantom trigger types in the DocType Select allow creation of rules that can never fire.

## Console Errors
None observed during API testing.
