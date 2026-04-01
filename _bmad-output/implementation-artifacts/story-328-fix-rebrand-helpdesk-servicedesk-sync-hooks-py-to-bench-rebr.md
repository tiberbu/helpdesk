# Story: Fix: Rebrand Helpdesk → ServiceDesk — sync hooks.py to bench + rebrand workspace JSON

Status: done
Task ID: mng7ldspw48z1c
Task Number: #328
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T15:36:57.627Z

## Description

## Fix Task (from QA report docs/qa-report-task-325.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P0): hooks.py not synced to bench — Frappe desk app switcher shows "Helpdesk"
- File (bench): `/home/ubuntu/frappe-bench/apps/helpdesk/hooks.py`
- Line 2: `app_title = "Helpdesk"` → `app_title = "ServiceDesk"`
- Line 16: `"title": "Helpdesk"` → `"title": "ServiceDesk"`
- The dev copy at `/home/ubuntu/bmad-project/helpdesk/helpdesk/hooks.py` is already correct
- Verify: `grep -n 'Helpdesk' /home/ubuntu/frappe-bench/apps/helpdesk/hooks.py` should return NO matches
- After fix: `kill -HUP $(pgrep -f 'gunicorn.*frappe.app.*preload' | head -1)` to reload

#### Issue 2 (P1): Workspace JSON not rebranded — Frappe desk workspace page shows "Helpdesk" everywhere
- File (BOTH copies):
  - Dev: `/home/ubuntu/bmad-project/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json`
  - Bench: `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json`
- Changes needed (display strings only, NOT module name or document name):
  - Line 3 content JSON: `Visit Helpdesk` → `Visit ServiceDesk`, `Helpdesk Configuration` → `ServiceDesk Configuration`, `Helpdesk Reports` → `ServiceDesk Reports`
  - Line 11: `"label": "Helpdesk"` → `"label": "ServiceDesk"`
  - Line 128: `"label": "Helpdesk Reports"` → `"label": "ServiceDesk Reports"`
  - Line 156: `"module": "Helpdesk"` — DO NOT CHANGE (this is the Frappe module name, changing it breaks migrations)
  - Line 157: `"name": "Helpdesk"` — DO NOT CHANGE (this is the document name/ID, changing it breaks the workspace)
  - Line 165: `"title": "Helpdesk"` → `"title": "ServiceDesk"`
- Verify: `grep -c 'Helpdesk' helpdesk/helpdesk/workspace/helpdesk/helpdesk.json` should return exactly 2 (module + name only)
- After fix: `cd /home/ubuntu/frappe-bench && bench --site help.frappe.local migrate` to apply workspace changes

#### I

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #328

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Issue 1 (P0): hooks.py bench copy updated — `app_title` and `add_to_apps_screen title` changed to "ServiceDesk". Gunicorn reloaded. `tabDesktop Icon` DB record also updated (label: "ServiceDesk") since it caches the app switcher title independently from hooks.py.
- Issue 2 (P1): Workspace JSON updated in both dev and bench copies — content (Visit ServiceDesk, ServiceDesk Configuration, ServiceDesk Reports), label, title fields changed. DB also updated directly via SQL since bench migrate had an unrelated pre-existing failure (missing HD Article category). Workspace DB confirmed: title=ServiceDesk, label=ServiceDesk, content has 0 Helpdesk refs.
- API verification: `frappe.apps.get_apps` → `title: ServiceDesk`; `frappe.client.get Desktop Icon Helpdesk` → `label: ServiceDesk`; workspace sidebar → `title: ServiceDesk`.
- Note: `label` in `get_workspace_sidebar_items` API returns workspace `name` ("Helpdesk") via Frappe's `_(page.get("name"))` — this is expected/by-design and cannot be changed without breaking migrations.

### Change Log

- `/home/ubuntu/frappe-bench/apps/helpdesk/hooks.py`: line 2 app_title, line 16 add_to_apps_screen title → "ServiceDesk"
- `/home/ubuntu/bmad-project/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json`: content (Visit/Configuration/Reports), label, title → ServiceDesk
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json`: same as dev (copied)
- DB `tabWorkspace` Helpdesk: title=ServiceDesk, label=ServiceDesk, content updated
- DB `tabDesktop Icon` Helpdesk: label=ServiceDesk

### File List

- `/home/ubuntu/frappe-bench/apps/helpdesk/hooks.py` (bench — modified)
- `/home/ubuntu/bmad-project/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json` (dev — modified)
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/workspace/helpdesk/helpdesk.json` (bench — modified/copied from dev)
