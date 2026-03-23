# QA Adversarial Review Report: Task #158

**Reviewed artifact:** `_bmad-output/implementation-artifacts/story-158-fix-p1-recursive-commit-scope-pollution-in-story-150-p2-inco.md`
**Reviewer model:** opus (adversarial)
**Date:** 2026-03-23
**Verdict:** MIXED -- 3 ACs pass, but the fix repeats the very defect class it was created to address.

---

## Acceptance Criteria Evaluation

### AC1: Story-150 File List expanded from 3 to 7 entries
**PASS**

Story-150's File List now contains 7 entries matching the 7 files in commit `95e55885a`:
1. story-133 (test count correction)
2. story-144 (File List expanded)
3. story-150 (this story file)
4. story-149 (sprint sync)
5. story-152 (sprint sync)
6. sprint-status.yaml
7. docs/qa-report-task-149.md

Evidence: `git show --name-only 95e55885a` lists exactly these 7 files. File List verified via `grep "^- \`" story-150-*.md` returning 7 lines.

### AC2: Story-144 Completion Notes corrected "7 string inf/nan tests" to "5"
**PASS**

The diff of commit `752897a89` shows story-144 line changed from:
> `the except (ValueError, OverflowError) fix + 7 string inf/nan tests`

to:
> `the except (ValueError, OverflowError) fix + 5 string inf/nan rejection tests`

No other stale "7 string" references remain in story-144.

### AC3: Story-133 HD Admin test attribution added
**PARTIAL PASS / P2 finding**

The Change Log (line 65) correctly adds: "and 2 HD Admin tests (`test_hd_admin_can_stop_timer`, `test_hd_admin_can_get_summary`)" and the Completion Notes bullet correctly enumerates them. However, the File List (line 72) was NOT updated and still reads:

> `(da95326be) 5 string inf/nan rejection tests + 1 scientific notation doc test + 2 billable clamp tests`

Missing: "+ 2 HD Admin tests". This is an inconsistency within the same file between Change Log (complete) and File List (incomplete).

---

## Adversarial Findings (10+ issues)

### Finding 1 -- P1: Task #158 commit bundles 6 unrelated files (same recursive defect)
**Severity: P1**

Commit `752897a89` touches **10 files** but only **4 are in scope** (story-133, story-144, story-150, and story-158 itself). The remaining 6 files are unrelated:

| File | Relationship to task |
|---|---|
| `story-128-qa-fix-p1-performance-regression-*.md` | New file, unrelated QA story |
| `story-153-qa-fix-p1-delete-entry-*.md` | Status/content changes to unrelated QA story |
| `story-159-qa-fix-delete-entry-dry-violation-*.md` | New file, unrelated QA story |
| `_bmad-output/sprint-status.yaml` | Sprint status update (arguably in scope but not listed) |
| `docs/qa-report-story-127-adversarial-review.md` | New file, unrelated QA report |
| `docs/qa-report-task-146.md` | New file, unrelated QA report |

This is the **fourth recursive instance** of the exact defect class this chain of tasks was created to fix. Task #154 flagged task #150 for bundling 4 unrelated files. Task #158 was created to fix that. Task #158's own commit bundles **6** unrelated files -- worse than the original offense.

### Finding 2 -- P1: Story-158 File List is incomplete (lists 4 of 10 files)
**Severity: P1**

Story-158's File List contains only 4 entries:
1. story-150 (File List expanded)
2. story-144 ("7" corrected to "5")
3. story-133 (HD Admin test attribution)
4. story-158 (this story file)

But the commit touches 10 files. This is the same P2 defect reported in the task description (story-150 listed 3 of 7), now repeated by the fix itself. The 6 missing files are listed in Finding 1 above.

### Finding 3 -- P2: Story-133 File List still omits HD Admin test count
**Severity: P2**

Task #158's stated goal was to add HD Admin test attribution to story-133. The Change Log was updated correctly (line 65 says "and 2 HD Admin tests"), but the File List summary on line 72 still reads:

```
(da95326be) 5 string inf/nan rejection tests + 1 scientific notation doc test + 2 billable clamp tests
```

The total for da95326be is actually 10 tests (5 + 1 + 2 + 2), but the File List only accounts for 8. The HD Admin tests are missing from the File List despite being the explicit deliverable of this task.

### Finding 4 -- P2: Story-150 Completion Notes undercount da95326be tests
**Severity: P2**

