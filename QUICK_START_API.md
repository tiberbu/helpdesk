# 🚀 Quick Start: HMIS API Integration

Get your HMIS connected to the Helpdesk in **5 minutes**!

---

## Step 1: Enable API in Helpdesk (2 minutes)

1. **Log in** to https://support.tiberbu.app as Administrator

2. **Go to Settings**
   - Click the gear icon ⚙️ in the sidebar
   - Click **"HD Settings"**

3. **Scroll to "External API Integration"** section

4. **Enable and configure:**
   - ☑️ Check **"Enable External API"**
   - Set **API Key**: `hmis_api_2026` (or any unique string)
   - Set **API Secret**: `YourSecureSecret123!` (use a strong password)
   - Click **Save**

✅ **API is now enabled!**

---

## Step 2: Test the API (1 minute)

### Option A: Quick Test with cURL

```bash
curl -X POST https://support.tiberbu.app/api/method/helpdesk.api.external_integration.create_ticket_from_hmis \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "description": "Testing HMIS integration",
    "raised_by_email": "test@facility.com",
    "api_key": "hmis_api_2026",
    "api_secret": "YourSecureSecret123!"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "ticket_id": "TKT-00123",
  "ticket_url": "https://support.tiberbu.app/helpdesk/tickets/TKT-00123",
  ...
}
```

---

### Option B: Test with Python Script

```bash
cd /home/ubuntu/frappe-bench/apps/helpdesk

# Edit the script and add your credentials
nano test_hmis_api.py
# Change API_KEY and API_SECRET to your values

# Run the test
python3 test_hmis_api.py
```

---

## Step 3: Integrate with HMIS (2 minutes)

### Copy this code into your HMIS:

```python
import requests

def create_helpdesk_ticket(issue):
    """
    Call this function whenever an implementor raises an issue in HMIS
    """
    endpoint = "https://support.tiberbu.app/api/method/helpdesk.api.external_integration.create_ticket_from_hmis"
    
    payload = {
        # Required fields
        "subject": issue["title"],
        "description": issue["description"],
        "raised_by_email": issue["user_email"],
        
        # Authentication
        "api_key": "hmis_api_2026",  # Your API key from HD Settings
        "api_secret": "YourSecureSecret123!",  # Your API secret
        
        # Optional but recommended
        "raised_by_name": issue["user_name"],
        "priority": "High",
        "external_reference_id": issue["id"],  # HMIS issue ID
        "hmis_module": issue["module"],
        "hmis_url": f"https://hmis.yourcompany.com/issues/{issue['id']}"
    }
    
    response = requests.post(endpoint, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            # Success! Store ticket_id in your HMIS database
            return result["ticket_id"]
    
    return None


# Example: When implementor creates issue in HMIS
issue = {
    "id": "HMIS-12345",
    "title": "Cannot save patient record",
    "description": "Getting timeout error",
    "user_email": "implementor@facility.com",
    "user_name": "John Implementor",
    "module": "Patient Management"
}

ticket_id = create_helpdesk_ticket(issue)
print(f"Created helpdesk ticket: {ticket_id}")
```

---

## ✅ Done!

Your HMIS is now connected to the Helpdesk!

When implementors raise issues in HMIS, tickets will automatically be created in the helpdesk system.

---

## 📊 What Happens Next?

```
Implementor raises issue in HMIS
         ↓
HMIS calls Helpdesk API
         ↓
Ticket created automatically
         ↓
Support team gets notified
         ↓
Issue is tracked and resolved
         ↓
(Optional) Update synced back to HMIS
```

---

## 🔍 Verify It Works

1. **In HMIS**: Create a test issue
2. **Check Helpdesk**: https://support.tiberbu.app/helpdesk/tickets
3. **Look for**: The ticket with "External Reference ID" field populated

---

## 📚 Full Documentation

For advanced features, error handling, and complete API reference:

**📖 Read:** `/home/ubuntu/frappe-bench/apps/helpdesk/HMIS_API_INTEGRATION.md`

Or online: `https://support.tiberbu.app/api/docs`

---

## 🆘 Troubleshooting

### "Invalid API credentials"
- Check API Key and Secret in HD Settings
- Make sure "Enable External API" is checked

### "Missing required fields"
- Ensure subject, description, and raised_by_email are included

### "Connection refused"
- Check firewall allows HTTPS (port 443)
- Verify helpdesk URL is correct

### Still stuck?
Create a ticket: https://support.tiberbu.app/my-tickets/new

---

## 🔐 Security Reminders

- ✅ Keep API Secret secure (like a password)
- ✅ Use HTTPS only (never HTTP)
- ✅ Don't commit credentials to version control
- ✅ Use environment variables in production

---

**That's it! You're all set! 🎉**
