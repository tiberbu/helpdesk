# Story 6.2: Report Scheduling and Export

Status: ready-for-dev

## Story

As a team manager,
I want to schedule reports for email delivery and export to CSV/Excel,
so that I can share insights with stakeholders automatically without manual effort.

## Acceptance Criteria

1. **[Schedule Fields on HD Custom Report]** Given the HD Custom Report DocType (created in Story 6.1) is updated, when a developer inspects the schema, then the following new fields exist: `schedule_enabled` (Check, default 0), `schedule_frequency` (Select, options: "Daily\nWeekly\nMonthly"), `schedule_day_of_week` (Select, options: "Monday\nTuesday\nWednesday\nThursday\nFriday\nSaturday\nSunday", visible only when frequency = "Weekly"), `schedule_day_of_month` (Int, min 1 max 31, visible only when frequency = "Monthly"), `schedule_time` (Time, default "08:00:00"), `schedule_recipients` (Small Text, comma-separated email addresses), and `last_scheduled_run` (Datetime, read-only). All fields are added directly to the DocType JSON (not via Custom Fields, AR-04).

2. **[schedule_report API endpoint]** Given a saved HD Custom Report with `schedule_enabled = 1` and valid `schedule_recipients`, when `helpdesk.api.reports.schedule_report` is called with a `report_id`, then the scheduling configuration is saved to the HD Custom Report record and a confirmation response is returned. The caller must have write permission on the HD Custom Report record.

3. **[Background Job — Report Execution and Email Delivery]** Given one or more HD Custom Report records have `schedule_enabled = 1` and their schedule conditions are met (daily: any day; weekly: specific day-of-week; monthly: specific day-of-month), when the scheduler event fires (daily cron), then each qualifying report is enqueued as a background job using `frappe.enqueue()` with the `long` queue. The background job: (a) executes the report using the same query logic as `execute_report`, (b) generates an Excel (.xlsx) attachment, (c) sends an email to all `schedule_recipients` with the attachment, (d) updates `last_scheduled_run` to the current datetime.

4. **[Scheduler Event in hooks.py]** Given the scheduler is configured in `hooks.py`, when a daily cron job runs at the configured time, then the function `helpdesk.helpdesk.doctype.hd_custom_report.hd_custom_report.run_scheduled_reports` is registered as a `daily` scheduler event. It finds all qualifying reports and enqueues each one individually, so failures in one report do not block others.

5. **[export_report API — CSV Download]** Given a saved HD Custom Report (or inline configuration), when `helpdesk.api.reports.export_report` is called with `report_id` and `export_format="csv"`, then: (a) the report query is executed with all filters and grouping applied, (b) a CSV file is generated in memory using Python's `csv` module, (c) the response is returned as a file download with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="{report_name}_{date}.csv"`. The caller must have read permission on the target DocType.

6. **[export_report API — Excel (.xlsx) Download]** Given a saved HD Custom Report (or inline configuration), when `helpdesk.api.reports.export_report` is called with `report_id` and `export_format="xlsx"`, then: (a) the report query is executed with all filters and grouping applied, (b) an Excel workbook is generated using `openpyxl` with a header row (bold, grey background) and data rows, (c) column widths are auto-fitted to content (minimum 10, maximum 50 characters), (d) the response is returned as a file download with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and appropriate `Content-Disposition` header.

7. **[Export Includes All Filters and Grouping]** Given a report with active filters (e.g., `status = "Open"`) and group-by configured, when the export is triggered (CSV or Excel), then the exported data reflects the same filters and grouping as the live preview — no raw unfiltered data is exported. The export fetches up to 10,000 rows (configurable cap) rather than the preview's paginated 100 rows.

8. **[Export Button in Report Builder UI]** Given the Report Builder page (`/helpdesk/reports/:id`) from Story 6.1, when a manager views a saved report with results, then an "Export" button (frappe-ui Button, variant="outline") is visible in the header bar with a dropdown showing "Download CSV" and "Download Excel (.xlsx)" options. Clicking either option calls `helpdesk.api.reports.export_report` with the appropriate format and triggers a browser file download.

