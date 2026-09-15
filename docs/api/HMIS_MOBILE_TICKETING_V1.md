# HMIS and Mobile plugin ticketing API contract v1.5

Updated: 2026-09-15. Server trust is configured on Helpdesk; mobile paths and payloads are unchanged. Multipart and list-filter extension: v1.2; wire `api_version` remains `1` (additive fields). Apps: `careverse_hq` and `helpdesk`.

```text
HMIS / Mobile -> authenticated CareVerse API -> service-authenticated, Ed25519-signed Helpdesk plugin API
                                            <- scoped ticket response
Helpdesk -> configured CareVerse public-key API -> verify Ed25519 signature
```

**Consumer applications call CareVerse.** CareVerse supplies identity and signs the request; the private key never belongs in a browser or mobile application. The algorithm is **Ed25519** (not “ED2215”).

## Primary consumer operations

All operations use the authenticated CareVerse RPC URLs below. The “all-tickets” and “1-ticket” operations are exposed as `list_tickets` and `get_ticket` in the established RPC namespace; there are no separate root `/all-tickets` or `/1-ticket` routes.

| Operation | Method and consumer path |
|---|---|
| Create ticket with files | `POST /api/method/careverse_hq.api.helpdesk.create_ticket` — multipart/form-data or JSON |
| Facility tickets | `GET /api/method/careverse_hq.api.helpdesk.list_tickets?facility=<facility>&email=<CareVerse-user>&subject=<search>&ticket_type=<type>&offset=0&limit=20` |
| Close ticket | `POST /api/method/careverse_hq.api.helpdesk.close_ticket` — ticket_id |
| Comment/chat on a ticket | `POST /api/method/careverse_hq.api.helpdesk.send_message` — ticket_id plus content and/or files |
| Read ticket chat | `GET /api/method/careverse_hq.api.helpdesk.get_thread?ticket_id=<ID>` |
| One ticket | `GET /api/method/careverse_hq.api.helpdesk.get_ticket?ticket_id=<ID>` |

The list is paginated and ordered by creation descending, then ticket ID descending. `facility` is mandatory. Mobile sends `email` by default for the reporter's tickets; omitting `email` returns all CareVerse integration tickets for the required facility. Optional `subject` is a case-insensitive contains search, `ticket_type` is an exact ticket-type filter, and `status` is an exact live status. Facility-wide results remain limited to the verified CareVerse instance.

## 1. URLs and endpoint map

Consumer prefix:
`https://desk.tiberbu.app/api/method/careverse_hq.api.helpdesk.`

Internal signed prefix:
`https://hd-dev.tiberbu.app/api/method/helpdesk.api.plugin.`

Append the same RPC name on each side:

| Method | RPC | Arguments | Result in `data` |
|---|---|---|---|
| POST | `create_ticket` | `source`, `external_reference_id`, `reporter`, `category`, `priority`, `description`, optional `attachments` | `ticket_id`, `status`, `assigned_to`, `assigned_team`, `reused`, `attachments` |
| GET | `get_ticket` | `ticket_id` | Ticket detail, including status and assignments |
| GET | `list_tickets` | `facility` required, `email` optional, `user` optional (compatibility), `subject` optional, `ticket_type` optional, `status` optional, `offset=0`, `limit=20` | `items`, `has_more`, `next_offset` |
| GET | `get_bootstrap` | none | Reporter identity, categories, priorities, statuses, capabilities |
| GET | `get_counties` | none | `items` |
| GET | `get_subcounties` | `county` | `items` |
| GET | `get_facilities` | `county` optional, `sub_county` optional, `offset=0`, `limit=50` | `items`, `has_more`, `next_offset` |
| GET | `get_thread` | `ticket_id`, `offset=0`, `limit=50` | Public messages, replies and activities in `items`, plus pagination |
| POST | `send_message` | `ticket_id`, optional `content`, optional `attachments` (at least one nonempty) | `ticket_id`, `accepted`, `message_id`, `status`, `attachments` |
| POST | `close_ticket` | `ticket_id` | `ticket_id`, `closed`, `status` |
| GET | `list_attachments` | `ticket_id`, `offset=0`, `limit=50` | `items`, `has_more`, `next_offset` |
| GET | `download_attachment` | `ticket_id`, `attachment_id` | Attachment metadata, `event_id`, `content_base64`, `sha256` |

Consumer create/comment POSTs accept `multipart/form-data` or JSON objects. Internal CareVerse → HD POSTs remain service-authenticated, signed JSON objects. GET arguments use URL query parameters. IDs are opaque strings, never integers. URL-encode email addresses and IDs. Pagination accepts integer offset >= 0 and limit 1–100.

`helpdesk.api.hmis_integration.*` is not the namespace of this implementation. The earlier `helpdesk.api.mobile.*` functions are internal services and are no longer whitelisted endpoints. Use `helpdesk.api.plugin.*` for server integration.

## 2. Consumer authentication and response envelopes

Authenticate to CareVerse using its existing login/session flow or an individual user's API credentials:

