# Story: Fix: P1 dev/bench desync in utils.py + hd_time_entry.py + commit-scope pollution audit

Status: done
Task ID: mn3ezislsg5jss
Task Number: #182
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:43:06.379Z

## Description

## P1 findings from adversarial review (docs/qa-report-task-164.md)

### P1 #1: Commit-scope pollution
Commit 1aab1769d (task #164) contains undeclared changes to utils.py and hd_time_entry.py from unrelated task chains. Story-164 file list only declares hd_ticket.py and test_incident_model.py.

### P1 #2: Dev/bench desync
- utils.py DEV has ValueError enforcement for identity contract in is_agent(); BENCH has only docstring warning
- hd_time_entry.py DEV has PRIVILEGED_ROLES as explicit frozenset; BENCH has AGENT_ROLES - {Agent} derivation
- These are contradictory implementations. Reconcile to one canonical version and sync.

### Files to reconcile:
- helpdesk/utils.py (dev vs bench)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (dev vs bench)

### Verification:
- diff dev and bench copies — must be identical
- Run full test suite to confirm no regressions

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #182

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **No code changes required.** Both P1 desync issues had already been resolved in prior fix commits:
  - Task #169, commit `d57b258ce` — "Fix: P1 PRIVILEGED_ROLES/AGENT_ROLES unsync + on_trash double get_roles" resolved hd_time_entry.py desync (PRIVILEGED_ROLES explicit frozenset now identical in dev and bench)
  - Task #175, commit `5a680623e` — "Fix: P1 _ensure_sm_agent_user missing HD Agent record + P1 is_agent identity contract" resolved utils.py desync (ValueError enforcement now identical in dev and bench)
- **Diffs confirmed identical**: `diff helpdesk/utils.py` → IDENTICAL; `diff hd_time_entry.py` → IDENTICAL
- **Test suite**: All 168 tests pass (43s, OK). Zero regressions.
- **P1 #1 (commit-scope pollution)**: Commit 1aab1769d introduced utils.py and hd_time_entry.py changes outside declared scope; those changes are now the canonical versions in both codebases and are correctly synced, so no further remediation needed.
- **Audit trail note** (added by task #196): The two resolving commits above were authorized and implemented by task #169 and task #175 respectively. Developers tracing the desync remediation should look up those task files: `story-169-fix-p1-privileged-roles-agent-roles-unsync-on-trash-double-g.md` and `story-175-fix-p1-ensure-sm-agent-user-missing-hd-agent-record-p1-is-ag.md`.

### Change Log

- 2026-03-23: Verified dev/bench sync — both files already identical. No code modifications needed. Confirmed 168/168 tests pass.

### File List

_(No files modified — both dev and bench were already in sync)_
