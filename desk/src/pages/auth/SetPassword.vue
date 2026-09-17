
<template>
  <div class="flex items-center justify-center min-h-screen bg-surface-gray-1">
    <div class="w-full max-w-sm p-8 rounded-lg border border-outline-gray-1 bg-surface-white">
      <div class="text-lg font-semibold text-ink-gray-8 mb-1">
        {{ __("Set a new password") }}
      </div>
      <div class="text-sm text-ink-gray-5 mb-6">
        {{ __("For security, please set your own password before continuing.") }}
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
        <div>
          <label class="text-sm text-ink-gray-6 mb-1 block">{{ __("Current password") }}</label>
          <input
            v-model="oldPassword"
            type="password"
            class="form-control w-full rounded border border-outline-gray-2 px-3 py-2 text-base"
            required
            autocomplete="current-password"
          />
        </div>
        <div>
          <label class="text-sm text-ink-gray-6 mb-1 block">{{ __("New password") }}</label>
          <input
            v-model="newPassword"
            type="password"
            class="form-control w-full rounded border border-outline-gray-2 px-3 py-2 text-base"
            required
            autocomplete="new-password"
          />
        </div>
        <div>
          <label class="text-sm text-ink-gray-6 mb-1 block">{{ __("Confirm new password") }}</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="form-control w-full rounded border border-outline-gray-2 px-3 py-2 text-base"
            required
            autocomplete="new-password"
          />
        </div>

        <div v-if="errorMessage" class="text-sm text-ink-red-3">
          {{ errorMessage }}
        </div>

        <Button
          type="submit"
          variant="solid"
          :loading="submitting"
          :label="__('Set password')"
          class="w-full"
        />
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, call, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import { router } from "@/router";

const authStore = useAuthStore();

const oldPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const submitting = ref(false);
const errorMessage = ref("");

async function onSubmit() {
  errorMessage.value = "";

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = __("New password and confirmation do not match.");
    return;
  }
  if (newPassword.value.length < 8) {
    errorMessage.value = __("Password must be at least 8 characters.");
    return;
  }

  submitting.value = true;
  try {
    await call("frappe.core.doctype.user.user.update_password", {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    });

    // Clear the forced-change flag now that they've set their own password
    await call("helpdesk.api.auth.complete_forced_password_change");

    toast.success(__("Password updated"));

    // Refresh auth store so forcePasswordChange reflects the cleared flag
    await authStore.reloadUser();

    router.replace({ name: "Home" });
  } catch (e: any) {
    errorMessage.value = e?.messages?.[0] || e?.message || __("Something went wrong. Please check your current password and try again.");
  } finally {
    submitting.value = false;
  }
}
</script>