```http
Authorization: token <HELPDESK_SERVICE_API_KEY>:<HELPDESK_SERVICE_API_SECRET>
Content-Type: application/json
```

Cookie clients preserve the CareVerse session and satisfy its CSRF requirements. Browser CORS and the application's login/SSO implementation remain application deployment responsibilities. The mobile client never receives the Helpdesk service credentials.

Consumer success, HTTP 200:

```json
{"message":{"status":"success","data":{"ticket_id":"TKT-XX-XX-XX-XXXXX","status":"Open","assigned_to":[],"assigned_team":null,"reused":false}}}
```

Check `body.message.status === "success"`; consume `body.message.data`. Other standard CareVerse envelope metadata may be present.

Internal Helpdesk success, HTTP 200:

```json
{"message":{"api_version":1,"data":{"ticket_id":"TKT-XX-XX-XX-XXXXX","status":"Open","assigned_to":[],"assigned_team":null,"reused":false}}}
```

The only difference is the outer application envelope. Business data is forwarded unchanged. Never treat HTTP 200 alone as proof of the expected response shape.

## 3. Create a ticket — exact consumer contract

```http
POST /api/method/careverse_hq.api.helpdesk.create_ticket
```

```json
{
  "source": "HMIS",
  "external_reference_id": "your-issue-id",
  "reporter": {
    "name": "Jane Doe",
    "email": "jane@x.org",
    "facility": "Facility Name"
  },
  "category": "System Error",
  "priority": "Medium",
  "description": "Patient registration fails when saving the encounter.",
  "attachments": [
    {"file_name":"registration.png","content_type":"image/png","content_base64":"<standard Base64 of image bytes>"},
    {"file_name":"issue.pdf","content_type":"application/pdf","content_base64":"<standard Base64 of PDF bytes>"}
  ]
}
```

CareVerse forwards this to `POST /api/method/helpdesk.api.plugin.create_ticket` with additional signed identity fields described in section 8.

| Input | Rule |
|---|---|
| source | Nonblank string, max 40 characters. Use a stable value such as `HMIS` or `Mobile`; case-sensitive. |
| external_reference_id | Nonblank string, max 140 characters. Generate once when the issue is created locally; retain across retries. |
| reporter | Exactly `name`, `email`, `facility`. An object in a JSON request; one JSON-encoded text field in multipart. |
| reporter.name | Nonblank display name, max 140 characters; metadata, not authorization. |
| reporter.email | Must exactly match the signed CareVerse user ID returned as `reporter_email` by bootstrap. No reporting as another email. |
| reporter.facility | Nonblank facility ID or display name, max 140 characters. |
| category | An enabled `HD Ticket Type` name from bootstrap `categories`. `System Error` is installed by this feature's setup patch. |
| priority | An existing `HD Ticket Priority` name from bootstrap. |
| description | Plain text, nonblank, max 20,000 characters. Stored as escaped HTML; the first line supplies the ticket subject, capped at 140 characters. |
| attachments | Optional array of image/PDF objects, described in section 6A. Omit or send `[]` for a text-only ticket. |

No subject, county, sub-county or ticket_type is required in the create payload. A matching catalogue facility supplies the ticket's facility and geography. An unknown free-text facility is preserved in reporter metadata; it does not create a facility master. An ambiguous facility display name is rejected; submit its unique catalogue ID instead. Native user/location/default routing remains active and can supply fallback geography/team.

Result:

```json
{
  "ticket_id": "TKT-XX-XX-XX-XXXXX",
  "status": "Open",
  "assigned_to": ["support.agent@example.org"],
  "assigned_team": "Mombasa County Team",
  "reused": false,
  "attachments": [
    {"attachment_id":"<file-id>","file_name":"registration.png","content_type":"image/png","size_bytes":12345,"is_private":true},
    {"attachment_id":"<pdf-file-id>","file_name":"issue.pdf","content_type":"application/pdf","size_bytes":23456,"is_private":true}
  ]
}
```

`assigned_to` is always an array of HD user IDs. The existing native assignment rules run during insertion, including round robin when configured. The API returns the actual persisted assignment; it does not invent an agent. With no eligible agent or enabled rule it returns `[]`; the UI should display “Awaiting assignment”. `assigned_team` can be null. Priority and status in subsequent detail responses reflect native rules, which may override requested defaults.

The user fills in the report, selects files and presses **Submit once**. The app submits one multipart or JSON request. CareVerse converts multipart files to the internal Base64 JSON representation before signing. HD validates every attachment before inserting the ticket; ticket, private File records and initial attachment manifest commit in the same request transaction. File persistence failure rolls back the ticket and new files through the native File rollback lifecycle. The app does not need a separate upload request or a second user action. Success means the full submission was saved; no partial-success payload exists.

### Multipart creation

Use the same create endpoint with ordinary text fields and repeated binary **`files`** parts:

