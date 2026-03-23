export const TRIGGER_OPTIONS = [
  {
    value: "ticket_created",
    label: "Ticket Created",
    description: "Fires when a new ticket is submitted",
  },
  {
    value: "ticket_updated",
    label: "Ticket Updated",
    description: "Fires on every save of an existing ticket",
  },
  {
    value: "ticket_assigned",
    label: "Ticket Assigned",
    description: "Fires when a ticket is assigned to an agent",
  },
  {
    value: "ticket_resolved",
    label: "Ticket Resolved",
    description: "Fires when ticket status changes to Resolved or Closed",
  },
  {
    value: "ticket_reopened",
    label: "Ticket Reopened",
    description: "Fires when a resolved ticket is reopened",
  },
  {
    value: "sla_warning",
    label: "SLA Warning",
    description: "Fires when a ticket approaches its SLA breach threshold",
  },
  {
    value: "sla_breached",
    label: "SLA Breached",
    description: "Fires when a ticket exceeds its SLA resolution time",
  },
  {
    value: "csat_received",
    label: "CSAT Response Received",
    description: "Fires when a customer submits a satisfaction rating",
  },
  {
    value: "chat_started",
    label: "Chat Started",
    description: "Fires when a new live chat session begins",
  },
  {
    value: "chat_ended",
    label: "Chat Ended",
    description: "Fires when a live chat session ends",
  },
]
