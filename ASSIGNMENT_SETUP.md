# Round-Robin Ticket Assignment Setup

## What Was Configured

### ✅ Users Created
- **keneth@tiberbu.com** (Kenneth) - Agent
- **kagai@tiberbu.com** (Karen) - Agent

Both users have been:
1. Created in the system with Agent role
2. Set up as HD Agent profiles
3. Enabled and ready to receive assignments

### ✅ Assignment Rule Created
**Name:** Auto-Assign All Tickets

**Configuration:**
- **Document Type:** HD Ticket
- **Rule Type:** Round Robin
- **Status:** Enabled (disabled = 0)
- **Priority:** 0 (highest - runs first)
- **Trigger Condition:** `status == 'Open'`

**Assignment Order:**
1. First ticket → keneth@tiberbu.com
2. Second ticket → kagai@tiberbu.com
3. Third ticket → keneth@tiberbu.com
4. And so on...

**Active Days:** Monday - Sunday (all week)

## How It Works

When a new ticket is created or updated with `status = 'Open'`:
1. The assignment rule automatically triggers
2. The next agent in rotation is selected (Kenneth → Karen → Kenneth...)
3. The ticket is assigned to that agent
4. A ToDo is created for the agent
5. The agent receives a notification

## Testing the Assignment

### Method 1: Via Web Interface (Recommended)
1. Go to https://support.tiberbu.app/helpdesk or https://erp.local/helpdesk
2. Click "New Ticket"
3. Fill in:
   - Subject: "Test Ticket 1"
   - Description: "Testing automatic assignment"
   - Status: Open (or leave as default)
4. Save the ticket
5. Check the "Assigned To" field - should show Kenneth
6. Create another ticket - should be assigned to Karen
7. Third ticket - back to Kenneth

### Method 2: Via Console
```python
# In bench console
ticket = frappe.get_doc({
    'doctype': 'HD Ticket',
    'subject': 'Test Assignment',
    'raised_by': 'Administrator'
})
ticket.insert(ignore_permissions=True)
frappe.db.commit()

# Wait a moment, then check
ticket.reload()
print("Assigned to:", ticket._assign)
```

### Method 3: Via API
```bash
curl -X POST https://support.tiberbu.app/api/resource/HD Ticket \
  -H "Authorization: token YOUR_API_KEY:YOUR_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "description": "Testing assignment",
    "raised_by": "test@example.com"
  }'
```

## Verifying Assignment

Check who a ticket is assigned to:
```sql
SELECT 
    t.name,
    t.subject,
    t.status,
    t._assign as assigned_to
FROM `tabHD Ticket` t
ORDER BY t.creation DESC
LIMIT 10;
```

Check the assignment rule state:
```sql
SELECT 
    name,
    rule,
    disabled,
    last_user,
    priority
FROM `tabAssignment Rule`
WHERE name = 'Auto-Assign All Tickets';
```

## Adding More Agents Later

To add more agents to the round-robin:

```python
# Get the assignment rule
rule = frappe.get_doc('Assignment Rule', 'Auto-Assign All Tickets')

# Add new agent
rule.append('users', {'user': 'newagent@tiberbu.com'})

# Save
rule.save(ignore_permissions=True)
frappe.db.commit()
```

The assignment will now rotate among Kenneth → Karen → New Agent → Kenneth...

## Troubleshooting

### Tickets Not Being Assigned

1. **Check rule is enabled:**
   ```python
   rule = frappe.get_doc('Assignment Rule', 'Auto-Assign All Tickets')
   print("Disabled:", rule.disabled)  # Should be 0
   ```

2. **Check ticket status matches condition:**
   - Assignment only triggers when `status == 'Open'`
   - Check ticket: `ticket.status` should be 'Open'

3. **Check agents exist:**
   ```python
   for user in ['keneth@tiberbu.com', 'kagai@tiberbu.com']:
       exists = frappe.db.exists('HD Agent', user)
       print(f"{user}: {exists}")
   ```

4. **Check assignment rule users:**
   ```python
   rule = frappe.get_doc('Assignment Rule', 'Auto-Assign All Tickets')
   print("Users in rule:")
   for u in rule.users:
       print(f"  - {u.user}")
   ```

### Assignment Stuck on One Person

Reset the round-robin counter:
```python
rule = frappe.get_doc('Assignment Rule', 'Auto-Assign All Tickets')
rule.last_user = None
rule.save(ignore_permissions=True)
frappe.db.commit()
```

## Files Created

1. `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/fixtures/setup_auto_assignment.py`
   - Setup script for creating users and assignment rule
   - Run with: `bench --site erp.local execute "helpdesk.fixtures.setup_auto_assignment.setup"`

2. `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/fixtures/test_assignment.py`
   - Test script for verifying assignments
   - Creates multiple test tickets and shows assignments

3. `/home/ubuntu/frappe-bench/apps/helpdesk/ASSIGNMENT_SETUP.md`
   - This documentation file

## Next Steps

1. Test the assignment by creating tickets via the web interface
2. Monitor the assignment pattern to verify round-robin works
3. Add more agents when needed using the instructions above
4. Optionally: Create team-specific assignment rules for different ticket types