| Part | Encoding |
|---|---|
| source | Text, e.g. `HMIS` |
| external_reference_id | Text, stable across retries |
| reporter | JSON text, e.g. `{"name":"Jane Doe","email":"jane@x.org","facility":"Clinic A"}` |
| category | Text, e.g. `System Error` |
| priority | Text, e.g. `Medium` |
| description | Plain text |
| files | Optional repeated binary file parts, each with filename and correct MIME type |

```bash
curl --fail-with-body \
  -H 'Authorization: token <CV_USER_KEY>:<CV_USER_SECRET>' \
  -F 'source=HMIS' \
  -F 'external_reference_id=your-issue-id' \
  -F 'reporter={"name":"Jane Doe","email":"jane@x.org","facility":"Clinic A"}' \
  -F 'category=System Error' \
  -F 'priority=Medium' \
  -F 'description=Patient registration fails when saving.' \
  -F 'files=@registration.png;type=image/png' \
  -F 'files=@issue.pdf;type=application/pdf' \
  'https://desk.tiberbu.app/api/method/careverse_hq.api.helpdesk.create_ticket'
```

Let the HTTP client generate `Content-Type: multipart/form-data; boundary=...`; do not set it manually without a boundary. Send raw file bytes, not Base64, in `files`. Use exactly `files`, not `files[]`, `file`, or `attachments`. Do not combine multipart files with the JSON `attachments` field. Unknown parts, duplicate text fields, duplicate reporter JSON keys, and multipart query parameters are rejected. Cookie clients must supply CSRF in `X-Frappe-CSRF-Token`, not as an additional form field.

The file-count, MIME, decoded-byte, filename and privacy limits in section 6A apply to both formats. Multipart with no files becomes `attachments:[]`. To retry a multipart ticket originally submitted with files, resend the same files in the same order. Responses, transaction guarantees and business retry keys are identical to JSON submission.

CareVerse reads each binary stream with a size bound and Base64-encodes it for the internal request. HD receives the existing signed JSON contract, not the client's multipart boundary or raw multipart body. No client signing changes or HD multipart endpoint are needed.

### Retry guarantee

The persistent uniqueness key is `(Helpdesk-local ownership scope, source, external_reference_id)`, protected by a database unique index. A retry returns the original `ticket_id`, current status/assignments, and `reused:true`. It neither changes the original description nor reruns routing/assignment. Returned `attachments` contain the original persisted files. When attachments are included on retry, their order, names, declared types and content hashes must match the original submission; changed attachments are rejected. Omitting `attachments` on retry retrieves the original result without requiring a re-upload. Sending `[]` is an explicit empty attachment set and conflicts with an originally nonempty set. Add later files using `send_message`. Concurrent creates are resolved by the unique index; the losing request reads the committed winner. Reuse is allowed only for the original signed reporter; another reporter cannot claim or read that reference.

Persist the reference before the first POST. On network timeout, retry the same source/reference. Each CareVerse attempt receives a fresh signature/request ID automatically. A transport `request_id` is not the business retry key. Different sources or CareVerse instances may independently use the same reference. Do not reuse a reference for a genuinely different issue. After ticket deletion, this implementation does not retain a permanent idempotency tombstone.

## 4. Check status and list facility tickets

```http
GET /api/method/careverse_hq.api.helpdesk.get_ticket?ticket_id=TKT-XX-XX-XX-XXXXX
GET /api/method/careverse_hq.api.helpdesk.list_tickets?facility=Clinic%20A&email=jane%40x.org&subject=registration&ticket_type=System%20Error&offset=0&limit=20
```

Internal counterparts are `helpdesk.api.plugin.get_ticket` and `helpdesk.api.plugin.list_tickets` with the same business arguments and signed identity fields.

Detail `data` is a flat object, not `data.ticket`:

```json
{
  "ticket_id": "TKT-XX-XX-XX-XXXXX",
  "name": "TKT-XX-XX-XX-XXXXX",
  "subject": "Patient registration fails when saving the encounter.",
  "status": "Open",
  "priority": "Medium",
  "category": "System Error",
  "ticket_type": "System Error",
  "source": "HMIS",
  "external_reference_id": "your-issue-id",
  "reporter": {"name":"Jane Doe","email":"jane@x.org","facility":"Facility Name"},
  "description_html": "Patient registration fails when saving the encounter.",
  "attachments": [],
  "assigned_to": [],
  "assigned_team": null,
  "agent_group": null,
  "county": null,
  "sub_county": null,
  "facility": null,
  "raised_by": "service-user@example.org",
  "creation": "2026-09-11 10:30:00.000000",
  "modified": "2026-09-11 10:30:00.000000"
}
```

`raised_by` is the HD service identity; `reporter.email` is the CareVerse identity. Dates without offsets use the site timezone from bootstrap. Nullable geography is expected for unmatched free-text facilities.

List result:

```json
{"items":[{"ticket_id":"TKT-XX-XX-XX-XXXXX","status":"Open","assigned_to":[]}],"has_more":false,"next_offset":null}
```

