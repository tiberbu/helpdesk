import { useAuthStore } from "@/stores/auth";
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
    },
    { immediate: true }
  );
  $socket.on("helpdesk:comment-reaction-update", () => {
    if (isCustomerPortal.value) return;
    resource.reload();
  });

  // Reload notification list when a new @mention notification is delivered
  // to this user via real-time, so the bell badge updates immediately.
  $socket.on("helpdesk:new-notification", () => {
    if (isCustomerPortal.value) return;
    resource.reload();
  });

  // SLA warning notifications delivered via frappe.publish_realtime(user=...).
  // Show a toast so the agent is alerted immediately even if the notification
  // panel is not open.  The message payload matches notify_agent_sla_warning().
  $socket.on(
    "sla_warning",
    (data: {
      ticket: string;
      subject: string;
      threshold_minutes: number;
      minutes_remaining: number;
      sla_deadline: string;
    }) => {
      if (isCustomerPortal.value) return;
      const minsLeft = Math.round(data.minutes_remaining);
      toast.create({
        message: `SLA Warning: Ticket #${data.ticket} — ${minsLeft} min until breach`,
      });
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
