# Role-Based Routing & Access Control

## Overview
This system implements role-based routing to prevent customers from accessing agent interfaces and to provide a clear separation between customer portal and agent workspace.

## Roles

### 1. **Helpdesk Customer**
- **Purpose**: End users who submit and track tickets
- **Access**: Customer portal only
- **Routes**:
  - `/helpdesk/my-tickets` - View their own tickets
  - `/helpdesk/my-tickets/new` - Create new tickets
  - `/helpdesk/kb-public` - Browse knowledge base
- **Blocked from**:
  - `/helpdesk/home` - Agent dashboard
  - `/helpdesk/tickets` - All tickets view (agent)
  - `/desk` - Backend/admin interface

### 2. **Agent**
- **Purpose**: Support staff who handle tickets
- **Access**: Full helpdesk interface + customer portal
- **Routes**:
  - `/helpdesk/home` - Agent dashboard
  - `/helpdesk/tickets` - All tickets
  - `/helpdesk/kb` - Knowledge base management
  - `/helpdesk/customers` - Customer management
  - Can also access `/helpdesk/my-tickets` if needed

### 3. **Agent Manager**
- **Purpose**: Team leads and supervisors
- **Access**: Same as Agent + additional management features
- **Routes**: All Agent routes + team management

### 4. **System Manager**
- **Purpose**: System administrators
- **Access**: Everything including `/desk` backend
- **Routes**: All routes available

## Automatic Redirects

### After Login
- **Agents/Agent Managers** → `/helpdesk/home`
- **System Manager** → `/desk`
- **Helpdesk Customers** → `/helpdesk/my-tickets`

### URL Protection
If a customer tries to access an agent-only URL:
- `/helpdesk/home` → Redirects to `/helpdesk/my-tickets`
- `/helpdesk/tickets/TICKET-001` → Redirects to `/helpdesk/my-tickets/TICKET-001`
- `/desk` → Blocked (shows unauthorized)

## Implementation Files

### Backend
- `helpdesk/api/redirect.py` - Redirect logic
- `helpdesk/api/permission.py` - Permission checks
- `helpdesk/api/auth.py` - User role detection
- `helpdesk/overrides/session.py` - Post-login redirect hook
- `helpdesk/hooks.py` - Session hook registration

### Frontend
- `desk/src/router/index.ts` - Vue Router guards
- `desk/src/stores/auth.ts` - Auth state management

## How to Assign Roles

### Creating a Customer User
```python
# Via console
user = frappe.get_doc("User", "customer@example.com")
user.append("roles", {"role": "Helpdesk Customer"})
user.save()
```

### Creating an Agent User
```python
# Create HD Agent first
agent = frappe.new_doc("HD Agent")
agent.user = "agent@example.com"
agent.agent_name = "Agent Name"
agent.is_active = 1
agent.insert()

# User automatically gets Agent role
```

## Testing the Setup

1. **Create a test customer**:
   ```bash
   bench --site support.tiberbu.app console
   ```
   ```python
   user = frappe.new_doc("User")
   user.email = "testcustomer@example.com"
   user.first_name = "Test"
   user.last_name = "Customer"
   user.enabled = 1
   user.send_welcome_email = 0
   user.append("roles", {"role": "Helpdesk Customer"})
   user.insert()
   ```

2. **Login as customer** at https://support.tiberbu.app/login
   - Should redirect to `/helpdesk/my-tickets`
   
3. **Try accessing** https://support.tiberbu.app/helpdesk/home
   - Should automatically redirect back to `/helpdesk/my-tickets`

4. **Login as agent** (keneth@tiberbu.com / kagai@tiberbu.com / austine@tiberbu.com)
   - Should redirect to `/helpdesk/home`
   - Can access all agent features

## URL Structure Summary

```
https://support.tiberbu.app
├── /login                          [All users]
├── /desk                           [System Manager, Agents only]
└── /helpdesk
    ├── /home                       [Agents only] - Agent dashboard
    ├── /tickets                    [Agents only] - All tickets view
    ├── /kb                         [Agents only] - KB management
    ├── /customers                  [Agents only] - Customer list
    ├── /teams                      [Agents only] - Team management
    └── /my-tickets                 [All authenticated users] - Customer portal
        ├── /                       List of user's tickets
        ├── /new                    Create new ticket
        └── /:ticketId              View specific ticket
```

## Customization

To add more customer-facing pages, edit `/home/ubuntu/frappe-bench/apps/helpdesk/desk/src/router/index.ts` and add `meta: { public: true, auth: true }` to the route.

Example:
```typescript
{
  path: "/my-profile",
  name: "CustomerProfile",
  component: () => import("@/pages/CustomerProfile.vue"),
  meta: {
    public: true,  // Accessible to customers
    auth: true,    // Requires login
  },
},
```