Each actual list item has the full detail shape above; the example abbreviates it. Order: creation descending, then name descending. `facility` is required; missing or blank values return a validation error. Mobile sends `email` by default for the logged-in CareVerse reporter. Omitting `email` deliberately returns all CareVerse integration tickets for that facility. `user` remains a compatibility filter for the same identity. If either is supplied, it must equal the authenticated CareVerse user; a mismatch is denied. If both are supplied, both must match. `subject` is a case-insensitive contains search. `ticket_type` is an exact `HD Ticket.ticket_type` match. Optional status is an exact live status name.

`facility` matches either the resolved HD Facility ID or the stored original `reporter.facility` value by database equality (no substring search). Use the catalogue ID when available, otherwise the exact submitted facility text. Database collation controls case sensitivity. Facility conditions are combined with instance/user permissions and status; they never replace them. A valid filter with no matches returns `items:[]`, `has_more:false`, `next_offset:null`. All filters apply before pagination. Offset-based pages can shift when newer tickets arrive; refresh from offset 0 to reload the latest list.

Every ticket read/write is scoped to the verified instance and HD service owner, plus native ticket permissions. When `email` is supplied, the signed reporter is also required; when it is omitted, the required facility is the cross-reporter boundary. Historic/demo tickets lacking plugin attribution are not silently claimed; they will not appear in this list. No bulk historical attribution was performed.

### Close and reopen

`POST /api/method/careverse_hq.api.helpdesk.close_ticket` accepts `{"ticket_id":"..."}`. The authenticated reporter may close their ticket from any current status; repeating the call is safe and returns `{"ticket_id":"...","closed":true,"status":"Closed"}`. A later `send_message` on a resolved or closed ticket adds the public comment and reopens the ticket to the configured Helpdesk reopen status (normally `Open`) in the same transaction. The response includes the resulting `status`. Internal notes and agent-only operations remain unavailable.

## 5. Critical dependency GETs

Call bootstrap before rendering the create form:

```http
GET /api/method/careverse_hq.api.helpdesk.get_bootstrap
```

Example `data` (values are discovered, not hardcoded):

```json
{
  "user_id":"service-user@example.org",
  "reporter_email":"jane@x.org",
  "is_agent":false,
  "categories":[{"name":"System Error"}],
  "priorities":[{"name":"Medium"}],
  "statuses":[{"name":"Open"}],
  "capabilities":{"ticket_messages":true,"attachments":true,"typing":false,"read_receipts":false,"push_notifications":false},
  "attachment_limits":{"max_files":5,"max_file_bytes":2097152,"max_total_bytes":6291456,"content_types":["application/pdf","image/jpeg","image/png","image/webp"],"encoding":"base64","max_image_pixels":20000000,"max_pdf_pages":100},
  "thread_poll_seconds":10,
  "site_timezone":"Africa/Nairobi"
}
```

Use `categories[].name` as create `category`. Reporter identity is authoritative; the client supplies the display name and facility. `is_agent` is informational and grants no broader plugin scope.

| Dependency | Example query | Item shape |
|---|---|---|
| get_counties | none | `{"name":"Mombasa","county_name":"Mombasa"}` |
| get_subcounties | `county=Mombasa` | `{"name":"Mombasa-Mvita","subcounty_name":"Mvita","county":"Mombasa"}` |
| get_facilities | `county=Mombasa&sub_county=Mombasa-Mvita&offset=0&limit=50` | `{"name":"facility-id","facility_name":"Facility Name","county":"Mombasa","sub_county":"Mombasa-Mvita","subcounty":"Mombasa-Mvita"}` |

County/sub-county responses use `data.items` without pagination metadata. Facilities use `items`, `has_more`, `next_offset`. Geography is optional UI assistance for choosing a facility; it is not a create prerequisite. The current hd-dev facility catalogue is empty; `items:[]` is valid, and the supplied facility text is still accepted. Do not confuse HD Facility Mapping demo routing records with the HD Facility catalogue.

## 6. Ticket comments, activity and chat

```http
GET /api/method/careverse_hq.api.helpdesk.get_thread?ticket_id=<ID>&offset=0&limit=50
POST /api/method/careverse_hq.api.helpdesk.send_message
```

Send body:

```json
{"ticket_id":"<ID>","content":"The workstation opens now, but registration still fails."}
```

Comments also accept multipart:

```bash
curl --fail-with-body \
  -H 'Authorization: token <CV_USER_KEY>:<CV_USER_SECRET>' \
  -F 'ticket_id=<ID>' \
  -F 'content=The error is still occurring.' \
  -F 'files=@registration.png;type=image/png' \
  'https://desk.tiberbu.app/api/method/careverse_hq.api.helpdesk.send_message'
```

The only multipart text fields are `ticket_id` and optional `content`; files use the repeated `files` part. Text-only comments can use the JSON body above. Retrieve comments/replies/activity using `get_thread?ticket_id=<ID>`.