Story-150 Completion Notes (line 54) says the old "7" count was wrong because it "incorrectly included 2 billable clamping tests and/or the 1 scientific notation documentation test." This explanation is incomplete -- da95326be actually added 10 tests total (5 inf/nan + 1 scientific notation + 2 billable clamp + 2 HD Admin), not 7 or 8. The explanation doesn't mention the 2 HD Admin tests at all, even though they were part of the original mis-count's denominator.

### Finding 5 -- P2: No cross-reference chain between story-154 (QA) and story-158 (fix)
**Severity: P2**

Story-158's Description section references "adversarial review task #154 (docs/qa-report-task-150.md)" but story-154's story file is never updated with a pointer back to story-158 as the implementing fix. This breaks bidirectional traceability.

### Finding 6 -- P2: sprint-status.yaml changes are undocumented in story-158
**Severity: P2**

Commit `752897a89` modifies `_bmad-output/sprint-status.yaml` (8 lines changed), but story-158's Change Log makes no mention of it. Sprint status changes are part of the commit scope and should be documented.

### Finding 7 -- P3: Acceptance Criteria are generic, not specific to the task
**Severity: P3**

Story-158's Acceptance Criteria are:
- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

These are boilerplate criteria auto-generated by the task system. None are specific to the actual deliverables (e.g., "story-150 File List has 7 entries", "story-144 says '5' not '7'", "story-133 mentions HD Admin tests"). The task was checked off against vague criteria that don't verify the actual fix.

### Finding 8 -- P3: Story-158 does not mention the P2 "Decimal bypass" finding from the task description
**Severity: P3**

The task description (from QA report) includes a "P2: 2 HD Admin tests in da95326be unaccounted in story-133 audit" finding and no explicit mention of whether the Decimal bypass wontfix note was verified as still accurate. The review scope should have confirmed the wontfix note added in story-150 is still correct.

### Finding 9 -- P3: The "Files changed" section in story-162 (QA story) is garbled
**Severity: P3**

Story-162's "Files changed" section reads:
> `file updated**: Status -> done, acceptance criteria checked off, Completion Notes / Change Log / File List all populated.`

This appears to be a copy-paste artifact. The leading `file updated**:` is not valid markdown and doesn't describe which files were changed. It should list the 3 story files that were modified.

### Finding 10 -- P3: Story chain is generating more audit debt than it resolves
**Severity: P3 (process)**

The chain of fix tasks (133 -> 140/QA -> 144 -> 147/QA -> 150 -> 154/QA -> 158 -> 162/QA) has been running for 8+ iterations, each time finding that the fix introduced the same category of defect it was meant to resolve. Each iteration adds 1-3 new unrelated files to the commit, generates a new QA report flagging it, and spawns another fix. The process has become self-perpetuating: each fix creates new audit debt equal to or greater than what it resolves.

### Finding 11 -- P3: da95326be total test count (10) is never stated in any story
**Severity: P3**

Multiple stories discuss subsets of the 10 tests added in `da95326be` (5 inf/nan, 1 scientific notation, 2 billable clamp, 2 HD Admin), but no story file ever states the total (10). This makes it impossible for a future reader to quickly verify completeness without re-running `git diff`.

### Finding 12 -- P2: No verification that the 2 tests actually exist and pass
**Severity: P2**

Task #158 adds attribution for `test_hd_admin_can_stop_timer` and `test_hd_admin_can_get_summary` to story-133's notes, but the task record contains no evidence that these tests were actually verified to exist in the current codebase or that they pass. The task is purely documentation-level; a diligent fix would have included a test run confirming the tests referenced actually work.

---

## Summary

| Severity | Count | Description |
|---|---|---|
| P1 | 2 | Recursive commit-scope pollution (6 unrelated files) + incomplete File List (4 of 10) |
| P2 | 4 | Story-133 File List omits HD Admin tests; story-150 undercount; missing cross-reference; undocumented sprint-status change; no test verification |
| P3 | 5 | Generic ACs; garbled story-162 description; self-perpetuating audit chain; missing total count; missing Decimal bypass verification |
| **Total** | **11** | |

## Recommendation

The P1 findings represent the **fourth consecutive recursive instance** of the same defect class. At this point, creating yet another fix task would likely produce a fifth instance. The recommended course of action is:

1. **Stop the recursion.** Accept that automated commit tooling bundles unrelated staged files and document this as a known process limitation.
2. **Batch-fix** all File List / Completion Notes inconsistencies across stories 133, 150, and 158 in a single deliberate commit that touches ONLY those 3 files.
3. **Add a process note** to the sprint documentation that story file audits are best-effort and commit scope pollution is a tooling artifact, not a human error.

---

*Report generated by adversarial review (opus model), task #162.*