9. **[Schedule Configuration Panel in Report Builder UI]** Given the Report Builder page, when a manager opens a saved report, then a "Schedule" section is available in the left configuration panel (collapsed by default, expandable). The section contains: `schedule_enabled` toggle, `schedule_frequency` dropdown, conditional `schedule_day_of_week` / `schedule_day_of_month` selector, `schedule_time` time picker, and `schedule_recipients` text area (comma-separated emails). A "Save Schedule" button calls `helpdesk.api.reports.schedule_report`. A "Last run:" badge displays `last_scheduled_run` when set.

10. **[Schedule Recipient Validation]** Given the schedule configuration, when the manager saves a schedule with `schedule_enabled = 1`, then the backend validates that `schedule_recipients` is not empty and contains at least one syntactically valid email address. If validation fails, `frappe.throw()` returns a descriptive error. If `schedule_day_of_month` is set, it is validated to be between 1 and 28 (to avoid month-end edge cases with safe truncation to 28).

11. **[Email Format]** Given the scheduled report job runs successfully, when the email is sent to recipients, then: (a) the email subject is `"[Helpdesk Report] {report_name} — {formatted_date}"`, (b) the email body contains a plain-text summary: "Your scheduled report '{report_name}' is attached. Period: {date}. Rows: {row_count}.", (c) the attachment filename follows the pattern `{report_name}_{YYYY-MM-DD}.xlsx`. Frappe's standard `frappe.sendmail()` is used for sending.

12. **[Unit Tests — Scheduling Logic]** Given the scheduling and export implementation, when the test suite runs, then unit tests for the following pass with minimum 80% code coverage (NFR-M-01):
    - `test_schedule_fields_exist_on_doctype` — Assert all 7 new fields are present in the HD Custom Report schema.
    - `test_schedule_recipient_validation_empty` — Assert `frappe.ValidationError` when `schedule_enabled=1` and `schedule_recipients` is blank.
    - `test_schedule_recipient_validation_invalid_email` — Assert `frappe.ValidationError` for malformed email address.
    - `test_schedule_day_of_month_validation` — Assert `frappe.ValidationError` for `schedule_day_of_month = 0` and `> 28`.
    - `test_run_scheduled_reports_enqueues_jobs` — Mock `frappe.enqueue`, call `run_scheduled_reports()`, assert enqueue called once per qualifying report.
    - `test_export_csv_format` — Call `export_report` with `export_format="csv"`, assert returned content is valid CSV with correct header row.
    - `test_export_xlsx_format` — Call `export_report` with `export_format="xlsx"`, assert returned bytes are a valid Excel workbook with correct sheet name and headers.
    - `test_export_applies_filters` — Create report with filter `status = "Open"`, export as CSV, assert no non-Open rows in output.
    - `test_export_permission_enforcement` — Call `export_report` as Guest, assert PermissionError is raised.
    - `test_send_scheduled_report_email` — Mock `frappe.sendmail`, run the job function directly, assert sendmail called with correct subject format and attachment.

## Tasks / Subtasks