Content is plain text, max 10,000 characters. Either nonblank content or one or more valid attachments is required. For an attachment-only message, omit content or send `""`; its display text is “Attachments”. Use the same `attachments` objects as create.

Result:

```json
{"ticket_id":"<ID>","accepted":true,"message_id":"comment:<comment-id>","attachments":[]}
```

When files were submitted, `attachments` contains their metadata. Comment and files commit together. Accepted means persisted, not read/delivered. Use the stable `message_id` to reconcile the subsequent thread response.

Thread result:

```json
{
  "items":[
    {"id":"comment:comment-id","kind":"message","author":"service-user@example.org","created_at":"2026-09-11 10:31:00.000000","content_text":"Please share an update.","content_html":"Please share an update.","attachments":[]},
    {"id":"activity:activity-id","kind":"activity","author":"support.agent@example.org","created_at":"2026-09-11 10:32:00.000000","content_text":"set status to Open","attachments":[]}
  ],
  "initial_attachments":[],
  "has_more":false,
  "next_offset":null
}
```

| kind | Source | Meaning |
|---|---|---|
| message | HD Ticket Comment | Public customer/agent comment, including plugin chat |
| reply | Communication | Initial description or email/portal reply; includes content_text and content_html |
| activity | HD Ticket Activity | Display-only action text for status, priority, team and other native history events |

Internal notes are excluded even for agents. Parent-ticket permissions protect activity reads. BCC/CC metadata and call recordings are not exposed. An initial communication may duplicate the description, so avoid rendering both as separate messages.

Every event additionally contains `attachments:[]` or an array of attachment metadata. Top-level `initial_attachments` contains the original report files, also available in ticket detail. Initial attachments are separate from chat events to avoid rendering the description twice.

Order is ascending `(created_at,id)`. Merge/deduplicate using stable prefixed event IDs. Prefer `content_text` for native rendering; sanitize rich HTML. Fetch detail and all thread pages on opening; poll from offset 0 every 10 seconds while foregrounded and after sending/reconnecting. Pause in the background and back off on failure. Offset pagination is not a durable incremental cursor and currently aggregates the full thread before slicing.

**Message sending is not retry-idempotent.** After an uncertain send, reconcile the thread before resending. Ticket creation's external reference does not deduplicate chat messages. Public comments reuse native notifications/realtime hooks. A comment on a resolved or closed ticket reopens it to the configured reopen status; it does not guarantee email delivery.

Not implemented: video/audio, typing, read receipts, unread counts, push delivery, message editing/deletion, or a consumer WebSocket subscription. Customer close and comment-based reopen are supported. Respect bootstrap capability flags.

## 6A. Screenshots, images and PDFs

### Upload shape and limits

There is no standalone upload RPC in this version. Consumer files travel inside multipart `files` parts or JSON `attachments` on `create_ticket`/`send_message`. CareVerse always forwards the same signed JSON transport to HD. Use `attachments:[]` or omit it when no files are selected. A screenshot is a normal image attachment.

Each object contains exactly these three fields:

```json
{"file_name":"registration.png","content_type":"image/png","content_base64":"<Base64 bytes; no data: prefix>"}
```

| Constraint | Value |
|---|---|
| Allowed extensions / MIME | `.png` / `image/png`; `.jpg` or `.jpeg` / `image/jpeg`; `.webp` / `image/webp`; `.pdf` / `application/pdf` |
| Files per create or message | At most 5 |
| Decoded bytes per file | 1–2,097,152 bytes (2 MiB) |
| Total decoded bytes per request | At most 6,291,456 bytes (6 MiB) |
| Filename | 1–120 ASCII characters; starts with a letter/digit; subsequent letters/digits, spaces, `.`, `_`, `-`; no `..` or paths |
| Images | Valid static PNG/JPEG/WebP; at most 20,000,000 pixels; declared MIME must match actual format |
| PDFs | Parseable PDF, unencrypted, 1–100 pages; native Frappe upload restrictions also apply |
| Base64 | Standard alphabet, valid padding, no whitespace/newlines/data-URL prefix |
| Signed HD body ceiling | 9 MiB of raw JSON; Base64 expands binary size by approximately one third |

Video, audio, GIF, SVG, HTML, archives and office documents are rejected. Convert device HEIC photos to an allowed format before submitting. Do not silently drop a selected unsupported file; explain the limit before submission. Additional site-level file restrictions can reject uploads even within these API limits.

The upload validates actual image/PDF content, not only a filename or MIME supplied by the client. Limits are file/pixel/page limits, not a malware scanning guarantee. All plugin files use native private storage on HD. No public file URL or file-system path is returned to consumer applications.

### Metadata and retrieval

The same metadata object appears in create results, ticket detail/list `attachments` (initial report files), message results, thread events, and the attachment list:

```json
{"attachment_id":"<file-id>","file_name":"registration.png","content_type":"image/png","size_bytes":12345,"is_private":true}
```

Native storage can normalize the filename or deduplicate identical bytes; use the returned opaque ID and returned filename. If the same bytes are selected more than once, native storage may reuse the underlying blob while retaining distinct File IDs.

