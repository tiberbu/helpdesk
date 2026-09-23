import frappe

def send():
    api_key = "DZaLRbVp2rXkgTtYBcePQd84xltDsjoT"
    api_secret = "dRwAbpmgch7ucEex#8I@P.,6;]iOU*i?;dH93LJV8&HLq:}k"

    message = """
<p>Hi Kagai,</p>
<p>Below is the full API reference for integrating HMIS with the Helpdesk system. When an issue is raised in HMIS, it will automatically create a ticket in the support portal.</p>

<hr>
<h2>Base URL</h2>
<pre>https://support.tiberbu.app</pre>

<h2>Authentication</h2>
<p>Pass these credentials in the body of every request:</p>
<pre>api_key:    {api_key}
api_secret: {api_secret}</pre>

<hr>
<h2>1. Create Ticket</h2>
<pre>POST /api/method/helpdesk.api.external_integration.create_ticket_from_hmis</pre>

<p><strong>Required:</strong> subject, description, raised_by_email, api_key, api_secret</p>
<p><strong>Optional:</strong> raised_by_name, facility, custom_phone, custom_section, priority, external_reference_id, hmis_module</p>

<h3>Field Mapping from your current HMIS payload:</h3>
<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>HMIS field</th><th>API field</th></tr>
  <tr><td>raised_by (session user email)</td><td>raised_by_email</td></tr>
  <tr><td>name (full_name)</td><td>raised_by_name</td></tr>
  <tr><td>custom_location</td><td>facility</td></tr>
  <tr><td>custom_phone</td><td>custom_phone</td></tr>
  <tr><td>subject</td><td>subject</td></tr>
  <tr><td>custom_section</td><td>custom_section</td></tr>
  <tr><td>description</td><td>description</td></tr>
  <tr><td>agent_group</td><td>(auto-set to TAIFACARE SUPPORT)</td></tr>
</table>

<h3>Python Example:</h3>
<pre>
import requests

API_KEY = "{api_key}"
API_SECRET = "{api_secret}"
BASE_URL = "https://support.tiberbu.app"

def create_ticket(issue):
    response = requests.post(
        f"{{BASE_URL}}/api/method/helpdesk.api.external_integration.create_ticket_from_hmis",
        json={{
            "subject": issue["subject"],
            "description": issue["description"],
            "raised_by_email": issue["raised_by"],
            "raised_by_name": issue["name"],
            "facility": issue["custom_location"],
            "custom_phone": issue["custom_phone"],
            "custom_section": issue["custom_section"],
            "api_key": API_KEY,
            "api_secret": API_SECRET
        }},
        timeout=30
    )
    result = response.json().get("message", {{}})
    return result.get("ticket_id")
</pre>

<h3>cURL Example:</h3>
<pre>
curl -X POST https://support.tiberbu.app/api/method/helpdesk.api.external_integration.create_ticket_from_hmis \\
  -H "Content-Type: application/json" \\
  -d '{{
    "subject": "Test Issue",
    "description": "Details here",
    "raised_by_email": "user@facility.go.ke",
    "raised_by_name": "John Doe",
    "facility": "Maktau Health Centre",
    "custom_phone": "0712345678",
    "custom_section": "OPD",
    "api_key": "{api_key}",
    "api_secret": "{api_secret}"
  }}'
</pre>

<h3>Success Response:</h3>
<pre>
{{
  "message": {{
    "success": true,
    "ticket_id": "91",
    "ticket_url": "https://support.tiberbu.app/helpdesk/tickets/91",
    "ticket_status": "Open",
    "ticket_priority": "High"
  }}
}}
</pre>

<hr>
<h2>2. Get Ticket Status</h2>
<pre>POST /api/method/helpdesk.api.external_integration.get_ticket_status</pre>
<p><strong>Required:</strong> ticket_id (string), api_key, api_secret</p>

<hr>
<h2>3. Update Ticket</h2>
<pre>POST /api/method/helpdesk.api.external_integration.update_ticket_from_hmis</pre>
<p><strong>Required:</strong> ticket_id (string), api_key, api_secret</p>
<p><strong>Optional:</strong> comment, priority, status</p>

<hr>
<h2>Important Notes</h2>
<ol>
  <li><strong>ticket_id must be a string</strong> — always convert with str()</li>
  <li><strong>Response is wrapped</strong> in a "message" key — access via response.json()["message"]</li>
  <li><strong>Always check</strong> result["success"] == true before proceeding</li>
  <li><strong>HTTPS only</strong> — never use HTTP</li>
  <li><strong>Set timeout to 30s</strong> on all requests</li>
</ol>

<p>Regards,<br>TaifaCare Support Team</p>
""".format(api_key=api_key, api_secret=api_secret)

    frappe.sendmail(
        recipients=["kagai@tiberbu.com"],
        sender="no-reply@kenya-hie.health",
        subject="HMIS x Helpdesk API Integration — Full Reference",
        message=message,
        now=True
    )
    print("Email sent successfully.")
