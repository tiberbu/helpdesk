# Story: [County-3] Hierarchical visibility and permission scoping

Status: in-progress
Task ID: mnga2c41qzw0rp
Task Number: #339
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T16:46:07.827Z

## Description

## Story 3 of 7 — depends on Story 1

### Problem
Agents must only see tickets within their support scope:
- L0 agent: only tickets assigned to their sub-county team
- L1 agent: tickets from all sub-county teams under their county + their own L1 tickets
- L2 National: all tickets nationwide
- L3 Engineering: only tickets explicitly escalated to engineering

### Implementation

#### Option A: Custom get_list Permission Query (Recommended)
Override HD Ticket permission_query_conditions to filter based on user team hierarchy:

```python
def get_permission_query_conditions(user):
    user_teams = get_user_teams(user)
    if is_national_level(user_teams):
        return ""  # No filter — see all
    
    # Get all teams in scope (own team + all child teams)
    scoped_teams = []
    for team in user_teams:
        scoped_teams.append(team)
        scoped_teams.extend(get_descendant_teams(team))
    
    team_list = ", ".join([frappe.db.escape(t) for t in scoped_teams])
    return f"`tabHD Ticket`.`_assign` REGEXP {team_list_regex}"
```

#### Helper Functions Needed
- `get_user_teams(user)` — returns HD Team names where user is a member
- `get_descendant_teams(team)` — recursively gets all child teams using parent_team
- `is_national_level(teams)` — checks if any team has support_level.level_order >= 2

### Testing
- Create L0 agent → verify they only see sub-county tickets
- Create L1 agent → verify they see county-wide tickets
- Create L2 agent → verify they see everything
- Verify ticket list API respects these filters
- Verify dashboard counts respect these filters

## Done Criteria
- Permission scoping works per support level
- L0 sees only their sub-county
- L1 sees their county (all child L0 teams)
- L2 sees all
- L3 sees only engineering-escalated tickets
- bench build passes
- Tested with different user accounts

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] #### Option A: Custom get_list Permission Query (Recommended)
- [ ] Override HD Ticket permission_query_conditions to filter based on user team hierarchy:
- [ ] ```python
- [ ] def get_permission_query_conditions(user):
- [ ] user_teams = get_user_teams(user)
- [ ] if is_national_level(user_teams):
- [ ] return ""  # No filter — see all
- [ ] # Get all teams in scope (own team + all child teams)
- [ ] scoped_teams = []
- [ ] for team in user_teams:
- [ ] scoped_teams.append(team)
- [ ] scoped_teams.extend(get_descendant_teams(team))
- [ ] team_list = ", ".join([frappe.db.escape(t) for t in scoped_teams])
- [ ] return f"`tabHD Ticket`.`_assign` REGEXP {team_list_regex}"
- [ ] ```

## Dev Notes

[epic:county-support] [after:County-1]

### References

- Task source: Claude Code Studio task #339

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
