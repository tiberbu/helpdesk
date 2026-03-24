# Story: QA: Story 4.1: Business Hours SLA Calculation Engine

Status: done
Task ID: mn3uhduegdiu9x
Task Number: #237
Workflow: playwright-qa
Model: opus
Created: 2026-03-23T23:56:43.228Z

## Description

## QA Report Task -- DO NOT MODIFY CODE

**Review task #38: Story 4.1: Business Hours SLA Calculation Engine**
**QA Depth: 1/1** (max depth reached = no further QA cycles)

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-38-story-4-1-business-hours-sla-calculation-engine.md`

### Deliverable
Produce `docs/qa-report-task-38.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

## Acceptance Criteria

- [x] Navigate to the relevant pages for this feature (API-tested via curl at http://help.frappe.local)
- [x] Test each acceptance criterion using API interactions and bench console
- [x] Check console for errors
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Tasks / Subtasks

- [x] Login to app via curl (http://help.frappe.local)
- [x] Read all implementation files
- [x] Run 21 unit tests -- all pass (0.006s)
- [x] Run 3 performance tests -- all pass (0.009s)
- [x] Test SLA API endpoints (timezone field, working hours, holiday list, recalculation)
- [x] Verify permission checks on recalculation API (auth + unauth)
- [x] Run end-to-end integration tests via bench console (calc_elapsed_time edge cases)
- [x] Verify code quality and architecture
- [x] Check regressions (42 utils imports, hooks, patches, bench sync, frontend loads)
- [x] Write QA report at docs/qa-report-task-38.md

## Dev Notes

- Playwright MCP tools were unavailable in the environment. All testing done via curl API calls, bench console integration tests, and unit test suites.
- All 4 acceptance criteria PASS.
- No P0/P1 issues found. Two minor P2/P3 issues noted in the QA report.

### References

- Task source: Claude Code Studio task #237

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- All 4 ACs verified: business hours calculation, holiday exclusion, pause-on-status compatibility, performance (<5s for 1000 tickets)
- 21 unit tests + 3 performance tests pass
- 4 end-to-end integration tests via bench console pass (within-hours, weekend span, outside-hours, pre-hours clipping)
- API testing confirms: timezone field on SLAs (18 IANA zones), holiday list linked, recalculation endpoint works, permissions enforced
- Two minor issues: P2 stale utils.py in bench (deployment artifact), P3 unused _normalize_time import
- No fix task created (no P0/P1 issues)

### Change Log

- 2026-03-24: Created QA report at docs/qa-report-task-38.md
- 2026-03-24: Updated QA report with end-to-end bench console tests and new test URL (help.frappe.local)

### File List

| File | Status |
|------|--------|
| `docs/qa-report-task-38.md` | Created/Updated |
