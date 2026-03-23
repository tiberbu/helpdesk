# Story: Fix: P1 4th recursive commit-scope pollution in story-158 + incomplete File Lists in stories 133/158

Status: done
Task ID: mn3etoi3vgzz1v
Task Number: #176
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:38:34.849Z

## Description

## From adversarial review task #162 (docs/qa-report-task-158.md)

### P1: Task #158 commit (752897a89) bundles 6 unrelated files — 4th recursive instance
Commit touches 10 files but only 4 are in scope. 6 unrelated files: story-128, story-153, story-159, sprint-status.yaml, qa-report-story-127, qa-report-task-146. This is the 4th recursive instance of the defect this chain was created to fix.

### P1: Story-158 File List is incomplete (lists 4 of 10 files)
Same defect as P2 in story-150 and story-144.

### P2: Story-133 File List omits HD Admin tests
Change Log correctly mentions 2 HD Admin tests but File List line 72 still says "5 string inf/nan rejection tests + 1 scientific notation doc test + 2 billable clamp tests" — missing "+ 2 HD Admin tests".

### Recommendation from QA
Stop the recursion. Batch-fix all File List inconsistencies (stories 133, 158) in ONE commit touching ONLY those files. Add a process note that commit scope pollution is a tooling artifact.

### Files to modify
- story-158 File List (expand to 10 entries)
- story-133 File List line 72 (add HD Admin test count)
- Consider adding process note to sprint-status.yaml about commit scope pollution

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #176

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1 (story-158 File List)**: Expanded File List from 4 to 10 entries to reflect all files in commit `752897a89`. Added 6 out-of-scope entries (story-128, story-153, story-159, sprint-status.yaml, qa-report-story-127, qa-report-task-146) with annotation "bundled by tooling (out-of-scope; commit scope pollution artifact)" to make the pollution transparent without falsifying the record.
- **P2 (story-133 File List line 72)**: Added "+ 2 HD Admin tests" to the test count description for `test_hd_time_entry.py` in the da95326be entry. The HD Admin tests (`test_hd_admin_can_stop_timer`, `test_hd_admin_can_get_summary`) were already attributed in the Change Log and Completion Notes — this brings the File List inline with them.
- No source code changes; no regressions possible. This is a documentation-only fix.

### Change Log

- **_bmad-output/implementation-artifacts/story-158-fix-p1-recursive-commit-scope-pollution-in-story-150-p2-inco.md**: File List expanded from 4 to 10 entries; 6 out-of-scope entries labelled as tooling artifacts.
- **_bmad-output/implementation-artifacts/story-133-fix-require-int-str-overflowerror-on-inf-nan-input-p1-story-.md**: File List line 72 updated to add "+ 2 HD Admin tests" to the da95326be test count.

### File List

- `_bmad-output/implementation-artifacts/story-158-fix-p1-recursive-commit-scope-pollution-in-story-150-p2-inco.md` — File List expanded to 10 entries
- `_bmad-output/implementation-artifacts/story-133-fix-require-int-str-overflowerror-on-inf-nan-input-p1-story-.md` — File List line 72 updated with HD Admin test count
- `_bmad-output/implementation-artifacts/story-176-fix-p1-4th-recursive-commit-scope-pollution-in-story-158-inc.md` — this story file
