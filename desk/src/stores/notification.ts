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

  // Agent bell: uses createListResource directly on the doctype (agents have permission)
  const agentResource: ListResource<Notification> = createListResource({
    doctype: "HD Notification",
    cache: "AgentNotifications",
    fields: [
      "creation", "message", "name", "notification_type",
      "read", "reference_comment", "reference_ticket", "user_from", "user_to",
    ],
    orderBy: "modified desc",
  });

  // Customer bell: uses a whitelisted API that bypasses doctype permissions
  const customerResource = createResource({
    url: "helpdesk.helpdesk.doctype.hd_notification.utils.get_customer_notifications",
    auto: false,
  });

  const customerClear = createResource({
    url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear_customer_notifications",
    auto: false,
    onSuccess: () => customerResource.fetch(),
  });

  const agentClear = createResource({
    url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
    auto: false,
    onSuccess: () => agentResource.reload(),
  });

  // Unified clear — object with .submit() that calls the right backend
  const clear = {
    get loading() {
      return isCustomerPortal.value ? customerClear.loading : agentClear.loading;
    },
    submit() {
      if (isCustomerPortal.value) {
        customerClear.submit();
      } else {
        agentClear.submit();
      }
    },
  };

  const read = (ticket: string) => {
    if (isCustomerPortal.value) {
      createResource({
        url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear_customer_notifications",
        auto: true,
        params: { ticket },
        onSuccess: () => customerResource.fetch(),
      });
    } else {
      createResource({
        url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
        auto: true,
        params: { ticket },
        onSuccess: () => agentResource.reload(),
      });
    }
  };

  const data = computed<Notification[]>(() => {
    if (isCustomerPortal.value) {
      return (customerResource.data as Notification[]) || [];
    }
    return agentResource.data || [];
  });

  const unread = computed(() => data.value.filter((d) => !d.read).length);

  function toggle() {
    visible.value = !visible.value;
  }

  function reloadCurrent() {
    if (isCustomerPortal.value) {
      customerResource.fetch();
    } else {
      agentResource.reload();
    }
  }

  watch(
    () => authStore.userId,
    (newVal) => {
      if (!newVal) return;
      if (isCustomerPortal.value) {
        customerResource.fetch();
      } else {
        agentResource.filters = { user_to: ["=", authStore.userId] };
        agentResource.reload();
        requestNotificationPermission();
      }
    },
    { immediate: true }
  );

  $socket.on("helpdesk:comment-reaction-update", () => {
    if (isCustomerPortal.value) return;
    agentResource.reload();
  });

  $socket.on("helpdesk:new-notification", (payload: {
    notification_type?: string;
    reference_ticket?: string;
    ticket_subject?: string;
    user_from?: string;
  } = {}) => {
    reloadCurrent();
    if (!isCustomerPortal.value) {
      handleIncomingNotification(payload);
    }
  });

  $socket.on("sla_warning", (data: {
    ticket: string; subject: string; threshold_minutes: number;
    minutes_remaining: number; sla_deadline: string; is_manager_notification?: boolean;
  }) => {
    if (isCustomerPortal.value) return;
    const minsLeft = Math.round(data.minutes_remaining);
    const prefix = data.is_manager_notification ? "SLA Alert (Manager)" : "SLA Warning";
    toast.create({ message: `${prefix}: Ticket #${data.ticket} — ${minsLeft} min until breach` });
    handleSlaWarning(data);
    agentResource.reload();
  });

  $socket.on("sla_breached", (data: { ticket: string; subject: string }) => {
    if (isCustomerPortal.value) return;
    toast.create({ message: `SLA Breached: Ticket #${data.ticket} has exceeded its SLA` });
    handleSlaBreached(data);
    agentResource.reload();
  });

  $socket.on("escalation_notification", (data: {
    ticket: string; team?: string; message?: string; url?: string;
  }) => {
    if (isCustomerPortal.value) return;
    toast.create({ message: data.message || `Ticket #${data.ticket} escalated to your team` });
    handleEscalationNotification(data);
    agentResource.reload();
  });

  return {
    clear,
    data,
    toggle,
    read,
    unread,
    visible,
    resource: agentResource,
  };
});
