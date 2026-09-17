import { onMounted, ref } from "vue";
import { toast } from "frappe-ui";

export function useServiceWorkerUpdate() {
  const updateAvailable = ref(false);
  const registration = ref<ServiceWorkerRegistration | null>(null);

  onMounted(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.ready.then((reg) => {
        registration.value = reg;

        // Check for updates every 60 seconds
        setInterval(() => {
          reg.update();
        }, 60000);

        // Listen for waiting service worker
        reg.addEventListener("updatefound", () => {
          const newWorker = reg.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
                updateAvailable.value = true;
                showUpdateToast();
              }
            });
          }
        });
      });

      // Handle controller change (new SW activated)
      let refreshing = false;
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    }
  });

  function showUpdateToast() {
    const toastInstance = toast.create({
      title: "New version available",
      text: "Click to update and get the latest fixes",
      position: "bottom-center",
      timeout: 0, // Don't auto-dismiss
      action: {
        label: "Update Now",
        onClick: () => {
          applyUpdate();
          toastInstance.dismiss();
        },
      },
    });
  }

  function applyUpdate() {
    if (registration.value?.waiting) {
      registration.value.waiting.postMessage({ type: "SKIP_WAITING" });
    }
  }

  return {
    updateAvailable,
    applyUpdate,
  };
}
