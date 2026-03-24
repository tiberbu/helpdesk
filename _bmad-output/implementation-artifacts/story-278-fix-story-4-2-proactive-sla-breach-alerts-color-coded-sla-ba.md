# Story: Fix: Story 4.2 Proactive SLA Breach Alerts — Color-coded SLA badges not rendering on Tickets list

Status: done
Task ID: mn4cohbi4xjslv
Task Number: #278
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T08:26:06.129Z

## Description

## Fix Task (from QA report docs/qa-report-task-39.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Badge component VNodes not rendering in ListViewBuilder custom column handlers
- File: `desk/src/pages/ticket/Tickets.vue`
- Lines: 211-287 (`handle_resolution_by_field`) and 180-208 (`handle_response_by_field`)
- Current: Uses `h(Badge, { label, theme: "red", variant: "outline" })` which renders as plain text in ListViewBuilder cells
- Expected: Badge should render with colored styling (red/orange/yellow outline badges)
- Root cause: ListViewBuilder extracts text content from component VNodes instead of rendering them as components. The existing `status` column custom renderer works because it uses plain HTML elements (`h("div", ...)`, `h("span", ...)`) not component VNodes.
- Fix: Replace `h(Badge, { label, theme, variant })` with equivalent plain HTML `h("span", { class: "..." }, label)` using the Badge component's computed CSS classes directly.

**Badge outline class mappings** (from `node_modules/frappe-ui/src/components/Badge/Badge.vue`):
- Base: `inline-flex select-none items-center gap-1 rounded-full whitespace-nowrap h-5 text-xs px-1.5`
- red outline: `text-ink-red-4 bg-transparent border border-outline-red-2`
- orange outline: `text-ink-amber-3 bg-transparent border border-outline-amber-2`
- green outline: `text-ink-green-3 bg-transparent border border-outline-green-2`
- blue outline: `text-ink-blue-2 bg-transparent border border-outline-blue-1`

**Changes needed in `handle_resolution_by_field()`** (lines 211-287):

Replace ALL `h(Badge, { label: X, theme: Y, variant: "outline" })` calls with:
```js
const badgeBase = 'inline-flex select-none items-center gap-1 rounded-full whitespace-nowrap h-5 text-xs px-1.5'
const badgeOutline = {
  red: 'text-ink-red-4 bg-transparent border border-outline-red-2',
  orange: 'text-ink-amber-3 bg-transparent border border-outline-amber-

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #278

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Replaced all `h(Badge, { label, theme, variant: "outline" })` VNode calls in ListViewBuilder custom column renderers with plain HTML `h("span", { class: ... })` equivalents using inline Tailwind classes from frappe-ui Badge source.
- Added `hBadge(label, theme)` helper function and `_badgeBase`/`_badgeOutlineTheme` constants before the handler functions.
- Fixed three column renderers: `agreement_status`, `response_by` (via `handle_response_by_field`), `resolution_by` (via `handle_resolution_by_field`).
- Removed unused `Badge` import from `frappe-ui`.
- Added `yellow` theme to the badge theme map (used by 30–60 min warning).
- Build passed with no TypeScript errors.

### Change Log

- `desk/src/pages/ticket/Tickets.vue`: Removed `Badge` import; added `hBadge` helper; replaced 8 `h(Badge,...)` calls with `hBadge(...)` across `agreement_status`, `handle_response_by_field`, `handle_resolution_by_field`.

### File List

- `desk/src/pages/ticket/Tickets.vue` (modified)
