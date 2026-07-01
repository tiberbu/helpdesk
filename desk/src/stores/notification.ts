import { useAuthStore } from "@/stores/auth";
import {
  handleIncomingNotification,
  handleSlaWarning,
  handleSlaBreached,
  handleEscalationNotification,
  requestNotificationPermission,
} from "@/composables/useAssignmentNotification";
import { ListResource, Notification } from "@/types";
import { isCustomerPortal } from "@/utils";
import { createListResource, createResource, toast } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import { globalStore } from "./globalStore";

export const useNotificationStore = defineStore("notification", () => {
  const authStore = useAuthStore();
  const { $socket } = globalStore();

  const visible = ref(false);
  const resource: ListResource<Notification> = createListResource({
    doctype: "HD Notification",
    cache: "Notifications",
    fields: [
      "creation",
      "message",
      "name",
      "notification_type",
      "read",
      "reference_comment",
      "reference_ticket",
      "user_from",
      "user_to",
    ],
    orderBy: "modified desc",
  });
  const clear = createResource({
    url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
    auto: false,
    onSuccess: () => resource.reload(),
  });

  const read = (ticket: string) => {
    createResource({
      url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
      auto: true,
      params: {
        ticket,
      },
      onSuccess: () => resource.reload(),
    });
  };

  const data = computed(() => resource.data || []);
  const unread = computed(() => data.value.filter((d) => !d.read).length);

  function toggle() {
    visible.value = !visible.value;
  }

  watch(
    () => authStore.hasDeskAccess,
    (newVal) => {
      if (!newVal) return;
      resource.filters = {
        user_to: ["=", authStore.userId],
      };
      resource.reload();
      // Request browser notification permission when agent logs in
      requestNotificationPermission();
    },
    { immediate: true }
  );
  $socket.on("helpdesk:comment-reaction-update", () => {
    if (isCustomerPortal.value) return;
    resource.reload();
  });

  // Reload notification list and play sound/show browser notification when
  // an assignment or mention arrives for this agent.
  $socket.on("helpdesk:new-notification", (payload: {
    notification_type?: string;
    reference_ticket?: string;
    ticket_subject?: string;
    user_from?: string;
  } = {}) => {
    if (isCustomerPortal.value) return;
    resource.reload();
    handleIncomingNotification(payload);
  });

  // SLA warning — toast + ding + browser notification
  $socket.on(
    "sla_warning",
    (data: {
      ticket: string;
      subject: string;
      threshold_minutes: number;
      minutes_remaining: number;
      sla_deadline: string;
      is_manager_notification?: boolean;
    }) => {
      if (isCustomerPortal.value) return;
      const minsLeft = Math.round(data.minutes_remaining);
      const prefix = data.is_manager_notification ? "SLA Alert (Manager)" : "SLA Warning";
      toast.create({
        message: `${prefix}: Ticket #${data.ticket} — ${minsLeft} min until breach`,
      });
      handleSlaWarning(data);
      resource.reload();
    }
  );

  // SLA breached — toast + ding x3 + browser notification
  $socket.on(
    "sla_breached",
    (data: { ticket: string; subject: string }) => {
      if (isCustomerPortal.value) return;
      toast.create({
        message: `SLA Breached: Ticket #${data.ticket} has exceeded its SLA`,
      });
      handleSlaBreached(data);
      resource.reload();
    }
  );

  // Escalation — ding x2 + browser notification
  $socket.on(
    "escalation_notification",
    (data: { ticket: string; team?: string; message?: string; url?: string }) => {
      if (isCustomerPortal.value) return;
      toast.create({
        message: data.message || `Ticket #${data.ticket} escalated to your team`,
      });
      handleEscalationNotification(data);
      resource.reload();
    }
  );

  return {
    clear,
    data,
    toggle,
    read,
    unread,
    visible,
    resource,
  };
});
