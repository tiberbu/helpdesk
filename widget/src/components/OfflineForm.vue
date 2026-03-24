<script setup>
/**
 * OfflineForm.vue — Shown when no agents are available (AC #4).
 *
 * Collects Name, Email, Subject, and Message then calls create_offline_ticket.
 * On success shows a confirmation message with the customer's email.
 */
import { ref } from 'vue'

const props = defineProps({
  brand: { type: String, default: 'default' },
  siteUrl: { type: String, default: '' },
})

// ── Form state ─────────────────────────────────────────────────────────────
const name = ref('')
const email = ref('')
const subject = ref('')
const message = ref('')
const errors = ref({})
const isLoading = ref(false)
const errorBanner = ref('')
const submitted = ref(false)
const submittedEmail = ref('')

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
  if (!message.value.trim()) e.message = 'Message is required.'
  errors.value = e
  return Object.keys(e).length === 0
}

// ── Submit ─────────────────────────────────────────────────────────────────
async function handleSubmit() {
  errorBanner.value = ''
  if (!validate()) return

  isLoading.value = true
  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.create_offline_ticket`
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'omit',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        name: name.value.trim(),
        email: email.value.trim(),
        subject: subject.value.trim(),
        message: message.value.trim(),
        brand: props.brand,
      }),
    })

    const data = await res.json()
    const payload = data.message !== undefined ? data.message : data

    if (!res.ok || payload.exc) {
      throw new Error(payload.exc_type || 'Server error')
    }

    submittedEmail.value = email.value.trim()
    submitted.value = true
  } catch {
    errorBanner.value = 'Could not send your message. Please try again.'
  } finally {
    isLoading.value = false
  }
}

function dismissError() {
  errorBanner.value = ''
}
</script>

<template>
  <!-- Confirmation state (AC #4) -->
  <div v-if="submitted" class="hd-body">
    <div class="hd-confirm">
      <div class="hd-confirm__icon">✅</div>
      <p class="hd-confirm__title">Message sent!</p>
      <p class="hd-confirm__text">
        Thanks! We'll get back to you at <strong>{{ submittedEmail }}</strong> as soon as possible.
      </p>
    </div>
  </div>

  <!-- Leave-a-message form (AC #4) -->
  <div v-else class="hd-body">
    <p class="hd-form__title">Leave a message</p>
    <p style="font-size:12px;color:var(--hd-text-muted);margin-bottom:14px;">
      Our team is currently offline. Send us a message and we'll reply by email.
    </p>

    <!-- Error banner -->
    <div v-if="errorBanner" class="hd-alert hd-alert--error">
      <span>{{ errorBanner }}</span>
      <button class="hd-alert__dismiss" @click="dismissError" aria-label="Dismiss">×</button>
    </div>

    <form @submit.prevent="handleSubmit" novalidate>
      <!-- Name -->
      <div class="hd-form__group">
        <label class="hd-form__label" for="hd-off-name">Name</label>
        <input
          id="hd-off-name"
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
        <label class="hd-form__label" for="hd-off-email">Email</label>
        <input
          id="hd-off-email"
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
        <label class="hd-form__label" for="hd-off-subject">Subject</label>
        <input
          id="hd-off-subject"
          v-model="subject"
          class="hd-form__input"
          :class="{ 'hd-form__input--error': errors.subject }"
          type="text"
          placeholder="What's your question?"
        />
        <p v-if="errors.subject" class="hd-form__error">{{ errors.subject }}</p>
      </div>

      <!-- Message -->
      <div class="hd-form__group">
        <label class="hd-form__label" for="hd-off-message">Message</label>
        <textarea
          id="hd-off-message"
          v-model="message"
          class="hd-form__textarea"
          :class="{ 'hd-form__textarea--error': errors.message }"
          placeholder="Describe your issue…"
          rows="4"
        ></textarea>
        <p v-if="errors.message" class="hd-form__error">{{ errors.message }}</p>
      </div>

      <button type="submit" class="hd-btn hd-btn--primary" :disabled="isLoading">
        <span v-if="isLoading" class="hd-spinner" role="status" aria-label="Loading"></span>
        <span>{{ isLoading ? 'Sending…' : 'Send message' }}</span>
      </button>
    </form>
  </div>
</template>
