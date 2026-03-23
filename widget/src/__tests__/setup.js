/**
 * Vitest global test setup.
 *
 * - Provides a localStorage mock (jsdom has one but we expose helpers)
 * - Stubs window.innerWidth for responsive tests
 * - Resets fetch mock between tests
 */
import { vi } from 'vitest'

// ── localStorage helpers ───────────────────────────────────────────────────
// jsdom provides localStorage; we just ensure it's clean between tests.
beforeEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

afterEach(() => {
  localStorage.clear()
})

// ── ResizeObserver stub (not provided by jsdom) ────────────────────────────
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// ── customElements stub ────────────────────────────────────────────────────
if (!global.customElements) {
  global.customElements = {
    define: vi.fn(),
    get: vi.fn(() => undefined),
  }
}