```http
GET /api/method/careverse_hq.api.helpdesk.list_attachments?ticket_id=<ID>&offset=0&limit=50
GET /api/method/careverse_hq.api.helpdesk.download_attachment?ticket_id=<ID>&attachment_id=<file-id>
```

Internal equivalents use `helpdesk.api.plugin.list_attachments` and `helpdesk.api.plugin.download_attachment` with signed identity fields. Both require the authorized ticket ID; download additionally requires the attachment ID. An attachment ID alone is never authority.

List `data`:

```json
{"items":[{"attachment_id":"<file-id>","file_name":"registration.png","content_type":"image/png","size_bytes":12345,"is_private":true,"event_id":null}],"has_more":false,"next_offset":null}
```

`event_id:null` means an initial report attachment. Public comment/reply files use the matching `comment:<id>` or `communication:<id>`. The list groups initial files first, then public comments, then communications; it is not a chronological cursor. Native public reply attachments can be listed when private, locally stored, readable, within the stored size limit and matching an allowed type header. Full content validation runs on download; a malformed native file may therefore appear in metadata but fail download. Internal-note files, public URLs and remote linked files are excluded. Deleted files disappear from results. Initial manifest IDs are checked against their actual ticket association.

Download `data`:

```json
{"attachment_id":"<file-id>","file_name":"registration.png","content_type":"image/png","size_bytes":12345,"is_private":true,"event_id":null,"content_base64":"<standard Base64>","sha256":"<64 lowercase hex characters>"}
```

The API returns JSON through the normal CareVerse envelope, not a redirect, streaming response or permanent download link. HD performs a bounded local read and validates content before returning it, including native agent-uploaded files. Decode Base64 to bytes, optionally verify SHA-256, then preview the image or save/open the PDF using an appropriate viewer. Do not render file contents as HTML. Browser clients can use a Blob/object URL and revoke it when finished. No range requests, resumable/chunk uploads, thumbnail service, or deletion RPC is promised.

### Browser multipart submission example

The UI validates bootstrap limits, collects details and files, then invokes a single RPC. This example uses an already authenticated CareVerse session; supply its current CSRF token. Native mobile HTTP clients can construct the same multipart fields.

```javascript
async function submitIssue(details, selectedFiles, csrfToken) {
  // details.external_reference_id was persisted before the first attempt.
  const form = new FormData();
  for (const field of ["source", "external_reference_id", "category", "priority", "description"]) {
    form.append(field, details[field]);
  }
  form.append("reporter", JSON.stringify(details.reporter));
  for (const file of selectedFiles) form.append("files", file, file.name);
  const response = await fetch("/api/method/careverse_hq.api.helpdesk.create_ticket", {
    method: "POST",
    credentials: "include",
    headers: { "X-Frappe-CSRF-Token": csrfToken },
    body: form // Browser supplies the Content-Type and boundary.
  });
  const body = await response.json();
  if (!response.ok || body.message?.status !== "success") {
    throw new Error(body.message?.message || "Ticket submission failed");
  }
  return body.message.data;
}
```

Retain the draft and selected files until success. A timeout is uncertain, not proof of failure: retry the same business reference. A JSON retry without the attachment array can recover a committed result; if no ticket was committed it would create a text-only ticket, so **retry the full original payload until its outcome is known**. Once a successful ticket ID is known, send genuinely new files as a follow-up message. Message sending remains non-idempotent; reconcile using the thread before retrying an uncertain message.

## 7. Errors and client handling

| Situation | Consumer result / action |
|---|---|
| Missing CareVerse login | Framework authentication failure; sign in |
| Integration disabled or local signing configuration invalid | HTTP 503, CareVerse error envelope |
| HD connection failure | HTTP 502; creation can retry with the same business reference |
| HD timeout | HTTP 504; creation can retry with the same business reference; reconcile messages |
| Invalid attachment/type/size or changed retry attachment set | HTTP 417 validation failure; keep the draft and correct input. Oversized proxy requests can instead return HTTP 413 before JSON handling. |
| Invalid fields/category/priority | Usually HTTP 417 with `details.error_type = ValidationError`; refresh dependencies and correct payload |
| Missing or blank list facility | HTTP 400 from CareVerse with `message.message = "facility is required when listing tickets."` and `details.field = "facility"`; send the facility selected in the current CareVerse session |
| Wrong reporter or inaccessible ticket | HTTP 403; do not retry as another identity |
| Missing ticket | HTTP 404 |
| Downstream service authentication/signature/trust failure | HTTP 502; do not log out the CareVerse user; administrator fixes service credentials/trust |
| Malformed or unexpected upstream response | HTTP 502 |

Example CareVerse rejection:

```json
{"message":{"status":"error","message":"Helpdesk rejected the request.","details":{"error_type":"PermissionError","upstream_status":403,"request_id":"<trace-id>"}}}
```

