# HMIS → Helpdesk API Integration Guide

## 🎯 Overview

This API allows your HMIS system to automatically create and manage support tickets in the Helpdesk app when implementors raise issues.

**Base URL:** `https://support.tiberbu.app`

---

## 📋 Table of Contents

1. [Setup & Authentication](#setup--authentication)
2. [API Endpoints](#api-endpoints)
3. [Usage Examples](#usage-examples)
4. [Error Handling](#error-handling)
5. [Webhooks](#webhooks)
6. [Testing](#testing)

---

## 🔐 Setup & Authentication

### Step 1: Enable External API in Helpdesk

1. Log in to Helpdesk as Administrator
2. Go to: **Settings → HD Settings**
3. Scroll to **"External API Integration"** section
4. Check ☑️ **"Enable External API"**
5. Generate and save:
   - **API Key**: A unique identifier (e.g., `hmis_api_key_2026`)
   - **API Secret**: A secure password (e.g., `your-secure-secret-here`)
6. Click **Save**

⚠️ **Keep your API Secret secure!** Treat it like a password.

---

### Step 2: Test Authentication

```bash
curl -X POST https://support.tiberbu.app/api/method/helpdesk.api.external_integration.get_ticket_status \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "1",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
  }'
```

If authentication works, you'll get ticket details. If not, you'll see:
```json
{
  "exc_type": "AuthenticationError",
  "exception": "Invalid API credentials"
}
```

---

## 🔌 API Endpoints

### 1. Create Ticket from HMIS

**Endpoint:** `POST /api/method/helpdesk.api.external_integration.create_ticket_from_hmis`

**Description:** Creates a new support ticket when an issue is raised in HMIS.

**Request Body:**

```json
{
  "subject": "Unable to save patient record",
  "description": "Getting timeout error when saving patient admission form in Ward Management module",
  "raised_by_email": "implementor@facility.com",
  "raised_by_name": "John Implementor",
  "priority": "High",
  "ticket_type": "Issue",
  "category": "Technical Support",
  "external_reference_id": "HMIS-ISSUE-12345",
  "hmis_module": "Patient Management",
  "hmis_url": "https://hmis.yourcompany.com/issues/12345",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}
```

**Required Fields:**
- `subject` (string) - Ticket title
- `description` (string) - Detailed description
- `raised_by_email` (string) - Email of person reporting issue
- `api_key` (string) - Your API key
- `api_secret` (string) - Your API secret

**Optional Fields:**
- `raised_by_name` (string) - Full name of reporter
- `priority` (string) - `Low`, `Medium`, `High`, or `Urgent` (default: `Medium`)
- `ticket_type` (string) - Type of ticket
- `category` (string) - Ticket category
- `external_reference_id` (string) - HMIS issue ID for tracking
- `hmis_module` (string) - Which HMIS module has the issue
- `hmis_url` (string) - Direct link to issue in HMIS
- `custom_fields` (object) - Additional custom field values

**Response (Success):**

```json
{
  "success": true,
  "ticket_id": "TKT-00123",
  "ticket_name": "TKT-00123",
  "ticket_url": "https://support.tiberbu.app/helpdesk/tickets/TKT-00123",
  "ticket_subject": "Unable to save patient record",
  "ticket_status": "Open",
  "ticket_priority": "High",
  "created_on": "2026-06-11 14:30:00",
  "message": "Ticket TKT-00123 created successfully"
}
```

**Response (Error):**

```json
{
  "exc_type": "AuthenticationError",
  "exception": "Invalid API credentials. Please check your API key and secret."
}
```

---

### 2. Update Ticket from HMIS

**Endpoint:** `POST /api/method/helpdesk.api.external_integration.update_ticket_from_hmis`

**Description:** Update an existing ticket (add comments, change status/priority)

**Request Body:**

```json
{
  "ticket_id": "TKT-00123",
  "comment": "User confirmed issue is resolved after database optimization",
  "status": "Resolved",
  "priority": "Medium",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}
```

**Required Fields:**
- `ticket_id` (string) - Helpdesk ticket ID (from create response)
- `api_key` (string)
- `api_secret` (string)

**Optional Fields:**
- `comment` (string) - Add a comment/update to the ticket
- `status` (string) - Update status: `Open`, `Replied`, `Resolved`, `Closed`
- `priority` (string) - Update priority: `Low`, `Medium`, `High`, `Urgent`

**Response:**

```json
{
  "success": true,
  "ticket_id": "TKT-00123",
  "ticket_status": "Resolved",
  "ticket_priority": "Medium",
  "message": "Ticket TKT-00123 updated successfully"
}
```

---

### 3. Get Ticket Status

**Endpoint:** `POST /api/method/helpdesk.api.external_integration.get_ticket_status`

**Description:** Check current status of a ticket

**Request Body:**

```json
{
  "ticket_id": "TKT-00123",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}
```

**Response:**

```json
{
  "success": true,
  "ticket_id": "TKT-00123",
  "subject": "Unable to save patient record",
  "status": "Resolved",
  "priority": "High",
  "raised_by": "implementor@facility.com",
  "agent_group": "Technical Support",
  "assigned_to": "support@tiberbu.com",
  "created_on": "2026-06-11 14:30:00",
  "modified_on": "2026-06-11 16:45:00",
  "first_response_time": "2026-06-11 14:45:00",
  "resolution_date": "2026-06-11 16:45:00"
}
```

---

## 💻 Usage Examples

### Python Example

```python
import requests
import json

# Configuration
HELPDESK_URL = "https://support.tiberbu.app"
API_KEY = "your-api-key"
API_SECRET = "your-api-secret"

def create_helpdesk_ticket(issue_data):
    """
    Create a helpdesk ticket from HMIS issue
    """
    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.create_ticket_from_hmis"
    
    payload = {
        "subject": issue_data["title"],
        "description": issue_data["description"],
        "raised_by_email": issue_data["user_email"],
        "raised_by_name": issue_data["user_name"],
        "priority": "High",
        "external_reference_id": issue_data["issue_id"],
        "hmis_module": issue_data["module"],
        "hmis_url": issue_data["url"],
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ Ticket created: {result['ticket_id']}")
            print(f"   URL: {result['ticket_url']}")
            return result
        else:
            print(f"❌ Error: {result.get('exception')}")
            return None
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return None

# Example usage
issue = {
    "issue_id": "HMIS-12345",
    "title": "Cannot generate patient report",
    "description": "PDF generation fails with 500 error",
    "user_email": "nurse@facility.com",
    "user_name": "Jane Nurse",
    "module": "Reports",
    "url": "https://hmis.example.com/issues/12345"
}

ticket = create_helpdesk_ticket(issue)
```

---

### PHP Example

```php
<?php

function createHelpdeskTicket($issueData) {
    $helpdeskUrl = "https://support.tiberbu.app";
    $apiKey = "your-api-key";
    $apiSecret = "your-api-secret";
    
    $endpoint = $helpdeskUrl . "/api/method/helpdesk.api.external_integration.create_ticket_from_hmis";
    
    $payload = [
        "subject" => $issueData["title"],
        "description" => $issueData["description"],
        "raised_by_email" => $issueData["user_email"],
        "raised_by_name" => $issueData["user_name"],
        "priority" => "High",
        "external_reference_id" => $issueData["issue_id"],
        "hmis_module" => $issueData["module"],
        "hmis_url" => $issueData["url"],
        "api_key" => $apiKey,
        "api_secret" => $apiSecret
    ];
    
    $ch = curl_init($endpoint);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200) {
        $result = json_decode($response, true);
        if ($result['success']) {
            echo "✅ Ticket created: " . $result['ticket_id'] . "\n";
            return $result;
        }
    }
    
    echo "❌ Error creating ticket\n";
    return null;
}

// Example usage
$issue = [
    "issue_id" => "HMIS-12345",
    "title" => "Cannot generate patient report",
    "description" => "PDF generation fails with 500 error",
    "user_email" => "nurse@facility.com",
    "user_name" => "Jane Nurse",
    "module" => "Reports",
    "url" => "https://hmis.example.com/issues/12345"
];

createHelpdeskTicket($issue);
?>
```

---

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const HELPDESK_URL = 'https://support.tiberbu.app';
const API_KEY = 'your-api-key';
const API_SECRET = 'your-api-secret';

async function createHelpdeskTicket(issueData) {
    const endpoint = `${HELPDESK_URL}/api/method/helpdesk.api.external_integration.create_ticket_from_hmis`;
    
    const payload = {
        subject: issueData.title,
        description: issueData.description,
        raised_by_email: issueData.userEmail,
        raised_by_name: issueData.userName,
        priority: 'High',
        external_reference_id: issueData.issueId,
        hmis_module: issueData.module,
        hmis_url: issueData.url,
        api_key: API_KEY,
        api_secret: API_SECRET
    };
    
    try {
        const response = await axios.post(endpoint, payload);
        
        if (response.data.success) {
            console.log(`✅ Ticket created: ${response.data.ticket_id}`);
            console.log(`   URL: ${response.data.ticket_url}`);
            return response.data;
        }
    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
        return null;
    }
}

// Example usage
const issue = {
    issueId: 'HMIS-12345',
    title: 'Cannot generate patient report',
    description: 'PDF generation fails with 500 error',
    userEmail: 'nurse@facility.com',
    userName: 'Jane Nurse',
    module: 'Reports',
    url: 'https://hmis.example.com/issues/12345'
};

createHelpdeskTicket(issue);
```

---

### cURL Example

```bash
curl -X POST https://support.tiberbu.app/api/method/helpdesk.api.external_integration.create_ticket_from_hmis \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Unable to save patient record",
    "description": "Getting timeout error when saving patient admission form",
    "raised_by_email": "implementor@facility.com",
    "raised_by_name": "John Implementor",
    "priority": "High",
    "external_reference_id": "HMIS-ISSUE-12345",
    "hmis_module": "Patient Management",
    "hmis_url": "https://hmis.yourcompany.com/issues/12345",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
  }'
```

---

## ⚠️ Error Handling

### Common Error Responses

**1. Invalid Credentials (403)**
```json
{
  "exc_type": "AuthenticationError",
  "exception": "Invalid API credentials. Please check your API key and secret."
}
```
→ **Fix:** Check API key and secret in HD Settings

---

**2. Missing Required Fields (417)**
```json
{
  "exc_type": "MandatoryError",
  "exception": "Missing required fields: subject, description, and raised_by_email are mandatory"
}
```
→ **Fix:** Ensure all required fields are included

---

**3. Ticket Not Found (404)**
```json
{
  "exc_type": "DoesNotExistError",
  "exception": "Ticket TKT-99999 not found"
}
```
→ **Fix:** Verify ticket ID is correct

---

**4. External API Disabled (403)**
```json
{
  "exc_type": "AuthenticationError",
  "exception": "Invalid API credentials"
}
```
→ **Fix:** Enable External API in HD Settings

---

### Error Handling Best Practices

```python
def create_ticket_safely(issue_data):
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        
        # Check HTTP status
        if response.status_code != 200:
            log_error(f"HTTP {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        
        # Check API success flag
        if not result.get("success"):
            log_error(f"API Error: {result.get('exception')}")
            return None
        
        # Success!
        return result
        
    except requests.exceptions.Timeout:
        log_error("Request timeout - helpdesk may be slow")
        return None
        
    except requests.exceptions.ConnectionError:
        log_error("Cannot connect to helpdesk - check network")
        return None
        
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        return None
```

---

## 🔔 Webhooks (Optional)

If you want Helpdesk to **push updates back to HMIS**, use the webhook endpoint:

**Endpoint:** `POST /api/method/helpdesk.api.external_integration.hmis_webhook`

**Use Cases:**
- Notify HMIS when ticket is resolved
- Sync status changes back to HMIS
- Update HMIS issue with ticket responses

**Example Webhook Payload:**

```json
{
  "event": "issue_created",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "data": {
    "reference_id": "HMIS-12345",
    "subject": "Issue title",
    "description": "Issue details",
    "user_email": "user@facility.com",
    "priority": "High",
    "module": "Reports",
    "url": "https://hmis.example.com/issues/12345"
  }
}
```

**Supported Events:**
- `issue_created` - Create new ticket
- `issue_updated` - Update existing ticket

---

## 🧪 Testing

### Test Script

Save as `test_hmis_api.py`:

```python
import requests
import json
from datetime import datetime

HELPDESK_URL = "https://support.tiberbu.app"
API_KEY = "your-api-key"
API_SECRET = "your-api-secret"

def test_create_ticket():
    """Test creating a ticket"""
    print("🧪 Testing ticket creation...")
    
    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.create_ticket_from_hmis"
    
    payload = {
        "subject": f"Test Ticket - {datetime.now().isoformat()}",
        "description": "This is a test ticket created via API",
        "raised_by_email": "test@facility.com",
        "raised_by_name": "Test User",
        "priority": "Low",
        "external_reference_id": f"TEST-{datetime.now().timestamp()}",
        "hmis_module": "Testing",
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ SUCCESS: Ticket {result['ticket_id']} created")
            print(f"   URL: {result['ticket_url']}")
            return result['ticket_id']
        else:
            print(f"❌ FAILED: {result.get('exception')}")
    else:
        print(f"❌ HTTP ERROR: {response.status_code}")
        print(response.text)
    
    return None

def test_get_status(ticket_id):
    """Test getting ticket status"""
    print(f"\n🧪 Testing get status for {ticket_id}...")
    
    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.get_ticket_status"
    
    payload = {
        "ticket_id": ticket_id,
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ SUCCESS: Got ticket status")
            print(f"   Status: {result['status']}")
            print(f"   Priority: {result['priority']}")
        else:
            print(f"❌ FAILED: {result.get('exception')}")
    else:
        print(f"❌ HTTP ERROR: {response.status_code}")

def test_update_ticket(ticket_id):
    """Test updating a ticket"""
    print(f"\n🧪 Testing update for {ticket_id}...")
    
    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.update_ticket_from_hmis"
    
    payload = {
        "ticket_id": ticket_id,
        "comment": "This is a test comment added via API",
        "priority": "Medium",
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ SUCCESS: Ticket updated")
        else:
            print(f"❌ FAILED: {result.get('exception')}")
    else:
        print(f"❌ HTTP ERROR: {response.status_code}")

# Run tests
if __name__ == "__main__":
    print("="*60)
    print("HMIS → Helpdesk API Integration Test")
    print("="*60)
    
    # Test 1: Create ticket
    ticket_id = test_create_ticket()
    
    if ticket_id:
        # Test 2: Get status
        test_get_status(ticket_id)
        
        # Test 3: Update ticket
        test_update_ticket(ticket_id)
    
    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)
```

**Run the test:**
```bash
python3 test_hmis_api.py
```

---

## 📚 Integration Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    HMIS System                          │
│                                                         │
│  1. User raises issue in HMIS                          │
│  2. HMIS captures issue details                        │
│  3. HMIS calls Helpdesk API                            │
│     POST /api/method/.../create_ticket_from_hmis       │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Helpdesk System                         │
│                                                         │
│  4. Authenticate API credentials                        │
│  5. Create HD Ticket with HMIS reference               │
│  6. Assign to appropriate team                          │
│  7. Return ticket ID & URL                             │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  HMIS System                            │
│                                                         │
│  8. Store ticket ID in HMIS issue                      │
│  9. Display link to helpdesk ticket                    │
│  10. (Optional) Sync status updates                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Best Practices

1. **Keep API Secret Secure**
   - Never commit to version control
   - Use environment variables
   - Rotate periodically

2. **Use HTTPS Only**
   - All API calls must use HTTPS
   - Never send credentials over HTTP

3. **Validate Responses**
   - Always check `success` flag
   - Handle errors gracefully
   - Log failures for debugging

4. **Rate Limiting**
   - Don't spam the API
   - Implement retry logic with backoff
   - Cache ticket status when possible

5. **IP Whitelisting (Optional)**
   - Configure firewall to allow only HMIS server IP
   - Contact support@tiberbu.com to whitelist IPs

---

## 📞 Support

For API issues or questions:

- **Email:** support@tiberbu.com
- **Documentation:** https://support.tiberbu.app/api/docs
- **Create Ticket:** https://support.tiberbu.app/my-tickets/new

---

## 📝 Changelog

### Version 1.0 (2026-06-11)
- Initial release
- Create ticket endpoint
- Update ticket endpoint
- Get status endpoint
- Webhook support
