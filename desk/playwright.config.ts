/**
 * Playwright config for the Helpdesk redesigned login surface.
 *
 * Sprint 8: this config drives the e2e + a11y suite under tests-e2e/login/.
 * The tests run against an admin-authenticated /login_preview by default so
 * they can exercise the redesigned page without flipping the production
 * /login feature flag.
 *
 * Required env (set in CI / locally before running):
 *   - PW_BASE_URL — e.g. http://127.0.0.1:8000
 *   - PW_HOST_HEADER — e.g. support.tiberbu.app (gunicorn site routing)
 *   - PW_ADMIN_EMAIL / PW_ADMIN_PASSWORD — System Manager credentials
 *
 * Local default targets the dev gunicorn on 8000 so a workstation `bench
 * start` is enough to drive the run. CI overrides via env.
 */

import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.PW_BASE_URL || "http://127.0.0.1:8000";
const HOST_HEADER = process.env.PW_HOST_HEADER || "support.tiberbu.app";
// Used by the page.goto call so Frappe's site router picks the right site.
const EXTRA_HEADERS = HOST_HEADER ? { Host: HOST_HEADER } : undefined;

const PLATFORM_OVERRIDE = process.env.PLAYWRIGHT_HOST_PLATFORM_OVERRIDE;

export default defineConfig({
    testDir: "./tests-e2e/login",
    timeout: 30 * 1000,
    expect: { timeout: 5 * 1000 },
    fullyParallel: false,
    workers: 1,
    reporter: process.env.CI ? "github" : "list",
    use: {
        baseURL: BASE_URL,
        extraHTTPHeaders: EXTRA_HEADERS,
        trace: "retain-on-failure",
        // Sprint 8 — the redesigned login is HTTPS-required (FR-SEC-01),
        // but the gunicorn dev server is HTTP on localhost. login.js's HTTPS
        // guard explicitly allows localhost — that's why the dev base URL is
        // 127.0.0.1.
        ignoreHTTPSErrors: true,
    },
    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
        },
    ],
});
