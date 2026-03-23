<script setup>
/**
 * PreChatForm.vue — Shown when agents are online (AC #3).
 *
 * Collects Name, Email, and Subject then calls create_session.
 * Emits 'session-created' with { session_id, token } on success.
 */
import { ref } from 'vue'

const props = defineProps({
  brand: { type: String, default: 'default' },
  siteUrl: { type: String, default: '' },
})

const emit = defineEmits(['session-created'])

// ── Form state ─────────────────────────────────────────────────────────────
const name = ref('')
const email = ref('')
const subject = ref('')
const errors = ref({})
const isLoading = ref(false)
const errorBanner = ref('')

// ── Validation ─────────────────────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validate() {
  const e = {}
  if (!name.value.trim()) e.name = 'Name is required.'
  if (!email.value.trim()) {
    e.email = 'Email is required.'
  } else if (!EMAIL_RE.test(email.value.trim())) {
    e.email = 'Please enter a valid email address.'
  }
  if (!subject.value.trim()) e.subject = 'Subject is required.'
  errors.value = e
  return Object.keys(e).length === 0
}

// ── Submit ─────────────────────────────────────────────────────────────────
async function handleSubmit() {
  errorBanner.value = ''
  if (!validate()) return

  isLoading.value = true
  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.create_session`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        name: name.value.trim(),
        subject: subject.value.trim(),
        brand: props.brand,
      }),
    })

    const data = await res.json()
    const payload = data.message !== undefined ? data.message : data

    if (!res.ok || payload.exc) {
      throw new Error(payload.exc_type || 'Server error')
    }

    emit('session-created', {
      session_id: payload.session_id,
      token: payload.token,
    })
  } catch {
    errorBanner.value = 'Could not start chat. Please try again.'
  } finally {
    isLoading.value = false
  }
}

function dismissError() {
  errorBanner.value = ''
}
</script>

<template>
  <div class="hd-body">
    <p class="hd-form__title">Start a conversation</p>

    <!-- Error banner (AC #3) -->
    <div v-if="errorBanner" class="hd-alert hd-alert--error">
      <span>{{ errorBanner }}</span>
      <button class="hd-alert__dismiss" @click="dismissError" aria-label="Dismiss">×</button>
    </div>

    <form @submit.prevent="handleSubmit" novalidate>
      <!-- Name -->
      <div class="hd-form__group">
        <label class="hd-form__label" for="hd-name">Name</label>
        <input
          id="hd-name"
          v-model="name"
          class="hd-form__input"
          :class="{ 'hd-form__input--error': errors.name }"
          type="text"
          placeholder="Your name"
          autocomplete="name"
        />
        <p v-if="errors.name" class="hd-form__error">{{ errors.name }}</p>
      </div>

      <!-- Email -->
      <div class="hd-form__group">
        <label class="hd-form__label" for="hd-email">Email</label>
        <input
          id="hd-email"
          v-model="email"
          class="hd-form__input"
          :class="{ 'hd-form__input--error': errors.email }"
          type="email"
          placeholder="you@example.com"
          autocomplete="email"
        />
        <p v-if="errors.email" class="hd-form__error">{{ errors.email }}</p>
      </div>

      <!-- Subject -->
      <div class="hd-form__group">
        <label class="hd-form__label" for="hd-subject">Subject</label>
        <input
          id="hd-subject"
          v-model="subject"
          class="hd-form__input"
          :class="{ 'hd-form__input--error': errors.subject }"
          type="text"
          placeholder="How can we help?"
        />
        <p v-if="errors.subject" class="hd-form__error">{{ errors.subject }}</p>
      </div>

      <!-- Submit (AC #3 — loading spinner) -->
      <button type="submit" class="hd-btn hd-btn--primary" :disabled="isLoading">
        <span v-if="isLoading" class="hd-spinner" role="status" aria-label="Loading"></span>
        <span>{{ isLoading ? 'Starting chat…' : 'Start chat' }}</span>
      </button>
    </form>
  </div>
</template>
