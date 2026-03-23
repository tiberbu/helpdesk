/**
 * PreChatForm.vue integration tests.
 *
 * Tests:
 *  1. Renders name / email / subject fields
 *  2. Validates required fields on submit
 *  3. Validates email format
 *  4. Shows loading spinner during submission
 *  5. Emits 'session-created' with { session_id, token } on success
 *  6. Shows error banner on API failure
 *  7. Dismissing error banner clears it
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import PreChatForm from '../components/PreChatForm.vue'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('PreChatForm.vue', () => {
  // ── 1. Renders all three form fields ────────────────────────────────────
  it('renders name, email, and subject inputs', () => {
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    expect(wrapper.find('#hd-name').exists()).toBe(true)
    expect(wrapper.find('#hd-email').exists()).toBe(true)
    expect(wrapper.find('#hd-subject').exists()).toBe(true)
  })

  // ── 2. Shows validation errors on empty submit ──────────────────────────
  it('shows validation errors when form is submitted empty', async () => {
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('form').trigger('submit')
    const errors = wrapper.findAll('.hd-form__error')
    expect(errors.length).toBeGreaterThanOrEqual(3)
    expect(errors.some(e => e.text().includes('Name'))).toBe(true)
    expect(errors.some(e => e.text().includes('Email'))).toBe(true)
    expect(errors.some(e => e.text().includes('Subject'))).toBe(true)
  })

  // ── 3. Shows email format error ─────────────────────────────────────────
  it('shows email format error for invalid email', async () => {
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-name').setValue('Alice')
    await wrapper.find('#hd-email').setValue('not-an-email')
    await wrapper.find('#hd-subject').setValue('Help')
    await wrapper.find('form').trigger('submit')
    const emailError = wrapper.findAll('.hd-form__error').find(e => e.text().includes('valid email'))
    expect(emailError).toBeTruthy()
  })

  // ── 4. Emits session-created on successful API call ──────────────────────
  it('emits session-created with session_id and token on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: { session_id: 'sess-42', token: 'jwt-abc' } }),
    })
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-name').setValue('Alice')
    await wrapper.find('#hd-email').setValue('alice@example.com')
    await wrapper.find('#hd-subject').setValue('Help needed')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('session-created')).toBeTruthy()
    const [payload] = wrapper.emitted('session-created')[0]
    expect(payload.session_id).toBe('sess-42')
    expect(payload.token).toBe('jwt-abc')
  })

  // ── 5. Shows loading spinner during API call ─────────────────────────────
  it('shows loading state during API call', async () => {
    let resolveP
    global.fetch = vi.fn().mockReturnValue(new Promise(r => { resolveP = r }))
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-name').setValue('Bob')
    await wrapper.find('#hd-email').setValue('bob@example.com')
    await wrapper.find('#hd-subject').setValue('Test')
    await wrapper.find('form').trigger('submit')
    // Spinner should appear before fetch resolves
    expect(wrapper.find('.hd-spinner').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    // Resolve
    resolveP({ ok: true, json: async () => ({ message: { session_id: 'x', token: 'y' } }) })
    await flushPromises()
    expect(wrapper.find('.hd-spinner').exists()).toBe(false)
  })

  // ── 6. Shows error banner on API failure ────────────────────────────────
  it('shows error banner when API call fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network error'))
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-name').setValue('Carol')
    await wrapper.find('#hd-email').setValue('carol@example.com')
    await wrapper.find('#hd-subject').setValue('Issue')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const banner = wrapper.find('.hd-alert--error')
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('Could not start chat')
  })

  // ── 7. Dismissing error banner clears it ────────────────────────────────
  it('dismisses error banner when × button clicked', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('fail'))
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-name').setValue('Dave')
    await wrapper.find('#hd-email').setValue('dave@example.com')
    await wrapper.find('#hd-subject').setValue('Issue')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await wrapper.find('.hd-alert__dismiss').trigger('click')
    expect(wrapper.find('.hd-alert--error').exists()).toBe(false)
  })

  // ── 8. Does not call API if validation fails ─────────────────────────────
  it('does not call fetch when validation fails', async () => {
    global.fetch = vi.fn()
    const wrapper = mount(PreChatForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('form').trigger('submit')
    expect(global.fetch).not.toHaveBeenCalled()
  })
})
