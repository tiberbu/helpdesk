# Story: QA: Fix: P1 4th recursive commit-scope pollution in story-158 + incomplete File List

Status: done
Task ID: mn3evy0i6nw4hv
Task Number: #178
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:45:11.694Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #176: Fix: P1 4th recursive commit-scope pollution in story-158 + incomplete File Lists in stories 133/158**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-176-fix-p1-4th-recursive-commit-scope-pollution-in-story-158-inc.md`
Run Playwright browser tests to verify each acceptance criterion.

### Files changed
files modified: story-133, story-158, story-176 (this story file). No unrelated files touched.
file updated (Status: done, tasks checked, Change Log, File List, Completion Notes):**
files modified — stopping the recursive scope pollution pattern.

### Test steps
1. Login to the app (see docs/testing-info.md for credentials)
2. Navigate to the relevant pages
3. Test each acceptance criterion from the story file
4. Check for regressions in related functionality
5. Verify no console errors

### Deliverable
Produce `docs/qa-report-task-176.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

### If P0/P1 issues found
Create a fix task using this exact command:
```
curl -b /tmp/ccs.cookie -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d '{"title":"Fix: [issue summary]","description":"[paste QA findings]","workdir":"/home/ubuntu/bmad-project/helpdesk","status":"bmad_workflow","notes":"[bmad-workflow:quick-dev]","chain_id":"mn3ampnp78k75o","sort_order":999}'
```

## Acceptance Criteria

- [x] Login to the app (see docs/testing-info.md for credentials)
- [x] Navigate to the relevant pages
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Tasks / Subtasks

- [x] Login to the app (see docs/testing-info.md for credentials)
- [x] Navigate to the relevant pages
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Dev Notes



### References

- Task source: Claude Code Studio task #178

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review of task #176 commit `fb0c46668` completed. Verdict: **FAIL** with 3 P1, 4 P2, 5 P3 findings.
- **Critical finding**: Task #176 is the **5th recursive instance** of commit-scope pollution — the very defect it was created to stop. Commit touches 8 files but File List declares 3. Five out-of-scope files include 3 Python source code changes (`utils.py`, `hd_time_entry.py`, `test_close_tickets.py`).
- **False audit claim**: Completion Notes state "No source code changes; no regressions possible. This is a documentation-only fix" — factually false given the 3 Python files modified with behavioral changes.
- **Breaking change**: `is_agent()` in `utils.py` now raises `ValueError` when `user_roles` is passed for non-session user — undocumented breaking behavioral change bundled silently.
- Full report: `docs/qa-report-task-176.md`
- P1 issues found — chained fix task created.

### Change Log

- `docs/qa-report-task-176.md` — created QA report with 12 findings (3 P1, 4 P2, 5 P3)

### File List

- `docs/qa-report-task-176.md` — adversarial QA report for task #176
- `_bmad-output/implementation-artifacts/story-178-qa-fix-p1-4th-recursive-commit-scope-pollution-in-story-158-.md` — this story file (status update)
