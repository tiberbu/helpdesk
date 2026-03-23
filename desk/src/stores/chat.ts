import { useAuthStore } from "@/stores/auth";
import { createResource, toast } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { globalStore } from "./globalStore";

export interface ChatSession {
  session_id: string;
  customer_email: string;
  customer_name: string;
  status: "waiting" | "active" | "ended";
  started_at: string;
  accepted_at?: string;
  agent?: string;
  ticket?: string;
  unread_count: number;
  message_count: number;
}

export interface ChatMessage {
  message_id: string;
  sender_type: "customer" | "agent" | "system";
  sender_email?: string;
  content: string;
  sent_at: string;
  is_read: boolean;
}

export const useChatStore = defineStore("chat", () => {
  const authStore = useAuthStore();
  const { $socket } = globalStore();

  // Agent availability
  const availability = ref<"Online" | "Away" | "Offline">("Online");

  // Chat sessions: waiting queue + active
  const sessions = ref<ChatSession[]>([]);
  const activeSessions = computed(() =>
    sessions.value.filter((s) => s.status === "active")
  );
  const waitingSessions = computed(() =>
    sessions.value.filter((s) => s.status === "waiting")
  );

  // Currently focused session
  const currentSessionId = ref<string | null>(null);
  const currentSession = computed(() =>
    sessions.value.find((s) => s.session_id === currentSessionId.value) ?? null
  );

  // Messages keyed by session_id
  const messagesBySession = ref<Record<string, ChatMessage[]>>({});
  const currentMessages = computed(() =>
    currentSessionId.value
      ? messagesBySession.value[currentSessionId.value] ?? []
      : []
  );

  // Typing indicator keyed by session_id
  const typingBySessions = ref<Record<string, boolean>>({});

  // Total unread count across all sessions
  const totalUnread = computed(() =>
    sessions.value.reduce((sum, s) => sum + (s.unread_count || 0), 0)
  );

  // -- Resources --

  const fetchSessionsResource = createResource({
    url: "helpdesk.api.chat.get_agent_sessions",
    auto: false,
    onSuccess(data: ChatSession[]) {
      // Preserve existing message counts if already loaded
      sessions.value = data;
    },
  });

  const acceptResource = createResource({
    url: "helpdesk.api.chat.accept_session",
    auto: false,
    onSuccess(data: { session_id: string; status: string; agent: string }) {
      const idx = sessions.value.findIndex(
        (s) => s.session_id === data.session_id
      );
      if (idx !== -1) {
        sessions.value[idx].status = "active";
      }
      currentSessionId.value = data.session_id;
    },
    onError(err: { message?: string }) {
      toast.create({ message: err?.message ?? "Failed to accept session." });
    },
  });

  const setAvailabilityResource = createResource({
    url: "helpdesk.api.chat.set_availability",
    auto: false,
    onSuccess(data: { availability: string }) {
      availability.value = data.availability as "Online" | "Away" | "Offline";
    },
  });

  const transferResource = createResource({
    url: "helpdesk.api.chat.transfer_session",
    auto: false,
    onSuccess(data: { session_id: string; agent: string }) {
      // Remove session from our active list after transfer
      sessions.value = sessions.value.filter(
        (s) => s.session_id !== data.session_id
      );
      if (currentSessionId.value === data.session_id) {
        currentSessionId.value =
          activeSessions.value[0]?.session_id ?? null;
      }
    },
    onError(err: { message?: string }) {
      toast.create({ message: err?.message ?? "Transfer failed." });
    },
  });

  const endSessionResource = createResource({
    url: "helpdesk.api.chat.end_session",
    auto: false,
    onSuccess(data: { session_id: string }) {
      sessions.value = sessions.value.filter(
        (s) => s.session_id !== data.session_id
      );
      if (currentSessionId.value === data.session_id) {
        currentSessionId.value =
          activeSessions.value[0]?.session_id ?? null;
      }
    },
  });

  // -- Actions --

  function init() {
    if (!authStore.isAgent) return;
    fetchSessions();
    _bindSocketEvents();
    _requestNotificationPermission();
  }

  function fetchSessions() {
    fetchSessionsResource.fetch();
  }

  function selectSession(sessionId: string) {
    currentSessionId.value = sessionId;
    // Clear unread for this session
    const s = sessions.value.find((x) => x.session_id === sessionId);
    if (s) s.unread_count = 0;
  }

  function acceptSession(sessionId: string) {
    acceptResource.submit({ session_id: sessionId });
  }

  function setAvailability(value: "Online" | "Away" | "Offline") {
    setAvailabilityResource.submit({ availability: value });
  }

  function transferSession(sessionId: string, targetAgentEmail: string) {
    transferResource.submit({
      session_id: sessionId,
      target_agent_email: targetAgentEmail,
    });
  }

  function endSession(sessionId: string) {
    endSessionResource.submit({ session_id: sessionId, token: "" });
  }

  function addMessage(sessionId: string, message: ChatMessage) {
    if (!messagesBySession.value[sessionId]) {
      messagesBySession.value[sessionId] = [];
    }
    messagesBySession.value[sessionId].push(message);
  }

  // -- Socket events --

  function _bindSocketEvents() {
    // New chat arrived in the queue
    $socket.on(
      "chat_queue_new",
      (data: Omit<ChatSession, "unread_count" | "message_count">) => {
        const exists = sessions.value.find(
          (s) => s.session_id === data.session_id
        );
        if (!exists) {
          sessions.value.push({
            ...data,
            unread_count: 0,
            message_count: 0,
          });
          _showDesktopNotification(
            "New chat request",
            `${data.customer_name || data.customer_email} wants to chat`
          );
        }
      }
    );

    // Chat assigned to this agent from a transfer
    $socket.on("chat_assigned", (data: { session_id: string }) => {
      fetchSessions();
      _showDesktopNotification(
        "Chat assigned",
        `Session ${data.session_id} was transferred to you`
      );
    });

    // Incoming message for one of our sessions
    $socket.on(
      "chat_message",
      (data: {
        session_id: string;
        message_id: string;
        content: string;
        sender_type: string;
        sent_at: string;
      }) => {
        if (data.sender_type === "customer") {
          addMessage(data.session_id, {
            message_id: data.message_id,
            sender_type: "customer",
            content: data.content,
            sent_at: data.sent_at,
            is_read: false,
          });

          // Increment unread if not the focused session
          if (currentSessionId.value !== data.session_id) {
            const s = sessions.value.find(
              (x) => x.session_id === data.session_id
            );
            if (s) s.unread_count = (s.unread_count || 0) + 1;
          }
        }
      }
    );

    // Session ended remotely (e.g. customer closed)
    $socket.on("session_ended", (data: { session_id: string }) => {
      const s = sessions.value.find((x) => x.session_id === data.session_id);
      if (s) s.status = "ended";
    });

    // Typing indicators
    $socket.on(
      "typing_start",
      (data: { session_id: string; sender_type: string }) => {
        if (data.sender_type === "customer") {
          typingBySessions.value[data.session_id] = true;
        }
      }
    );
    $socket.on("typing_stop", (data: { session_id: string }) => {
      typingBySessions.value[data.session_id] = false;
    });

    // Availability change from another tab/device
    $socket.on(
      "availability_changed",
      (data: { availability: string }) => {
        availability.value = data.availability as
          | "Online"
          | "Away"
          | "Offline";
      }
    );
  }

  function _requestNotificationPermission() {
    if (
      typeof Notification !== "undefined" &&
      Notification.permission === "default"
    ) {
      Notification.requestPermission();
    }
  }

  function _showDesktopNotification(title: string, body: string) {
    if (
      typeof Notification !== "undefined" &&
      Notification.permission === "granted"
    ) {
      new Notification(title, { body, icon: "/assets/helpdesk/manifest/128.png" });
    }
  }

  return {
    availability,
    sessions,
    activeSessions,
    waitingSessions,
    currentSessionId,
    currentSession,
    messagesBySession,
    currentMessages,
    typingBySessions,
    totalUnread,
    init,
    fetchSessions,
    selectSession,
    acceptSession,
    setAvailability,
    transferSession,
    endSession,
    addMessage,
  };
});
