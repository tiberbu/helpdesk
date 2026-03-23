# QA Report: Task #187 — Adversarial Review

**Reviewer model:** opus (adversarial review)
**Task under review:** #187 (story-187)
**Commit reviewed:** `2628c7c76`
**Date:** 2026-03-23
**Verdict:** FAIL (2 P1, 5 P2, 5 P3 findings — 12 total)

---

## Acceptance Criteria Evaluation

### AC-1: Update story-176 File List to 8 entries (label 5 out-of-scope as tooling artifacts)
**PASS** — Story-176 File List now has 8 entries: 3 in-scope, 5 out-of-scope with "(bundled by tooling; commit scope pollution artifact)" labels.

### AC-2: Correct the false "documentation-only" Completion Notes
**PASS** — The original "No source code changes; no regressions possible. This is a documentation-only fix." has been replaced with a "Corrected" section acknowledging the 3 Python source files.

### AC-3: Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented
**PASS (with caveats)** — All three were reviewed with KEEP decisions. The reasoning is documented. However, the review itself contains debatable claims — see Findings #5, #6.

### AC-4: Add task-specific AC to prevent future recurrence
**PASS** — AC-1 through AC-4 were added to story-187.

### Task-specific AC-1: Out-of-scope files labeled in File List
**FAIL** — Story-187 commits 7 files but its own File List declares only 2. See Finding #1.

### Task-specific AC-2: No false "documentation-only" claims
**PASS** — Completion Notes do not claim documentation-only.

### Task-specific AC-3: Behavioral changes to public utilities documented
**N/A** — No new behavioral changes to public utilities in this commit.

### Task-specific AC-4: Security-sensitive constant changes documented
**N/A** — No new security-sensitive constant changes in this commit.

---

## Findings

### Finding #1 — P1: 6TH RECURSIVE INSTANCE of commit-scope pollution — story-187 violates its own AC-1 in the same commit that created AC-1

**Severity:** P1
**Description:** Task #187 was created to fix the 5th recursive instance of commit-scope pollution and added AC-1 stating: "Any story whose commit includes files beyond the declared File List MUST label each out-of-scope file with '(bundled by tooling; commit scope pollution artifact)' in the File List."

The commit `2628c7c76` touches **7 files**:

| # | File | Declared in File List? |
|---|------|----------------------|
| 1 | `story-176...md` | YES |
| 2 | `story-187...md` | YES |
| 3 | `story-180...md` (NEW, 83 lines) | **NO** |
| 4 | `story-181...md` (status + completion notes updated) | **NO** |
| 5 | `story-186...md` (NEW, 84 lines) | **NO** |
| 6 | `_bmad-output/sprint-status.yaml` (multiple status changes) | **NO** |
| 7 | `docs/qa-report-task-175.md` (NEW, 111 lines) | **NO** |

The File List declares 2 files. The commit contains 7. **Five files are undeclared**, including 3 entirely new files (story-180, story-186, qa-report-task-175). This is the **6th recursive instance** of the exact defect this chain exists to fix. The task violates its own newly-created AC-1 in the same commit that introduced AC-1.

**Steps to reproduce:** `git show --stat 2628c7c76` — observe 7 files, compare to story-187 File List (2 entries).

---

### Finding #2 — P1: The recursion-breaking pattern has now failed SIX consecutive times — the process is structurally incapable of self-correction

**Severity:** P1
**Description:** The chain of "fix commit-scope pollution" tasks is:

| Task | Created to fix | Own pollution count |
|------|---------------|-------------------|
| #144 | Original pollution in story-133 | Polluted (added unrelated files) |
| #150 | Pollution in #144 | Polluted (incomplete File List) |
| #158 | Pollution in #150 | Polluted (6 unrelated files) |
| #176 | Pollution in #158 | Polluted (5 unrelated files, false docs-only claim) |
| #187 | Pollution in #176 | Polluted (5 unrelated files — this commit) |
| (next) | Pollution in #187 | (predicted: will also pollute) |

Every single fix task in this chain has committed the same defect it was created to fix. **The root cause is the automated commit staging in Claude Studio, which picks up all uncommitted changes.** No amount of documentation-level AC can fix a tooling-level defect. AC-1 through AC-4 are process rules that the AI agent demonstrably cannot follow because the tooling overrides them.

**The correct fix is one of:**
1. Use `git add <specific-files>` instead of `git add .` / `git add -A`
2. Use `git stash` before committing to isolate changes
3. Accept pollution as a permanent tooling artifact and stop creating recursive fix tasks

