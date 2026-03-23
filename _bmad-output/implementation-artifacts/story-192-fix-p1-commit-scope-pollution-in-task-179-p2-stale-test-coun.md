# Story: Fix: P1 commit-scope pollution in task-179 + P2 stale test counts in story-146/story-130

Status: done
Task ID: mn3fcaid3lrmhd
Task Number: #192
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:53:03.039Z

## Description

## P1/P2 Fixes from adversarial review task-183

See docs/qa-report-task-179.md for full report (14 findings).

### P1: Commit-scope pollution in task-179
Commit 0dc9def81 contains 9 files but story-179 only declares 3. Includes artifacts from tasks #170, #174, #182, and qa-report-task-164.md. This is the Nth recurrence of the exact anti-pattern the task chain was created to eliminate. Update story-179 file list to acknowledge all 9 files.

### P2-3: Story-146 line 69 still says "All 4 tests in helpdesk/tests/test_utils.py pass" but actual count is 6
Remove the hardcoded "4" count or replace with "All tests pass" -- same fix pattern already applied to test_hd_time_entry on the same line.

### P2-4: Story-130 line 81 still says "Current count (after subsequent stories) is 71" but actual is 83
Remove the hardcoded "71" count. Apply the same principle stated in story-146: "hardcoded counts become stale as the suite grows."

### P2-5: F-13 test only covers empty string, not None
Add a second assertion in test_falsy_status_clears_status_category that tests doc.status = None.

### Files to change
- _bmad-output/implementation-artifacts/story-179-*.md (update file list to acknowledge all 9 committed files)
- _bmad-output/implementation-artifacts/story-146-*.md (fix stale "4 tests" count)
- _bmad-output/implementation-artifacts/story-130-*.md (fix stale "71" count)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (add None falsy-status assertion)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #192

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1 fixed (story-179 file list)**: Updated story-179 File List to acknowledge all 9 files in commit `0dc9def81`. Previously only 3 files were declared; the 6 extra files (story-170, story-174, story-179 itself, story-182, sprint-status.yaml, docs/qa-report-task-164.md) are now listed with notes identifying them as unintentionally committed.
- **P2-3 fixed (story-146 count)**: Removed hardcoded "4" from "All 4 tests in helpdesk/tests/test_utils.py pass" → "All tests in helpdesk/tests/test_utils.py pass".
- **P2-4 fixed (story-130 count)**: Removed hardcoded "71" from "Current count (after subsequent stories) is 71" and added note explaining point-in-time counts are removed.
- **P2-5 fixed (F-13 None assertion)**: Added second assertion block in `test_falsy_status_clears_status_category` that seeds `status_category="Open"`, sets `doc.status = None`, calls `set_status_category()`, and asserts `status_category is None`. Synced to frappe-bench.

### Change Log

- `_bmad-output/implementation-artifacts/story-179-*.md`: Updated File List section to acknowledge all 9 committed files with explanatory notes.
- `_bmad-output/implementation-artifacts/story-146-*.md`: Removed hardcoded "4" count from test_utils.py reference (line 69).
- `_bmad-output/implementation-artifacts/story-130-*.md`: Removed hardcoded "71" count from test count correction note (line 81).
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py`: Added `None` falsy-status assertion to `test_falsy_status_clears_status_category`. Synced to frappe-bench.

### File List

- `_bmad-output/implementation-artifacts/story-179-fix-p1-undeclared-scope-creep-in-task-163-p2-stale-test-coun.md` (modified — expanded file list to 9 files)
- `_bmad-output/implementation-artifacts/story-146-fix-p1-delete-entry-double-get-roles-stale-test-count-audit-.md` (modified — removed hardcoded "4" count)
- `_bmad-output/implementation-artifacts/story-130-fix-p1-p2-from-adversarial-review-task-120-stale-test-count-.md` (modified — removed hardcoded "71" count)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified — added None assertion to F-13 test)