Pre-dispatch Frappe errors may use framework `exc_type`/`exception` instead of the application envelope. Internal HD signature rejection is HTTP 401; other HD errors use native Frappe error responses. Do not expose stack traces to end users. Connection/time-out errors may omit details. A duplicate reference from its original reporter is success, not an error.

## 8. CareVerse → Helpdesk Ed25519 protocol

All twelve HD plugin methods require native API-token authentication as an enabled non-Administrator Helpdesk service user, plus mandatory Ed25519 verification. The `allow_guest=True` declarations only permit entry into the guard; it rejects missing service credentials. An HD cookie alone cannot authenticate this transport. The signed CareVerse reporter may be any non-Guest identity, including Administrator for bench testing, and needs no HD account or mapping.

No instance ID or originating site URL is sent in headers, query parameters or JSON. Helpdesk trusts exactly one CareVerse origin configured locally. Requests containing legacy `instance_id`, `origin` or `careverse_url` arguments are rejected. CareVerse adds only these fields to business arguments:

| Field | Origin |
|---|---|
| user_id | Authenticated CareVerse session user; cannot be selected by the app |
| request_id | Fresh UUID hex for each outbound attempt |

Internal create body:

```json
{"source":"HMIS","external_reference_id":"your-issue-id","reporter":{"name":"Jane Doe","email":"jane@x.org","facility":"Facility Name"},"category":"System Error","priority":"Medium","description":"issue text here","user_id":"jane@x.org","request_id":"550e8400e29b41d4a716446655440000"}
```

GET includes these fields in its query and has an empty body. POST includes them in JSON, with no query string. Duplicate query parameters/JSON keys and missing/unexpected arguments are rejected. Dispatch uses verified raw bytes, never unsigned alternate kwargs.

Canonical UTF-8 string:

```text
UPPERCASE_METHOD + "\n" + EXACT_PATH_AND_QUERY + "\n" + UTC_TIMESTAMP + "\n" + SHA256_HEX(EXACT_BODY_BYTES)
```

For create, the path is exactly `/api/method/helpdesk.api.plugin.create_ticket`. GET preserves exact query ordering/encoding and hashes empty body bytes. POST signs the same JSON bytes that are transmitted. Do not serialize again after signing.

Headers:

```http
Authorization: token <configured-service-api-key>:<configured-service-api-secret>
X-AC-Key-Id: <key-id>
X-AC-Timestamp: 2026-09-11T10:30:00Z
X-AC-Signature: <standard-base64-of-Ed25519-signature>
Content-Type: application/json
```

Timestamp tolerance is ±30 seconds. Synchronize server clocks. `request_id` length is 16–128; an atomic Redis replay guard retains it for 90 seconds per instance. Retransmitting the same signed request fails; generate a new signed request while retaining the business reference. URL aliases and `cmd` dispatch are unsupported.

### Public-key discovery

Helpdesk fetches only the administrator-configured origin:

```http
GET <Helpdesk site_config.careverse_url>/api/method/careverse_hq.api.hmis_signing.get_public_key
```

```json
{"message":{"status":"success","data":{"key_id":"<id>","public_key_pem":"-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"}}}
```

The endpoint is public and returns no private material. Key ID must equal the first 16 hex characters of SHA-256 of the PEM text; the parsed key must be Ed25519. TLS verification is enabled; redirects are rejected; timeout is 5 seconds; maximum response size is 32 KiB.

Keys cache for 300 seconds per instance/origin. Simultaneous first requests wait up to five seconds for the in-flight discovery result, reading the shared cache rather than a stale request-local miss. Unknown IDs may trigger one refresh per 30 seconds. A rotated key can require a retry after this cooldown. Old cached keys can remain accepted until expiry: disable the instance for immediate revocation. Expired cache with unavailable discovery fails closed. Callers cannot choose a key URL.

## 9. Configuration and deployment

CareVerse **Helpdesk Integration Settings** contains `enabled`, `helpdesk_url`, `api_key` and encrypted Password `api_secret`. These are the dedicated Helpdesk service user's native API credentials. The existing HMIS Auth Settings keypair supplies Ed25519 signatures. Never send service credentials to the mobile app or put them in code.

Helpdesk site config supplies `careverse_url`, the only public-key origin. Keep its local **HD CareVerse Instance** trust record enabled. Its hostname-based name is retained as the ownership scope and never transported. `careverse_trust_record` remains an optional local compatibility override. Legacy user mappings are hidden and ignored. Disable the service user or trust record to stop subsequent operations.

Use one enabled Helpdesk Customer service user. Native ticket permissions still apply; the plugin additionally scopes every read/write by local trust scope, signed reporter and service owner. Native `raised_by` and native comment author may be the service identity; reporter metadata preserves the CareVerse user. No Helpdesk reporter-account creation or per-user mapping is needed.

Deploy both apps, migrate their sites, set the service credentials, and restart. Existing signature-only callers must be upgraded together with Helpdesk. When changing the execution account, migrate only this integration's attributed tickets' native `raised_by` to the new service account, preserving plugin reporter/scope/reference/key fields. Existing demos on hd-dev were migrated this way; IDs and retry keys remain intact. Rotating API credentials for the same account does not require ownership migration.

