import dingSound from "@/assets/ding.wav";

export interface NotificationPayload {
  notification_type?: string;
  reference_ticket?: string;
  ticket_subject?: string;
  user_from?: string;
  message?: string;
}

// Sound configs per notification type — louder/different feel for urgent ones
const SOUND_CONFIG: Record<string, { volume: number; playCount: number }> = {
  Assignment:    { volume: 0.7, playCount: 1 },
  Mention:       { volume: 0.6, playCount: 1 },
  Reaction:      { volume: 0.4, playCount: 1 },
  Escalation:    { volume: 0.8, playCount: 2 },
  "SLA Warning": { volume: 0.8, playCount: 2 },
  "SLA Breach":  { volume: 1.0, playCount: 3 },
  // legacy socket-only event names (kept for backward compat)
  sla_warning:   { volume: 0.8, playCount: 2 },
  sla_breached:  { volume: 1.0, playCount: 3 },
  escalation:    { volume: 0.8, playCount: 2 },
};

let audio: HTMLAudioElement | null = null;

function getAudio(): HTMLAudioElement {
  if (!audio) {
    audio = new Audio(dingSound);
  }
  return audio;
}

function playDing(volume = 0.7, times = 1, delayMs = 350) {
  const a = getAudio();
  let count = 0;

  const play = () => {
    try {
      a.volume = volume;
      a.currentTime = 0;
      a.play().catch(() => {});
      count++;
      if (count < times) {
        setTimeout(play, delayMs);
      }
    } catch {
      // Ignore
    }
  };

  play();
}

function showBrowserNotification(
  title: string,
  body: string,
  ticketId?: string,
  tag?: string
) {
  if (!("Notification" in window)) return;

  const show = () => {
    const n = new Notification(title, {
      body,
      icon: "/assets/helpdesk/desk/favicon.svg",
      tag: tag || (ticketId ? `ticket-${ticketId}` : "helpdesk-notification"),
    });
    if (ticketId) {
      n.onclick = () => {
        window.focus();
        window.location.href = `/helpdesk/tickets/${ticketId}`;
      };
    }
  };

  if (Notification.permission === "granted") {
    show();
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then((p) => { if (p === "granted") show(); });
  }
}

// ── Per-event handlers ────────────────────────────────────────────────────────

export function handleIncomingNotification(payload: NotificationPayload) {
  const type = payload.notification_type;
  if (!type) return;

  const config = SOUND_CONFIG[type];
  if (!config) return;

  playDing(config.volume, config.playCount);

  const ticketId = payload.reference_ticket;
  const subject  = payload.ticket_subject || "";
  const from     = payload.user_from || "";

  const titles: Record<string, string> = {
    Assignment:    "Ticket Assigned to You",
    Mention:       "You Were Mentioned",
    Reaction:      "Reaction on Your Comment",
    Escalation:    "Ticket Escalated",
    "SLA Warning": "SLA Warning",
    "SLA Breach":  "SLA Breached",
  };

  const bodies: Record<string, string> = {
    Assignment:    subject ? `${from ? from + ": " : ""}${subject}` : "You have been assigned a new ticket",
    Mention:       subject ? `${from} mentioned you on: ${subject}` : `${from} mentioned you`,
    Reaction:      `${from} reacted to your comment${subject ? " on: " + subject : ""}`,
    Escalation:    payload.message || (subject ? `Ticket escalated: ${subject}` : `Ticket #${ticketId} escalated`),
    "SLA Warning": payload.message || (subject ? `SLA warning: ${subject}` : `SLA warning on ticket #${ticketId}`),
    "SLA Breach":  payload.message || (subject ? `SLA breached: ${subject}` : `SLA breached on ticket #${ticketId}`),
  };

  showBrowserNotification(
    titles[type] || "New Notification",
    bodies[type] || "",
    ticketId,
    `hd-${type}-${ticketId}`
  );
}

export function handleSlaWarning(data: {
  ticket: string;
  subject?: string;
  minutes_remaining: number;
  is_manager_notification?: boolean;
}) {
  const config = SOUND_CONFIG.sla_warning;
  playDing(config.volume, config.playCount);

  const minsLeft = Math.round(data.minutes_remaining);
  const title = data.is_manager_notification ? "SLA Alert (Manager)" : "SLA Warning";
  const body  = `Ticket #${data.ticket} — ${minsLeft} min until breach${data.subject ? ": " + data.subject : ""}`;

  showBrowserNotification(title, body, data.ticket, `sla-warn-${data.ticket}`);
}

export function handleSlaBreached(data: { ticket: string; subject?: string }) {
  const config = SOUND_CONFIG.sla_breached;
  playDing(config.volume, config.playCount);

  showBrowserNotification(
    "SLA Breached",
    `Ticket #${data.ticket} has exceeded its SLA${data.subject ? ": " + data.subject : ""}`,
    data.ticket,
    `sla-breach-${data.ticket}`
  );
}

export function handleEscalationNotification(data: {
  ticket: string;
  team?: string;
  message?: string;
}) {
  const config = SOUND_CONFIG.escalation;
  playDing(config.volume, config.playCount);

  showBrowserNotification(
    "Ticket Escalated to Your Team",
    data.message || `Ticket #${data.ticket} has been escalated to your team`,
    data.ticket,
    `escalation-${data.ticket}`
  );
}

export function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
}
