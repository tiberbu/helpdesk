/**
 * OfflineForm.vue integration tests.
 *
 * Tests:
 *  1. Renders name / email / subject / message fields
 *  2. Shows "Leave a message" title and offline copy
 *  3. Validates all four required fields
 *  4. Submits successfully → shows confirmation with email
 *  5. Shows error banner on API failure
 *  6. Dismisses error banner
 *  7. Does not call fetch when validation fails
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OfflineForm from '../components/OfflineForm.vue'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('OfflineForm.vue', () => {
  // ── 1. Renders all four fields ────────────────────────────────────────────
  it('renders name, email, subject, and message inputs', () => {
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    expect(wrapper.find('#hd-off-name').exists()).toBe(true)
    expect(wrapper.find('#hd-off-email').exists()).toBe(true)
    expect(wrapper.find('#hd-off-subject').exists()).toBe(true)
    expect(wrapper.find('#hd-off-message').exists()).toBe(true)
  })

  // ── 2. Shows correct title ────────────────────────────────────────────────
  it('shows "Leave a message" title', () => {
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    expect(wrapper.find('.hd-form__title').text()).toContain('Leave a message')
  })

  // ── 3. Validates all required fields ─────────────────────────────────────
  it('shows four validation errors on empty submit', async () => {
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('form').trigger('submit')
    const errors = wrapper.findAll('.hd-form__error')
    expect(errors.length).toBe(4)
  })

  // ── 4. Successful submit shows confirmation with email ────────────────────
  it('shows confirmation with submitted email on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: { ticket_id: 'HD-001' } }),
    })
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-off-name').setValue('Eve')
    await wrapper.find('#hd-off-email').setValue('eve@example.com')
    await wrapper.find('#hd-off-subject').setValue('My issue')
    await wrapper.find('#hd-off-message').setValue('Please help!')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    // Confirmation screen
    expect(wrapper.find('.hd-confirm').exists()).toBe(true)
    expect(wrapper.find('.hd-confirm__title').text()).toContain('Message sent')
    expect(wrapper.find('.hd-confirm__text').text()).toContain('eve@example.com')
  })

  // ── 5. Shows error banner on API failure ─────────────────────────────────
  it('shows error banner on API failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network'))
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-off-name').setValue('Frank')
    await wrapper.find('#hd-off-email').setValue('frank@example.com')
    await wrapper.find('#hd-off-subject').setValue('Subject')
    await wrapper.find('#hd-off-message').setValue('Message body')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('.hd-alert--error').exists()).toBe(true)
    expect(wrapper.find('.hd-alert--error').text()).toContain('Could not send')
  })

  // ── 6. Dismisses error banner ─────────────────────────────────────────────
  it('dismisses error banner on × click', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('fail'))
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-off-name').setValue('Grace')
    await wrapper.find('#hd-off-email').setValue('grace@example.com')
    await wrapper.find('#hd-off-subject').setValue('Sub')
    await wrapper.find('#hd-off-message').setValue('Msg')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await wrapper.find('.hd-alert__dismiss').trigger('click')
    expect(wrapper.find('.hd-alert--error').exists()).toBe(false)
  })

  // ── 7. Does not call fetch when validation fails ──────────────────────────
  it('does not call fetch when form is invalid', async () => {
    global.fetch = vi.fn()
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('form').trigger('submit')
    expect(global.fetch).not.toHaveBeenCalled()
  })

  // ── 8. Shows loading state during submit ──────────────────────────────────
  it('disables submit button while submitting', async () => {
    let resolve
    global.fetch = vi.fn().mockReturnValue(new Promise(r => { resolve = r }))
    const wrapper = mount(OfflineForm, { props: { siteUrl: '', brand: 'default' } })
    await wrapper.find('#hd-off-name').setValue('Hank')
    await wrapper.find('#hd-off-email').setValue('hank@example.com')
    await wrapper.find('#hd-off-subject').setValue('Sub')
    await wrapper.find('#hd-off-message').setValue('Message')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    resolve({ ok: true, json: async () => ({ message: {} }) })
    await flushPromises()
  })
})