See the support WI in CareVerse `docs/api/HELPDESK_SUPPORT_CONFIGURATION_WI.md`. Mobile routes, payloads and success envelopes do not change. The facility catalogue remains empty and demo tickets route to Billing without assigned agents.

## 10. Implementation sequence and validation

Consumer flow:

1. Authenticate to CareVerse; GET bootstrap and populate category/priority choices.
2. Optionally load location/facility GETs; obtain reporter email from bootstrap.
3. Persist a stable external reference locally; collect selected files and POST one multipart form or JSON create payload.
4. Navigate with `data.ticket_id`; GET detail, facility/user-filtered ticket pages ordered newest first, and the public thread.
5. Send public text/attachment messages, reconcile/poll the thread, and retrieve private files through the download RPC.
6. Retry uncertain creates with the same reference; distinguish login errors from downstream failures.

Repeatable checks, from `/home/ubuntu/frappe-bench/sites`:

```bash
../env/bin/python -m unittest careverse_hq.tests.test_helpdesk_bridge helpdesk.tests.test_plugin_discovery helpdesk.tests.test_plugin_media
../env/bin/python ../apps/helpdesk/scripts/validate_plugin_rpc.py
```

The development script is pinned to hd-dev. Attachment checks cover combined image/PDF creation, stable retries, private download bytes/checksums, attachment-only messages, invalid type/Base64/path/size rejection, cross-ticket/instance denial, and full rollback after a simulated failure following file persistence. Three media unit tests cover supported image formats, native video disguised as PNG, and a bounded read despite stale size metadata. A live HTTPS test verified combined screenshot/PDF creation, concurrent retries retaining the same file IDs, exact downloaded bytes/checksums and screenshot messages through CareVerse to HD; its temporary ticket was deleted afterwards. Direct unauthenticated access to the private HD file was denied; the fixture also verifies that agent public files are accessible while internal-note files are hidden and denied. It rolls back temporary users, agents, assignment rules and tickets, mutes email, and uses real Ed25519 signing with mocked public-key HTTP discovery. It verifies exact creation payload, original-ticket retry, reporter spoofing denial, instance/source separation, public chat/activity and hidden notes, native round-robin rotation with two temporary agents, unchanged assignment on retry, timestamps, tampering, replay, and public-key discovery/cache behavior. The unique schema provides concurrent arbitration; this fixture harness does not simulate a concurrent HTTP race. A separate live test cleared the instance public-key cache, sent two simultaneous CareVerse creates over HTTP, and verified one ticket with one `reused:false` and one `reused:true` response. It also verified live detail/list, message persistence/thread retrieval, and all dependency GETs. Only that run's temporary ticket was deleted afterwards.

CareVerse unit tests cover fixed destination, signed identity injection, exact create payload forwarding, reporter email forwarding, disabled integration, malformed responses and upstream-auth error handling. Two discovery unit tests cover the cold-cache waiter and rejection of a different published key. Live CareVerse-to-HD tests exercise actual HTTPS signing and key discovery across all twelve RPCs; they do not replace consumer login testing.

Sources: `careverse_hq/api/helpdesk.py`, existing `careverse_hq/api/hmis_transport.py` and `hmis_signing.py`; `helpdesk/api/plugin.py`, `plugin_media.py`, internal `mobile.py`, `mobile_signing.py`, both configuration DocTypes and HD Ticket schema. This contract is maintained identically at `docs/api/HMIS_MOBILE_TICKETING_V1.md` in both repositories.

### Multipart and filter validation

A historical mapping-based live HTTPS check used temporary authenticated CareVerse/HD users and real API credentials (removed afterwards). It verified multipart creation with two binary files, retry stability, exact private screenshot download, facility/user filtering, newest-first pages, denial of another user filter, multipart comments, chat retrieval and single-ticket detail. Its temporary tickets, files, mapping and accounts were removed. The current service-account acceptance is recorded below; it supersedes the historical mapping transport. Unit tests additionally cover multipart normalization, repeated files, duplicate/unknown field rejection and duplicate reporter JSON keys. Signed-reporter own-ticket authorization remains unchanged.

## Service-account acceptance — 2026-09-15

67 contract, 34 real login-session/CSRF and 10 transport/signature/diagnostic checks passed on desk.tiberbu.app → hd-dev.tiberbu.app, plus 39 unit tests (24 CareVerse bridge, 15 Helpdesk). New CareVerse reporters had no HD accounts or mappings. Reporter isolation, existing demos and create retries were preserved. Signature-only requests are now rejected without configured service credentials. CareVerse contains detailed evidence in `docs/api/HELPDESK_SERVICE_ACCOUNT_RESULTS_2026-09-15.md`. Earlier mapping-based fixture results above are historical, not evidence of current transport behavior. UAT and native mobile release certification remain separate.
