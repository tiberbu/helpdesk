# Story: Fix: P1 6th recursive commit-scope pollution in task-189 + wrong test_utils.py path + stale story-171 notes

Status: done
Task ID: mn3foylz2tee10
Task Number: #202
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:02:55.517Z

## Description

## From adversarial review task #194 (docs/qa-report-task-189.md)

### P1-1: 6th recursive commit-scope pollution
Commit 9591cb7ef modifies 16 files but story-189 File List declares only 4. The 12 undeclared files include 8 story artifacts, sprint-status.yaml, 2 QA reports, and test_incident_model.py (production test code change). Update story-189 File List to enumerate all 16 files.

### P1-2: Wrong filesystem path in story-189
Story-189 Change Log and File List reference `helpdesk/helpdesk/tests/test_utils.py` — this path does not exist. Correct to `helpdesk/tests/test_utils.py`.

### P1-3: Stale story-171 completion notes
Story-171 claims 83 tests in test_hd_time_entry.py but actual count is 81 (3 moved to test_utils.py by task-189). Add cross-reference annotation noting the move.

### P2: Tombstone comments in test_hd_time_entry.py
Lines 1283-1288 contain 6 lines of moved-to comments that duplicate git history. Consider removing.

### Systemic recommendation
Implement a pre-commit hook comparing staged files against story File List to break the recursive pollution cycle.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #202

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: story-189 File List expanded from 4 to 16 entries — all 12 undeclared files now listed with "UNDECLARED commit scope pollution" annotations. Full list confirmed from `git show 9591cb7ef --name-only`.
- **P1-2 fixed**: Wrong path `helpdesk/helpdesk/tests/test_utils.py` corrected to `helpdesk/tests/test_utils.py` in both story-189 Change Log and File List entries.
- **P1-3 fixed**: story-171 completion notes updated with cross-reference annotation: the 3 tests added by task-171 (TestEnsureHelpersRolePollutionGuard) were subsequently moved to `helpdesk/tests/test_utils.py` by task-189, leaving `test_hd_time_entry.py` at 80 tests (not 83 as originally stated).
- **P2 fixed**: Removed 6-line tombstone comment block (lines 1283-1288) from `test_hd_time_entry.py` — these moved-to comments duplicate information already captured in git history and story artifacts.

### Change Log

- `_bmad-output/implementation-artifacts/story-189-fix-p1-5th-recursive-commit-scope-pollution-in-task-171-unde.md`: Fixed wrong path `helpdesk/helpdesk/tests/test_utils.py` → `helpdesk/tests/test_utils.py` in Change Log (P1-2); expanded File List from 4 to 16 entries adding all 12 undeclared files with UNDECLARED annotations (P1-1).
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md`: Added cross-reference annotation to P2-4 completion note — 83-test count updated with note that 3 tests were moved to test_utils.py by task-189 leaving 80 tests in test_hd_time_entry.py (P1-3).
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Removed 6-line tombstone comment block at end of file (P2).

### File List

- `_bmad-output/implementation-artifacts/story-189-fix-p1-5th-recursive-commit-scope-pollution-in-task-171-unde.md` (modified — P1-1, P1-2: expanded File List to 16 entries, fixed wrong path)
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md` (modified — P1-3: cross-reference annotation added to completion notes)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified — P2: removed 6-line tombstone comment block)
- `_bmad-output/implementation-artifacts/story-202-fix-p1-6th-recursive-commit-scope-pollution-in-task-189-wron.md` (self — story tracking file)
