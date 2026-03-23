# Story: Fix: P1 7th recursive commit-scope pollution in task-202 + stale 80-test count + ignored pre-commit hook recommendation

Status: done
Task ID: mn3fy95vfid0s8
Task Number: #210
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:09:54.788Z

## Description

## From adversarial review task #205 (docs/qa-report-task-202.md)

### P1-1: 7th recursive commit-scope pollution
Commit f26716cd9 modifies 15 files but story-202 File List declares only 4. The 11 undeclared files include 6 story artifacts, sprint-status.yaml, and 3 QA reports. Update story-202 File List to enumerate all 15 files.

### P1-2: Systemic pre-commit hook recommendation ignored
The QA report from task-194 recommended a pre-commit hook to break the pollution cycle. Task-202 silently dropped this. Either implement a lightweight hook or add an explicit policy decision to the project docs explaining why story File Lists need not track auto-generated bmad/QA artifacts.

### P1-3: Stale test count in story-171 cross-reference
Story-171 line 69 says test_hd_time_entry.py has 80 tests after the move, but actual count is 81. The 81st test was added by commit bf2e19d09 (task-196). Fix the count or remove absolute counts from cross-references.

### Systemic recommendation
Consider adding a policy document or .gitattributes rule that excludes _bmad-output/ and docs/qa-report-*.md from File List tracking requirements, which would break the infinite pollution loop permanently.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #210

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: story-202 File List expanded from 4 to 15 entries — all 11 undeclared files now listed with "UNDECLARED commit scope pollution" annotations. Full list confirmed from `git show f26716cd9 --name-only`.
- **P1-2 fixed**: Created `docs/file-list-tracking-policy.md` — explicit policy document stating that `_bmad-output/implementation-artifacts/story-*.md`, `_bmad-output/sprint-status.yaml`, and `docs/qa-report-*.md` are excluded from File List tracking requirements, with rationale explaining the recursive-pollution root cause. This is the permanent systemic fix.
- **P1-3 fixed**: story-171 line 69 cross-reference updated — "80 tests" corrected to reflect that task-196 (commit bf2e19d09) subsequently added a 81st test to `test_hd_time_entry.py`. Note appended to existing task-189 cross-reference annotation.

### Change Log

- `_bmad-output/implementation-artifacts/story-202-fix-p1-6th-recursive-commit-scope-pollution-in-task-189-wron.md`: Expanded File List from 4 to 15 entries — added 11 undeclared files with UNDECLARED annotations (P1-1).
- `docs/file-list-tracking-policy.md`: New policy document defining File List tracking exclusions for auto-generated BMAD/QA artifacts (P1-2 systemic fix).
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md`: Updated P2-4 completion note — appended task-196 cross-reference noting the 81st test, correcting the stale "80 tests" claim (P1-3).

### File List

- `_bmad-output/implementation-artifacts/story-202-fix-p1-6th-recursive-commit-scope-pollution-in-task-189-wron.md` (modified — P1-1: File List expanded to 15 entries)
- `docs/file-list-tracking-policy.md` (created — P1-2: policy document for File List tracking exclusions)
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md` (modified — P1-3: stale 80-test count corrected to 81 with task-196 cross-reference)
- `_bmad-output/implementation-artifacts/story-210-fix-p1-7th-recursive-commit-scope-pollution-in-task-202-stal.md` (self — story tracking file)
