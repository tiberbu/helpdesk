# Story: Fix: P1 hd_time_entry.json out of sync + recursive audit trail violation in task-146

Status: done
Task ID: mn3ednuo44gmjr
Task Number: #163
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:26:07.652Z

## Description

## P1 Fixes from adversarial review task-153

See docs/qa-report-task-146.md for full report (14 findings).

### P1-1: Task-146 audit trail violation (AGAIN)
Task-146 commit (769ad7efa) contains ZERO Python code. Actual code changes were in commit 8b17c65c3 (task-148). Story-130 audit correction incorrectly says code was re-implemented by story-146 -- should say task-148. Update story-130 and story-146 completion notes with accurate commit attribution.

### P1-2: hd_time_entry.json DocType JSON out of sync
Bench copy has System Manager with create:1 and write:1. Dev copy removed these. Run bench migrate to sync, or manually sync the JSON file and migrate.

### P2 Fixes
- P2-3: Story-146 completion notes claim 71 tests, actual is 80. Update or remove hardcoded count.
- P2-5: ensure_* helpers use frappe.throw() instead of assert/AssertionError for role-pollution detection. Use raise AssertionError(...) instead.
- P2-6: Story-130 audit correction references task-146 but code was task-148.

### Files to change
- story-130 completion notes (audit correction attribution)
- story-146 completion notes (test count)
- helpdesk/test_utils.py (frappe.throw -> AssertionError in ensure_* helpers)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json (sync to bench + migrate)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #163

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: Story-130 audit correction updated — "re-implemented correctly by story-146 (task-146)" → "task-148 (commit 8b17c65c3)". Story-146 commit (769ad7efa) contained ZERO Python code; task-148 commit (8b17c65c3) was the actual implementation.
- **P1-2 fixed**: `hd_time_entry.json` was already in sync (System Manager lacks create/write in JSON). DB was out of sync — `bench migrate` run to sync DB; System Manager now has create:0, write:0, delete:0.
- **P2-3 fixed**: Story-146 completion notes updated: "71 tests" → "80 tests" (actual verified count).
- **P2-5 fixed**: `ensure_hd_admin_user()`, `ensure_agent_manager_user()`, `ensure_system_manager_user()` in `helpdesk/test_utils.py` — replaced `frappe.throw()` with `raise AssertionError(...)` so role-pollution detection raises proper Python assertion errors (not Frappe validation exceptions) when called from test helpers.
- **P2-6 fixed**: Same as P1-1 — story-130 audit correction attribution corrected from task-146 to task-148.
- All changed Python files synced to frappe-bench.

### Change Log

- `helpdesk/test_utils.py`: Replaced `frappe.throw()` with `raise AssertionError(...)` in all three `ensure_*` helpers (P2-5).
- `_bmad-output/implementation-artifacts/story-130-*.md`: Updated audit correction — changed "story-146 (task-146)" to "task-148 (commit 8b17c65c3)" (P1-1/P2-6).
- `_bmad-output/implementation-artifacts/story-146-*.md`: Added AUDIT CORRECTION block noting task-146 commit has ZERO Python code, actual code in task-148; updated test count 71→80 (P1-1/P2-3).
- DB: `bench migrate` run — System Manager permissions for HD Time Entry now match JSON (create:0, write:0, delete:0) (P1-2).

### File List

- `helpdesk/test_utils.py` (modified)
- `_bmad-output/implementation-artifacts/story-130-fix-p1-p2-from-adversarial-review-task-120-stale-test-count-.md` (modified)
- `_bmad-output/implementation-artifacts/story-146-fix-p1-delete-entry-double-get-roles-stale-test-count-audit-.md` (modified)
