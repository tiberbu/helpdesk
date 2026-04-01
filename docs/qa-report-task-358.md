# QA Report: Task #358 — Support Level Management UI

**Feature:** CRUD page for HD Support Level + auto-escalation config
**QA Date:** 2026-04-01
**QA Depth:** 1/1 (max depth)
**Tested By:** QA Engineer (Playwright MCP)
**Build Status:** Pass (reported by dev)

---

## Acceptance Criteria Results

### AC1: Support Levels link in Settings sidebar
**PASS**

- "Support Levels" tab appears under "App Settings" section in the Settings modal
- Uses LucideLayers icon, consistent with other settings tabs
- Accessible via: Profile menu > Settings > App Settings > Support Levels
- Evidence: [Screenshot 01](../test-screenshots/task-362-01-support-levels-list.png)

### AC2: List view showing all HD Support Level records
**PASS**

- All 4 seed levels displayed correctly:
  | Order | Level Name | Display Name | Escalation | Auto-Escalate |
  |-------|-----------|-------------|------------|---------------|
  | 0 | L0 - Sub-County | Sub-County Support | Allowed | 60m |
  | 1 | L1 - County | County Support | Allowed | 120m |
  | 2 | L2 - National | National Support | Allowed | — |
  | 3 | L3 - Engineering | Engineering | Terminal | — |
- Columns: Order, Level Name, Display Name, Escalation, Auto-Escalate
- Evidence: [Screenshot 01](../test-screenshots/task-362-01-support-levels-list.png)

### AC3: Sorted by level_order
**PASS**

- Levels displayed in ascending level_order (0, 1, 2, 3)
- Verified via code: `sortedLevels` computed uses `.sort((a, b) => a.level_order - b.level_order)`

### AC4: Visual hierarchy display
**PASS**

- Visual hierarchy shows: `L0 L0 - Sub-County → L1 L1 - County → L2 L2 - National → L3 L3 - Engineering [Terminal]`
- Arrow icons (blue) between levels with escalation allowed
- Red "Terminal" badge shown for the last level (when `allow_escalation_to_next = 0`)
- When a new level was added (L4), the hierarchy updated dynamically and Terminal badge moved
- Evidence: [Screenshot 01](../test-screenshots/task-362-01-support-levels-list.png), [Screenshot 04](../test-screenshots/task-362-04-after-create.png)

### AC5: Create new support level
**PASS**

- "New" button opens create form with all fields
- Fields present: Level Name (required), Level Order (required, auto-defaults to next available), Display Name, Color, Allow Escalation to Next Level, Auto-Escalate on SLA Breach, Auto-Escalate After (Minutes)
- Save button disabled until required fields filled
- Successfully created "L4 - QA Test Level" with Display Name "QA Test Tier"
- New level appeared in list and hierarchy after save
- Evidence: [Screenshot 03](../test-screenshots/task-362-03-new-form.png), [Screenshot 04](../test-screenshots/task-362-04-after-create.png)

### AC6: Edit existing levels
**PASS**

- Clicking a row opens the edit form with all fields pre-populated
- Verified L0 edit form: Level Name "L0 - Sub-County", Order 0, Display Name "Sub-County Support", Allow Escalation checked, Auto-Escalate on SLA Breach checked, Auto-Escalate 60 minutes
- Verified L3 edit form: Level Name "L3 - Engineering", Order 3, Display Name "Engineering", Allow Escalation unchecked
- Back button returns to list
- Evidence: [Screenshot 02](../test-screenshots/task-362-02-edit-form.png)

### AC7: Delete levels (with confirmation)
**PASS (with P2 caveat)**

- **Edit form Delete button**: Works correctly. Shows confirmation dialog "Delete Support Level — Are you sure you want to delete this support level? This action cannot be undone." with Confirm button. Successfully deleted L4 test level.
- **Dropdown Delete (list view)**: Uses a two-click confirm pattern but has a race condition bug — the `@click.stop="isConfirmingDelete = false"` on the dropdown trigger button resets the flag before the menu re-renders, making the second-click confirm unreachable. See P2 issue below.
- Evidence: [Screenshot 06](../test-screenshots/task-362-06-delete-confirm.png)

### AC8: yarn build passes
**PASS** (reported by dev: 29.35s, no new errors)

---

## Issues Found

### P2: Dropdown delete in list view is non-functional (workaround exists)
- **File:** `desk/src/components/Settings/SupportLevels/SupportLevelsList.vue`
- **Line:** 135
- **Issue:** `@click.stop="isConfirmingDelete = false"` on the dropdown trigger button resets the `isConfirmingDelete` ref every time the dropdown opens. The two-click delete pattern (`deleteLevel` sets `isConfirmingDelete = true` on first click, expects second click) never reaches the second state because opening the dropdown again resets the flag.
- **Severity:** P2 — functional bug, but workaround exists (delete from edit form works perfectly with confirmation dialog)
- **No fix task created** per rules (P2 only).

---

## Console Errors
- All errors are `socket.io` connection refused (ERR_CONNECTION_REFUSED) — infrastructure issue (socketio not running), unrelated to Support Levels feature.
- **No application-level JavaScript errors** related to this feature.

---

## Regression Check
- Settings modal still functions correctly
- Other settings tabs (Teams, SLA, etc.) still accessible
- Navigation sidebar unaffected

---

## Screenshots
1. `test-screenshots/task-362-01-support-levels-list.png` — List view with hierarchy and all 4 levels
2. `test-screenshots/task-362-02-edit-form.png` — Edit form for L0 - Sub-County
3. `test-screenshots/task-362-03-new-form.png` — New support level form
4. `test-screenshots/task-362-04-after-create.png` — List after creating L4 - QA Test Level
5. `test-screenshots/task-362-05-after-delete.png` — List showing dropdown delete did not take effect
6. `test-screenshots/task-362-06-delete-confirm.png` — Delete confirmation dialog from edit form

---

## Summary
**Overall: PASS** — All acceptance criteria met. One P2 bug found (dropdown delete non-functional) with a working workaround (edit form delete). No P0/P1 issues.
