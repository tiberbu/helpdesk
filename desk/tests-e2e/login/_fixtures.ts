/**
 * Sprint 8 e2e — shared fixtures.
 *
 * These helpers keep the actual specs free of repetitive routing /
 * mocking boilerplate. They are intentionally narrow: this is not a
 * general-purpose Frappe Playwright kit.
 */

import { Page, expect } from "@playwright/test";

/** Open /login_preview as the admin so the redesigned body renders. */
export async function gotoPreview(page: Page, query = "") {
    // The admin gate uses a normal Frappe session cookie. CI logs in via
    // /api/method/login first; locally Playwright will follow the redirect.
    await loginAsAdmin(page);
    await page.goto(`/login_preview${query}`, { waitUntil: "domcontentloaded" });
    await expect(page.locator(".hd-login__shell")).toBeVisible();
}

/** Drive Frappe's framework /api/method/login to seed a session cookie. */
async function loginAsAdmin(page: Page) {
    const email = process.env.PW_ADMIN_EMAIL || "ubuntu@tiberbu.health";
    const password = process.env.PW_ADMIN_PASSWORD || "admin";
    const res = await page.request.post("/api/method/login", {
        form: { usr: email, pwd: password },
        failOnStatusCode: false,
    });
    if (!res.ok()) {
        throw new Error(
            `Could not pre-authenticate as admin (status ${res.status()}). ` +
                "Set PW_ADMIN_EMAIL / PW_ADMIN_PASSWORD env vars."
        );
    }
}

/**
 * Mock /api/method/login responses so we can exercise every controller
 * branch (success / 401 / 429 / MFA challenge) without touching real
 * users. Returns the route handler ID so the caller can detach.
 */
export async function mockLogin(
    page: Page,
    response: {
        status: number;
        body?: any;
        headers?: Record<string, string>;
    }
) {
    await page.route("**/api/method/login", async (route) => {
        const headers = {
            "content-type": "application/json",
            ...(response.headers || {}),
        };
        await route.fulfill({
            status: response.status,
            headers,
            body: JSON.stringify(response.body ?? {}),
        });
    });
}

/** Mock the password-reset endpoint. */
export async function mockReset(page: Page, status = 200) {
    await page.route(
        "**/api/method/frappe.core.doctype.user.user.reset_password",
        async (route) => {
            await route.fulfill({
                status,
                headers: { "content-type": "application/json" },
                body: JSON.stringify({}),
            });
        }
    );
}

/** Fill the OTP grid via paste. */
export async function pasteOtp(page: Page, code: string) {
    const cells = page.locator("[data-otp-cell]");
    await cells.first().focus();
    await page.evaluate((c) => {
        const ev = new ClipboardEvent("paste", {
            clipboardData: new DataTransfer(),
            bubbles: true,
            cancelable: true,
        });
        ev.clipboardData!.setData("text", c);
        document.activeElement?.dispatchEvent(ev);
    }, code);
}