- [ ] Task 1 — Add schedule fields to HD Custom Report DocType (AC: #1)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.json` (created in Story 6.1).
  - [ ] 1.2 Add a Section Break field with label "Scheduling" before the new schedule fields.
  - [ ] 1.3 Add field: `schedule_enabled` (Check, default 0, label "Enable Schedule").
  - [ ] 1.4 Add field: `schedule_frequency` (Select, options: "Daily\nWeekly\nMonthly", label "Frequency", depends_on: `eval:doc.schedule_enabled`).
  - [ ] 1.5 Add field: `schedule_day_of_week` (Select, options: "Monday\nTuesday\nWednesday\nThursday\nFriday\nSaturday\nSunday", label "Day of Week", depends_on: `eval:doc.schedule_enabled && doc.schedule_frequency == 'Weekly'`).
  - [ ] 1.6 Add field: `schedule_day_of_month` (Int, label "Day of Month", description: "Day 1–28. Reports scheduled for day 29–31 should use day 28.", depends_on: `eval:doc.schedule_enabled && doc.schedule_frequency == 'Monthly'`).
  - [ ] 1.7 Add field: `schedule_time` (Time, default "08:00:00", label "Send Time", depends_on: `eval:doc.schedule_enabled`).
  - [ ] 1.8 Add field: `schedule_recipients` (Small Text, label "Recipients (comma-separated emails)", depends_on: `eval:doc.schedule_enabled`).
  - [ ] 1.9 Add field: `last_scheduled_run` (Datetime, label "Last Scheduled Run", read_only 1).
  - [ ] 1.10 Update `hd_custom_report.py` controller: add `validate_schedule()` method called from `validate()` that enforces AC #10 constraints.

- [ ] Task 2 — Implement `schedule_report` and `export_report` endpoints in `helpdesk/api/reports.py` (AC: #2, #5, #6, #7)
  - [ ] 2.1 Open (or create if Story 6.1 is not yet done) `helpdesk/api/reports.py`.
  - [ ] 2.2 Implement `@frappe.whitelist() schedule_report(report_id: str, schedule_enabled: int, schedule_frequency: str, schedule_day_of_week: str = None, schedule_day_of_month: int = None, schedule_time: str = "08:00:00", schedule_recipients: str = "")`.
    - [ ] 2.2a Call `frappe.has_permission("HD Custom Report", "write", doc=report_id, throw=True)`.
    - [ ] 2.2b Load the HD Custom Report doc, update schedule fields, call `doc.save()`.
    - [ ] 2.2c Return `{"message": "Schedule saved", "report_id": report_id}`.
  - [ ] 2.3 Implement `@frappe.whitelist() export_report(report_id: str = None, data_source: str = None, selected_fields: str = None, filters: str = None, group_by: str = None, sort_by: str = None, sort_order: str = "DESC", export_format: str = "csv", report_name: str = "report")`.
    - [ ] 2.3a When `report_id` provided, load config from `frappe.get_doc("HD Custom Report", report_id)`.
    - [ ] 2.3b Call `frappe.has_permission(data_source, "read", throw=True)`.
    - [ ] 2.3c Call `build_query()` (from Story 6.1) to execute the query with `page_length=10000, page=1`.
    - [ ] 2.3d If `export_format == "csv"`: call `_generate_csv(rows, columns)` → return as `frappe.response` with file content.
    - [ ] 2.3e If `export_format == "xlsx"`: call `_generate_xlsx(rows, columns, report_name)` → return as `frappe.response` with file content.
  - [ ] 2.4 Implement private helper `_generate_csv(rows: list, columns: list) -> str`:
    - [ ] 2.4a Use Python's built-in `csv` module with `io.StringIO` as buffer.
    - [ ] 2.4b Write header row using column labels (or fieldnames if no label).
    - [ ] 2.4c Write data rows.
    - [ ] 2.4d Return the string content.
  - [ ] 2.5 Implement private helper `_generate_xlsx(rows: list, columns: list, report_name: str) -> bytes`:
    - [ ] 2.5a Import `openpyxl` and `openpyxl.styles` (already available in Frappe environment).
    - [ ] 2.5b Create workbook, rename active sheet to `report_name[:31]` (Excel limit).
    - [ ] 2.5c Write header row with bold font and grey fill (`PatternFill(fill_type="solid", fgColor="D3D3D3")`).
    - [ ] 2.5d Write all data rows.
    - [ ] 2.5e Auto-fit column widths: for each column, set `column_dimensions[col].width = max(min(max_len + 2, 50), 10)`.
    - [ ] 2.5f Save workbook to `io.BytesIO`, return bytes.
  - [ ] 2.6 Set `frappe.response` fields for file download:
    - [ ] 2.6a For CSV: `frappe.response["filename"]`, `frappe.response["filecontent"]`, `frappe.response["type"] = "download"`.
    - [ ] 2.6b For XLSX: same pattern with `.xlsx` extension and binary content.
    - [ ] 2.6c Use `frappe.utils.now_datetime().strftime("%Y-%m-%d")` for date in filename.

- [ ] Task 3 — Implement background job for scheduled report delivery (AC: #3, #11)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.py`.
  - [ ] 3.2 Implement `run_scheduled_reports()` module-level function (called by scheduler):
    - [ ] 3.2a Query all HD Custom Report records where `schedule_enabled = 1` using `frappe.get_all()`.
    - [ ] 3.2b For each report, call `_is_report_due(report)` to check if today matches the schedule (daily: always True; weekly: `today.strftime("%A") == report.schedule_day_of_week`; monthly: `today.day == report.schedule_day_of_month`).
    - [ ] 3.2c For each due report, call `frappe.enqueue("helpdesk.helpdesk.doctype.hd_custom_report.hd_custom_report.send_scheduled_report", queue="long", timeout=600, report_id=report.name)`.
    - [ ] 3.2d Wrap each enqueue in try/except — log errors to `frappe.log_error()` and continue to next report.
  - [ ] 3.3 Implement `send_scheduled_report(report_id: str)` function:
    - [ ] 3.3a Load the HD Custom Report doc.
    - [ ] 3.3b Execute the report query (reuse `build_query` from `reports.py`): import and call `from helpdesk.api.reports import build_query, _generate_xlsx`.
    - [ ] 3.3c If no rows returned, log a warning and skip email (do not send empty attachment).
    - [ ] 3.3d Generate Excel attachment bytes using `_generate_xlsx(rows, columns, doc.report_name)`.
    - [ ] 3.3e Build `recipients` list from `doc.schedule_recipients.split(",")` after stripping whitespace.
    - [ ] 3.3f Format subject: `f"[Helpdesk Report] {doc.report_name} — {today_str}"`.
    - [ ] 3.3g Format body: `f"Your scheduled report '{doc.report_name}' is attached.\nDate: {today_str}\nRows: {len(rows)}"`.
    - [ ] 3.3h Call `frappe.sendmail(recipients=recipients, subject=subject, message=body, attachments=[{"fname": filename, "fcontent": attachment_bytes}])`.
    - [ ] 3.3i Update `doc.last_scheduled_run = frappe.utils.now_datetime()` and call `doc.db_set("last_scheduled_run", doc.last_scheduled_run)` (lightweight update, no full save/validate cycle).
    - [ ] 3.3j Wrap entire function in try/except, log errors via `frappe.log_error()`.

- [ ] Task 4 — Register scheduler event in hooks.py (AC: #4)
  - [ ] 4.1 Open `helpdesk/hooks.py`.
  - [ ] 4.2 Locate the `scheduler_events` dict (or create it if not present).
  - [ ] 4.3 Add to the `"daily"` list: `"helpdesk.helpdesk.doctype.hd_custom_report.hd_custom_report.run_scheduled_reports"`.
  - [ ] 4.4 Verify no duplicate entries in the `"daily"` list (other daily jobs from the architecture exist: automation log cleanup, KB article review reminders — ensure all are preserved).

- [ ] Task 5 — Update Report Builder UI with Export and Schedule panels (AC: #8, #9)
  - [ ] 5.1 Open `desk/src/pages/reports/ReportBuilder.vue` (created in Story 6.1).
  - [ ] 5.2 Add "Export" button with dropdown to header bar:
    - [ ] 5.2a Use frappe-ui `Dropdown` component with trigger button "Export" (variant="outline").
    - [ ] 5.2b Dropdown items: "Download CSV" and "Download Excel (.xlsx)".
    - [ ] 5.2c On selection: call `reportStore.exportReport(format)` composable action that issues a `window.open()` or direct link to `helpdesk.api.reports.export_report` with appropriate params including `export_format`.
    - [ ] 5.2d Disable Export button when no report is loaded or `reportStore.previewData` is empty.
  - [ ] 5.3 Add "Schedule" collapsible section to the left config panel (below filter/group-by sections):
    - [ ] 5.3a Use frappe-ui `Collapse` or a plain `<details>` element with custom styling.
    - [ ] 5.3b Inside the section: `schedule_enabled` toggle (frappe-ui `Switch`), `schedule_frequency` Select, conditional `schedule_day_of_week` Select (shown only when frequency = "Weekly"), conditional `schedule_day_of_month` Int input (shown only when frequency = "Monthly"), `schedule_time` time input, `schedule_recipients` textarea (placeholder: "user@example.com, manager@example.com").
    - [ ] 5.3c "Save Schedule" button calls `helpdesk.api.reports.schedule_report` via `createResource`. On success, shows toast: "Schedule saved."
    - [ ] 5.3d If `last_scheduled_run` is set on the loaded report, display a small badge: "Last run: {relative_time}" using dayjs.
  - [ ] 5.4 On `loadReport(id)` in `report.ts` Pinia store: also hydrate schedule fields (add them to store state: `scheduleEnabled`, `scheduleFrequency`, `scheduleDayOfWeek`, `scheduleDayOfMonth`, `scheduleTime`, `scheduleRecipients`, `lastScheduledRun`).

- [ ] Task 6 — Update `report.ts` Pinia store for schedule state (AC: #9)
  - [ ] 6.1 Open `desk/src/stores/report.ts` (created in Story 6.1).
  - [ ] 6.2 Add reactive state for schedule fields: `scheduleEnabled` (boolean), `scheduleFrequency` (string), `scheduleDayOfWeek` (string), `scheduleDayOfMonth` (number), `scheduleTime` (string), `scheduleRecipients` (string), `lastScheduledRun` (string | null).
  - [ ] 6.3 Add `saveSchedule()` async action that calls `helpdesk.api.reports.schedule_report` with current schedule state and the current report ID.
  - [ ] 6.4 Add `exportReport(format: "csv" | "xlsx")` action that constructs the URL for `helpdesk.api.reports.export_report` with `cmd=helpdesk.api.reports.export_report&report_id=...&export_format=...` and uses `window.open()` to trigger file download.
  - [ ] 6.5 Extend `loadReport(reportId)` to hydrate schedule fields from the loaded HD Custom Report doc.

- [ ] Task 7 — Write unit tests (AC: #12)
  - [ ] 7.1 Open (or create) `helpdesk/helpdesk/doctype/hd_custom_report/test_hd_custom_report.py`.
  - [ ] 7.2 `test_schedule_fields_exist_on_doctype` — Load HD Custom Report meta via `frappe.get_meta`, assert all 7 schedule fields are present in `meta.fields` by fieldname.
  - [ ] 7.3 `test_schedule_recipient_validation_empty` — Create HD Custom Report with `schedule_enabled=1`, `schedule_recipients=""`, call `doc.save()`, assert `frappe.exceptions.ValidationError`.
  - [ ] 7.4 `test_schedule_recipient_validation_invalid_email` — Set `schedule_recipients="notanemail"`, assert `frappe.exceptions.ValidationError`.
  - [ ] 7.5 `test_schedule_day_of_month_validation_zero` — Set `schedule_frequency="Monthly"`, `schedule_day_of_month=0`, assert `frappe.exceptions.ValidationError`.
  - [ ] 7.6 `test_schedule_day_of_month_validation_over_28` — Set `schedule_day_of_month=29`, assert `frappe.exceptions.ValidationError`.
  - [ ] 7.7 Create `helpdesk/tests/test_reports_scheduling.py`.
  - [ ] 7.8 `test_run_scheduled_reports_enqueues_jobs` — Create an HD Custom Report with `schedule_enabled=1`, `schedule_frequency="Daily"`, `schedule_recipients="test@example.com"`. Patch `frappe.enqueue`. Call `run_scheduled_reports()`. Assert `frappe.enqueue` was called with `report_id=<name>` and `queue="long"`.
  - [ ] 7.9 `test_export_csv_format` — Create HD Custom Report with `data_source="HD Ticket"`, `selected_fields=["name","subject"]`. Call `export_report(report_id=..., export_format="csv")`. Assert `frappe.response["filename"]` ends with `.csv` and `frappe.response["filecontent"]` is a string with a valid CSV header row.
  - [ ] 7.10 `test_export_xlsx_format` — Call `export_report(report_id=..., export_format="xlsx")`. Assert `frappe.response["filename"]` ends with `.xlsx`. Load the bytes with `openpyxl.load_workbook(io.BytesIO(frappe.response["filecontent"]))`, assert workbook has at least one sheet and the first row is non-empty.
  - [ ] 7.11 `test_export_applies_filters` — Create test HD Ticket with status "Resolved". Configure report with filter `status = equals = "Open"`. Export as CSV. Assert the resolved ticket's name does NOT appear in the CSV output.
  - [ ] 7.12 `test_export_permission_enforcement` — Set `frappe.session.user = "Guest"`. Call `export_report(data_source="HD Ticket", ...)`. Assert `frappe.exceptions.PermissionError` is raised.
  - [ ] 7.13 `test_send_scheduled_report_email` — Create HD Custom Report with schedule fields set. Create at least one HD Ticket. Patch `frappe.sendmail`. Call `send_scheduled_report(report_id)`. Assert `frappe.sendmail` was called once; assert subject contains "[Helpdesk Report]"; assert attachment list is non-empty; assert `doc.last_scheduled_run` is updated.
  - [ ] 7.14 `test_export_row_cap_10000` — Assert that `export_report` internally calls `build_query` with `page_length=10000` (not the preview default of 100). Mock `build_query` and inspect the call arguments.

## Dev Notes

### Architecture Patterns

- **Dependency on Story 6.1** — This story extends the `HD Custom Report` DocType and `helpdesk/api/reports.py` created in Story 6.1. If Story 6.1 is not yet complete, the developer must first create the base DocType and API file, then add the scheduling fields on top. See story-6.1-custom-report-builder.md for the full base implementation.

- **DocType Field Extension Pattern** — Add new fields to the existing `hd_custom_report.json` using `depends_on` for conditional visibility (per AR-04). Example of a conditional field:
  ```json
  {
    "fieldname": "schedule_day_of_week",
    "fieldtype": "Select",
    "label": "Day of Week",
    "options": "Monday\nTuesday\nWednesday\nThursday\nFriday\nSaturday\nSunday",
    "depends_on": "eval:doc.schedule_enabled && doc.schedule_frequency == 'Weekly'"
  }
  ```

- **Background Job Pattern (ADR-12)** — Scheduled reports use the `long` queue (architecture ADR-12, "Report generation, CSAT survey batch send... long queue"). Use `frappe.enqueue()` for async execution:
  ```python
  frappe.enqueue(
      "helpdesk.helpdesk.doctype.hd_custom_report.hd_custom_report.send_scheduled_report",
      queue="long",
      timeout=600,
      is_async=True,
      report_id=report.name
  )
  ```
  Individual job failures must be isolated using try/except so one failing report does not block others (NFR-A-01).

- **Scheduler Event Registration (ADR-12)** — Add to the `"daily"` list in `scheduler_events` dict in `hooks.py`. The architecture already specifies the following daily events: `purge_old_logs` and `send_review_reminders`. This story adds `run_scheduled_reports`. Keep all three:
  ```python
  scheduler_events = {
      "daily": [
          "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
          "helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders",
          "helpdesk.helpdesk.doctype.hd_custom_report.hd_custom_report.run_scheduled_reports",  # NEW
      ]
  }
  ```

- **Excel Generation with openpyxl** — Frappe Framework's Python environment includes `openpyxl` (it's a Frappe dependency used by Frappe's built-in report export). Import directly:
  ```python
  import openpyxl
  from openpyxl.styles import Font, PatternFill
  import io
  ```
  Do NOT install any new Python packages. If `openpyxl` is somehow unavailable, fall back to CSV with a `frappe.log_error()` and a user-facing message.

- **File Download via frappe.response** — Frappe's standard pattern for returning file downloads from whitelisted methods:
  ```python
  frappe.response["filename"] = f"{report_name}_{today}.csv"
  frappe.response["filecontent"] = csv_content
  frappe.response["type"] = "download"
  ```
  For binary (xlsx), the same pattern applies but `filecontent` is bytes. The frontend triggers the download by opening a URL with `window.open()` appending `cmd=...&report_id=...&export_format=...` as GET params, or via a form POST if params are too long.

- **CSV Generation (stdlib only)** — Use Python's built-in `csv` module, no third-party library needed:
  ```python
  import csv
  import io

  def _generate_csv(rows, columns):
      output = io.StringIO()
      writer = csv.writer(output)
      writer.writerow([col.get("label") or col.get("fieldname") for col in columns])
      for row in rows:
          writer.writerow([row.get(col["fieldname"], "") for col in columns])
      return output.getvalue()
  ```

- **Email Sending (frappe.sendmail)** — Use Frappe's standard `frappe.sendmail()`:
  ```python
  frappe.sendmail(
      recipients=["manager@example.com"],
      subject="[Helpdesk Report] Weekly Summary — 2026-03-23",
      message="Your scheduled report is attached.\nDate: 2026-03-23\nRows: 47",
      attachments=[{
          "fname": "Weekly_Summary_2026-03-23.xlsx",
          "fcontent": xlsx_bytes
      }]
  )
  ```
  The `attachments` list accepts dicts with `fname` (filename) and `fcontent` (bytes or string). Do NOT use `frappe.attach_print()` — that is for print formats.

- **Permission Model (ADR-04, NFR-SE-05)** — `export_report` must call `frappe.has_permission(data_source, "read", throw=True)`. `schedule_report` must call `frappe.has_permission("HD Custom Report", "write", doc=report_id, throw=True)`. These are mandatory per Enforcement Guideline #2.

- **i18n** — All user-facing strings in Python use `frappe._()`, all JS/Vue strings use `__()` (Enforcement Guideline #7).

- **reuse `build_query` from Story 6.1** — The `build_query()` helper function in `reports.py` (Story 6.1 Task 2.4) is reused in `export_report` and `send_scheduled_report`. The export simply calls it with a higher `page_length` (10,000) instead of the default 100. This avoids duplication and ensures consistent filter/grouping behavior.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.json` | Add 7 schedule fields (Section Break, schedule_enabled, schedule_frequency, schedule_day_of_week, schedule_day_of_month, schedule_time, schedule_recipients, last_scheduled_run) |
| Modify | `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.py` | Add `validate_schedule()` and `run_scheduled_reports()`, `send_scheduled_report()` functions |
| Modify | `helpdesk/helpdesk/doctype/hd_custom_report/test_hd_custom_report.py` | Add schedule field and validation tests (Tasks 7.2–7.6) |
| Modify | `helpdesk/api/reports.py` | Add `schedule_report()`, `export_report()`, `_generate_csv()`, `_generate_xlsx()` |
| Create | `helpdesk/tests/test_reports_scheduling.py` | Unit tests for scheduling, email, export (Tasks 7.7–7.14) |
| Modify | `helpdesk/hooks.py` | Add `run_scheduled_reports` to `scheduler_events["daily"]` |
| Modify | `desk/src/pages/reports/ReportBuilder.vue` | Add Export dropdown button and Schedule collapsible panel |
| Modify | `desk/src/stores/report.ts` | Add schedule state fields, `saveSchedule()` and `exportReport()` actions |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all Python tests.
- Tests that create HD Custom Report records must clean up via `addCleanup(frappe.delete_doc, "HD Custom Report", doc.name)`.
- Patch `frappe.enqueue` and `frappe.sendmail` when testing scheduler and email functions (do not actually enqueue or send emails in tests).
- Run DocType tests: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_custom_report.test_hd_custom_report`
- Run scheduling/export tests: `bench --site <site> run-tests --module helpdesk.tests.test_reports_scheduling`

### Constraints

- Do NOT install new Python packages — use `openpyxl` (already in Frappe's environment) and stdlib `csv`, `io`.
- Do NOT allow scheduled reports to query arbitrary DocTypes — `data_source` allowlist from Story 6.1 must remain enforced (HD Ticket, HD CSAT Response, HD Article, HD Time Entry).
- Do NOT send emails for empty results — skip silently and log a debug message when the report produces 0 rows.
- Export row cap is 10,000 rows (not unlimited) to prevent memory exhaustion. Log a warning if total rows exceed 10,000 and only the first 10,000 are exported.
- `schedule_day_of_month` is capped at 28 (not 31) to avoid month-end edge cases (February has 28/29 days; months with 30 days exist). Validate and reject values > 28.
- `last_scheduled_run` must use `frappe.db_set()` (lightweight field update) rather than `doc.save()` to avoid triggering validate hooks (which would fire automation rules if those are wired to `on_update`).
- All whitelisted API methods must use `@frappe.whitelist()` decorator (Enforcement Guideline #1).
- Never use raw SQL — all queries via `frappe.qb` or `frappe.get_all()` (Enforcement Guideline #6).

### Project Structure Notes

- **DocType location:** `helpdesk/helpdesk/doctype/hd_custom_report/` — modifying existing Story 6.1 DocType.
- **Scheduler function location:** In the DocType controller `hd_custom_report.py` (module-level functions `run_scheduled_reports` and `send_scheduled_report`). This follows the Frappe convention of placing scheduler functions in the DocType controller when they operate on that DocType.
- **API location:** `helpdesk/api/reports.py` — adding to the existing file per ADR-08.
- **hooks.py location:** `helpdesk/hooks.py` — project root of the backend module. The existing `scheduler_events` dict is extended (not replaced). Per ADR-12, the daily events list already includes automation log cleanup and KB article review reminders.
- **Frontend page:** `desk/src/pages/reports/ReportBuilder.vue` — modifying existing Story 6.1 page per ADR-09.
- **Pinia store:** `desk/src/stores/report.ts` — modifying existing Story 6.1 store per ADR-11.
- **Dependencies:** This story has a hard runtime dependency on Story 6.1 (`HD Custom Report` DocType and base `reports.py` must exist). The story can be developed after Story 6.1 is merged, or in parallel if the developer creates the base DocType stub first. No dependency on Epic 3 (CSAT) or Epic 4 (SLA) — export works on whatever data exists at time of execution.
- **openpyxl in Frappe:** Frappe Framework uses `openpyxl` internally for Excel export functionality. It is listed in Frappe's `requirements.txt`. Safe to import directly without adding it to the app's dependencies.

### References

- FR-CR-02 (Report scheduling with email delivery and CSV/Excel export): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- NFR-SE-05 (Custom reports respect Frappe permission model): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-A-01 (Core ticketing unaffected by automation/chat failures — isolation principle applies to scheduler): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-02 (HD prefix naming convention): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-03 (Background jobs use Frappe's Redis Queue): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (Add fields to DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- ADR-02 (New DocType Schema — HD Custom Report already created in Story 6.1): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-04 (Permission Model Extensions — write permission for schedule_report): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-08 (API Design — reports.py with schedule_report and export_report endpoints): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — ReportBuilder.vue modifications): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-11 (State Management — report.ts Pinia store updates): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11]
- ADR-12 (Background Job Architecture — long queue for report generation; daily scheduler events): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- Enforcement Guideline #1 (frappe.whitelist for every API): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #2 (frappe.has_permission before data access): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #6 (No raw SQL): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #7 (frappe._() for i18n): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Scheduler events pattern (daily list): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- Project Directory Structure (api/reports.py, hooks.py, doctype/hd_custom_report/): [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Epic 6 Story 6.2 full AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2]
- Story 6.1 (base DocType and report API): [Source: _bmad-output/implementation-artifacts/story-6.1-custom-report-builder.md]

## Dev Agent Record

### Agent Model Used

_To be filled by implementing dev agent_

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
