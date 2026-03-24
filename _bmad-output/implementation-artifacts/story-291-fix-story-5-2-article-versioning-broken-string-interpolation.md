# Story: Fix: Story 5.2 Article Versioning — Broken __() string interpolation in ArticleVersionHistory.vue

Status: in-progress
Task ID: mn4fgomq7q1nhu
Task Number: #291
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T09:44:01.204Z

## Description

## Fix Task (from QA report docs/qa-report-task-43.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: __() translation calls pass arrays instead of spread arguments

The `translate()` function in `translation.ts` uses rest params (`...args: string[]`), but `ArticleVersionHistory.vue` passes arrays as a single argument. For multi-arg calls, `{0}` gets the stringified array and `{1}+` are undefined.

**File:** `desk/src/components/knowledge-base/ArticleVersionHistory.vue`

##### Fix 1a — Line 171 (diff header, VISIBLY BROKEN)
- Current: `__("Compare v{0} ({1}) vs v{2} ({3})", [diffVersions[0].version_number, formatTs(diffVersions[0].timestamp), diffVersions[1].version_number, formatTs(diffVersions[1].timestamp)])`
- Expected: `__("Compare v{0} ({1}) vs v{2} ({3})", diffVersions[0].version_number, formatTs(diffVersions[0].timestamp), diffVersions[1].version_number, formatTs(diffVersions[1].timestamp))`
- Shows as: `Compare v1,Mar 24, 2026 12:33 PM,6,Mar 24, 2026 12:24 PM ({1}) vs v{2} ({3})`

##### Fix 1b — Line 334 (revert dialog message, VISIBLY BROKEN)
- Current: `__("This will restore the article content from version #{0} ({1}) and create a new version record. The article status will not change.", [v.version_number, formatTs(v.timestamp)])`
- Expected: `__("This will restore the article content from version #{0} ({1}) and create a new version record. The article status will not change.", v.version_number, formatTs(v.timestamp))`

##### Fix 1c — Line 42 (versions selected count, works accidentally but should be fixed)
- Current: `__("{0} versions selected", [selectedVersions.length])`
- Expected: `__("{0} versions selected", selectedVersions.length)`

##### Fix 1d — Line 350 (revert toast, works accidentally but should be fixed)
- Current: `__("Article reverted to version #{0}", [v.version_number])`
- Expected: `__("Article reverted to version #{0}", v.version_number)`

### Verif

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #291

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