---

### Finding #3 — P2: Story-181 completion notes and status were modified by task-187's commit, NOT by task-181's agent

**Severity:** P2
**Description:** Story-181 is a QA adversarial-review task (#181) with its own agent model (opus). Commit `2628c7c76` (task-187, by sonnet) modifies story-181's status from `in-progress` to `done`, checks off all acceptance criteria, and populates its Completion Notes with "Adversarial review completed with 13 findings."

This means the **sonnet agent working on task-187 completed task-181's paperwork**. This is an audit trail violation — story-181's Dev Agent Record says "Agent Model Used: opus" but its completion notes were written by the sonnet model running task-187. The story file's change history attributes the completion to the wrong task.

---

### Finding #4 — P2: `docs/qa-report-task-175.md` is bundled into task-187's commit despite belonging to task-181

**Severity:** P2
**Description:** The file `docs/qa-report-task-175.md` is the QA report produced by the adversarial review in task-181. It was created by the opus agent during task-181's work, but committed as part of task-187's commit `2628c7c76`. This means:

1. `git blame docs/qa-report-task-175.md` attributes the entire file to commit `2628c7c76` (task-187), not task-181.
2. The file cannot be traced to its originating task through git history.
3. qa-report-task-175.md is a 111-line document with 13 detailed findings — a significant artifact silently bundled.

---

### Finding #5 — P2: The "KEEP, document" dispositions for P1-3 and P2-1 are retrospective justifications, not independent reviews

**Severity:** P2
**Description:** The task description asks: "Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented as separate tasks." The review concludes all three should be kept.

But the reviewer (sonnet, task-187) is the same agent family that **introduced** these changes in the first place. The review is the author reviewing their own work and concluding it was correct. Specifically:

- **P1-3 (ValueError)**: The review says "legitimate defensive guard." But the previous QA report (task-175/181, by opus) flagged this as P2 with 4 specific problems: not Frappe-friendly, bypassable when user=None, no test for the bypass, queries by `name` not `user`. Task-187's disposition doesn't address any of these 4 sub-findings.

- **P2-1 (PRIVILEGED_ROLES)**: The review says "deliberate privilege-escalation prevention." But the prior QA report flagged it as P2 Finding #8: the "fix" introduced a new manual-sync risk (DocType JSON divergence) while solving the old auto-derivation risk. Task-187 doesn't acknowledge this trade-off.

- **P2-2 (Test assertions)**: The review claims "replacement `mock_logger.warning.assert_called_once()` is a stronger assertion." But the prior QA report (task-176 review, Finding #5) specifically noted: "no new assertion verifies the WARNING-level log instead." These two claims are contradictory — either a mock assertion exists or it doesn't. Task-187 doesn't cite a line number or file to resolve the contradiction.

---

### Finding #6 — P2: AC-1 through AC-4 are unenforceable documentation theater

**Severity:** P2
**Description:** The four new ACs added to prevent future recurrence are:

- AC-1: File List must label out-of-scope files
- AC-2: Must not claim "documentation-only" when .py files are modified
- AC-3: Behavioral changes must be documented
- AC-4: Security-sensitive constant changes must be noted

These are process rules written in a markdown file that the AI agent reads at task start. But the defect occurs at **commit time**, not at task planning time. The agent completes its work, writes the story file correctly, and then the automated `git add + commit` bundles in extra files. The agent doesn't get a chance to update the File List after the commit because the commit is the final action.

**AC-1 is particularly absurd**: it asks the agent to label out-of-scope files in the File List, but the agent doesn't know which files will be out-of-scope until after the commit. The commit happens after the agent finishes writing the story file. This is asking the agent to predict the future.

---

### Finding #7 — P2: sprint-status.yaml shows 4 status changes for 3 different tasks, only 1 is in scope

**Severity:** P2
**Description:** The sprint-status.yaml diff in commit `2628c7c76` changes:

1. Task 180: `ready-for-dev` → `review` (OUT OF SCOPE)
2. Task 186: `ready-for-dev` → `review` (OUT OF SCOPE)
3. Task 187: `in-progress` → `review` (IN SCOPE)
4. Task 190: new line added (OUT OF SCOPE)

Three of the four changes are for unrelated tasks. This is the same sprint-status pollution pattern found in every predecessor commit.

---

### Finding #8 — P3: The Change Log only documents changes to story-176 and story-187, omitting 5 other files modified

**Severity:** P3
**Description:** Story-187's Change Log lists 2 entries:
- `story-176...md` — File List expanded
- `story-187...md` — AC, Change Log, etc.

It omits the 5 other files modified in the commit: story-180 (new), story-181 (updated), story-186 (new), sprint-status.yaml, qa-report-task-175.md. This is the same "incomplete Change Log" pattern flagged in the prior QA reports (findings #9 in task-176 report).

---

### Finding #9 — P3: No browser-level testing was performed by task-187 (a dev task), and no evidence of backend test execution

**Severity:** P3
**Description:** Task-187 is a documentation-fix task, so no backend code was changed. However, the task description's AC-3 asks the agent to "Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented." A proper review would have run the test suites to verify that the existing changes still pass — but there's no evidence in the story file that any tests were executed during the review. The Completion Notes make claims about test behavior ("replacement mock_logger.warning.assert_called_once() is a stronger assertion") without citing test execution results.

**QA verification:** This adversarial reviewer ran `bench run-tests --app helpdesk --module helpdesk.tests.test_utils` and confirmed 9/9 pass. The prior QA report (task-175) confirms 83/83 hd_time_entry tests pass and 6/6 test_utils pass (now 9/9 after additions in later commits).

---

### Finding #10 — P3: The P2-2 disposition ("NOT a weakening") is unverifiable without a file path and line number

**Severity:** P3
**Description:** The Completion Notes for P2-2 state: "The replacement `mock_logger.warning.assert_called_once()` is a stronger assertion." But the story doesn't cite which file, which test method, or which line contains this replacement assertion. The claim is unverifiable from the story file alone. A reader must independently run `git show fb0c46668 -- test_close_tickets.py` to check whether this mock assertion actually exists.

---

### Finding #11 — P3: Story-187 doesn't cross-reference the prior QA report (docs/qa-report-task-176.md) that created it

**Severity:** P3
**Description:** Story-187's description says "From adversarial review task #178 (docs/qa-report-task-176.md)". But the QA report is `docs/qa-report-task-176.md` which was the output of task #178 reviewing task #176. The story doesn't reference the specific finding numbers from that report (P1-1 through P2-2) in its AC or Tasks, making it hard to trace which findings map to which AC.

---

### Finding #12 — P3: The story's "References" section only lists "Task source: Claude Code Studio task #187" with no links to predecessor context

**Severity:** P3
**Description:** The References section should link to:
- `docs/qa-report-task-176.md` (the QA report that triggered this task)
- Story-176 (the story being corrected)
- Story-175 QA report (referenced in the dispositions)

Instead, the only reference is a generic "Claude Code Studio task #187" which provides zero traceability.

---

## Test Results

| Test Suite | Result |
|---|---|
| `helpdesk.tests.test_utils` | 9/9 PASS |
| App HTTP health check | 200 OK at `http://helpdesk.localhost:8004/` |
| API login | PASS (Administrator) |
| API resource query (HD Ticket) | PASS (returns data) |

---

## Console Errors

Playwright MCP unavailable. API-level testing shows no server errors from standard endpoints.

---

## Browser Testing

Playwright MCP tools not available in this environment. App verified accessible via:
- HTTP 200 at `http://helpdesk.localhost:8004/`
- Successful Administrator login via API
- HD Ticket resource API returns data

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|-----------|
| P1 | 2 | 6th recursive commit-scope pollution (violates own AC-1 in same commit), structurally unfixable process |
| P2 | 5 | Cross-task audit trail violation (story-181 completed by wrong agent), bundled QA report, rubber-stamp dispositions, unenforceable ACs, sprint-status pollution |
| P3 | 5 | Incomplete Change Log, no test execution evidence, unverifiable claims, missing cross-references |

**The fundamental failure:** Task #187 was created to fix the 5th recursive instance of commit-scope pollution. It became the 6th. It added 4 new ACs to prevent this from happening, then violated AC-1 in the same commit that created it. The chain of fix-the-fix tasks is now at 6 iterations with 0 successful executions. The problem is structural (automated commit staging) and cannot be fixed by documentation-level process rules.

**Recommendation:** Stop the recursion permanently. Either:
1. Fix the tooling (use `git add <specific-files>` instead of staging everything)
2. Accept the pollution as a known tooling limitation and document it ONCE in a project-level note, then stop creating recursive fix tasks

No P0 issues found. The P1 findings are process/documentation failures, not production code defects. No fix task is warranted because the fix would itself become the 7th recursive instance.

---

## Screenshots

Playwright MCP unavailable. No screenshots taken.
