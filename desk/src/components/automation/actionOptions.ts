export const ACTION_OPTIONS = [
  { value: "assign_to_agent", label: "Assign to Agent", valueType: "text" },
  { value: "assign_to_team", label: "Assign to Team", valueType: "text" },
  { value: "set_priority", label: "Set Priority", valueType: "priority" },
  { value: "set_status", label: "Set Status", valueType: "status" },
  { value: "set_category", label: "Set Category", valueType: "text" },
  { value: "add_tag", label: "Add Tag", valueType: "text" },
  { value: "send_email", label: "Send Email (to)", valueType: "text" },
  { value: "send_notification", label: "Send In-App Notification", valueType: "text" },
  { value: "add_internal_note", label: "Add Internal Note", valueType: "textarea" },
  { value: "trigger_webhook", label: "Trigger Webhook", valueType: "url" },
]

export const PRIORITY_OPTIONS = [
  { label: "Low", value: "Low" },
  { label: "Medium", value: "Medium" },
  { label: "High", value: "High" },
  { label: "Urgent", value: "Urgent" },
]

export const STATUS_OPTIONS = [
  { label: "Open", value: "Open" },
  { label: "Replied", value: "Replied" },
  { label: "Resolved", value: "Resolved" },
  { label: "Closed", value: "Closed" },
]
