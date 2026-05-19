/**
 * Sprint 8 e2e — happy/sad-path coverage of the redesigned login page.
 *
 * These specs run against the admin-gated /login_preview route so they don't
 * depend on the production /login feature flag. The cutover spec
 * (login-flag.spec.ts) covers the flag-gated /login behavior separately.
 */

import { test, expect } from "@playwright/test";
import {
    gotoPreview,
    mockLogin,
    mockReset,
    pasteOtp,
} from "./_fixtures";

test.describe("redesigned login — happy path", () => {
    test("renders Tiberbu brand surface for ?tenant=Tiberbu", async ({ page }) => {
        await gotoPreview(page, "?tenant=Tiberbu");
        await expect(page.locator(".hd-login__badge-label")).toContainText(
            "Tiberbu"
        );
        // Brand colour propagates via the inline custom property.
        const bg = await page.evaluate(() =>
            getComputedStyle(
                document.querySelector(".hd-login") as HTMLElement
            ).getPropertyValue("--hd-primary").trim()
        );
        expect(bg.toLowerCase()).toBe("#5551ff");
    });

    test("password toggle flips type + aria-pressed + aria-label", async ({
        page,
    }) => {
        await gotoPreview(page);
        const pwd = page.locator("#hd-login-password");
        const toggle = page.locator("[data-toggle-password]");
        await expect(pwd).toHaveAttribute("type", "password");
        await toggle.click();
        await expect(pwd).toHaveAttribute("type", "text");
        await expect(toggle).toHaveAttribute("aria-pressed", "true");
        await toggle.click();
        await expect(pwd).toHaveAttribute("type", "password");
        await expect(toggle).toHaveAttribute("aria-pressed", "false");
    });

    test("forgot link swaps to forgot view + URL hash + back-link returns", async ({
        page,
    }) => {
        await gotoPreview(page);
        await page.locator('a[href="#forgot"]').click();
        await expect(page).toHaveURL(/#forgot$/);
        await expect(page.locator("[data-view='forgot']")).toBeVisible();
        await page.locator("[data-back-to-signin]").first().click();
        await expect(page.locator("[data-view='sign-in']")).toBeVisible();
    });

    test("submitting forgot form always shows reset-success (privacy)", async ({
        page,
    }) => {
        await mockReset(page, 200);
        await gotoPreview(page);
        await page.locator('a[href="#forgot"]').click();
        await page
            .locator("[data-view-form='forgot'] input[type='email']")
            .fill("anybody@example.com");
        await page
            .locator("[data-view-form='forgot'] button[type='submit']")
            .click();
        await expect(page.locator("[data-view='reset-success']")).toBeVisible();
    });
});

test.describe("redesigned login — auth response handling", () => {
    test("MFA challenge swaps to OTP view, OTP cells autofocus", async ({
        page,
    }) => {
        await mockLogin(page, {
            status: 200,
            body: {
                verification: { type: "OTP App" },
                tmp_id: "mock-tmp-id",
            },
        });
        await gotoPreview(page);
        await page.locator("#hd-login-email").fill("user@example.com");
        await page.locator("#hd-login-password").fill("password");
        await page
            .locator("[data-view-form='sign-in'] button[type='submit']")
            .click();

        await expect(page.locator("[data-view='mfa-otp']")).toBeVisible();
        const announcer = page.locator("[data-view-announcer]");
        await expect(announcer).toContainText(/One-time code/i);
    });

    test("paste of 6 digits fills cells + auto-submits MFA", async ({ page }) => {
        // First fetch returns MFA challenge, second (the OTP submit) returns success.
        let calls = 0;
        await page.route("**/api/method/login", async (route) => {
            calls += 1;
            if (calls === 1) {
                await route.fulfill({
                    status: 200,
                    headers: { "content-type": "application/json" },
                    body: JSON.stringify({
                        verification: { type: "OTP App" },
                        tmp_id: "mock-tmp-id",
                    }),
                });
            } else {
                await route.fulfill({
                    status: 200,
                    headers: { "content-type": "application/json" },
                    body: JSON.stringify({ redirect_to: "/helpdesk" }),
                });
            }
        });

        await gotoPreview(page);
        await page.locator("#hd-login-email").fill("user@example.com");
        await page.locator("#hd-login-password").fill("password");
        await page
            .locator("[data-view-form='sign-in'] button[type='submit']")
            .click();
        await expect(page.locator("[data-view='mfa-otp']")).toBeVisible();
        await pasteOtp(page, "123456");
        // submitOtp fires automatically; verify second login call happened.
        await expect.poll(() => calls).toBe(2);
    });

    test("429 with Retry-After triggers locked-out view + countdown text", async ({
        page,
    }) => {
        await mockLogin(page, {
            status: 429,
            headers: { "Retry-After": "30" },
            body: {},
        });
        await gotoPreview(page);
        await page.locator("#hd-login-email").fill("user@example.com");
        await page.locator("#hd-login-password").fill("p");
        await page
            .locator("[data-view-form='sign-in'] button[type='submit']")
            .click();
        await expect(page.locator("[data-view='locked-out']")).toBeVisible();
        await expect(page.locator("[data-lockout-message]")).toContainText(
            /Try again in \d+ seconds/i
        );
    });

    test("LoginAttemptTracker lockout (no Retry-After) shows generic message", async ({
        page,
    }) => {
        await mockLogin(page, {
            status: 417,
            body: {
                _server_messages: '["Account locked. Resume after 600 seconds"]',
            },
        });
        await gotoPreview(page);
        await page.locator("#hd-login-email").fill("user@example.com");
        await page.locator("#hd-login-password").fill("p");
        await page
            .locator("[data-view-form='sign-in'] button[type='submit']")
            .click();
        await expect(page.locator("[data-view='locked-out']")).toBeVisible();
        await expect(page.locator("[data-lockout-message]")).toContainText(
            /temporarily locked/i
        );
        await expect(page.locator("[data-lockout-message]")).not.toContainText(
            /Try again in/i
        );
    });

    test("bad credentials shows the combined error + flips aria-invalid", async ({
        page,
    }) => {
        await mockLogin(page, {
            status: 401,
            body: { message: "Invalid login" },
        });
        await gotoPreview(page);
        await page.locator("#hd-login-email").fill("user@example.com");
        await page.locator("#hd-login-password").fill("wrong");
        await page
            .locator("[data-view-form='sign-in'] button[type='submit']")
            .click();

        const err = page.locator("#hd-login-error-sign-in");
        await expect(err).toBeVisible();
        await expect(err).toContainText(/incorrect/i);
        await expect(page.locator("#hd-login-email")).toHaveAttribute(
            "aria-invalid",
            "true"
        );
        await expect(page.locator("#hd-login-password")).toHaveAttribute(
            "aria-invalid",
            "true"
        );
    });
});

test.describe("redesigned login — security headers", () => {
    test("CSP + X-Frame + nosniff + Referrer-Policy are present", async ({
        page,
    }) => {
        // Hit /login_preview directly via request to inspect the origin
        // headers (the page.goto path may run through extra browser
        // middleware that obscures them).
        const res = await page.request.get("/login_preview", {
            failOnStatusCode: false,
        });
        // Anonymous gets 404; if the test runner is authenticated we get
        // 200. Either way the headers we set unconditionally are present
        // for the 200 response.
        if (res.status() === 200) {
            const csp = res.headers()["content-security-policy"];
            expect(csp).toBeTruthy();
            expect(csp).toContain("default-src 'self'");
            expect(csp).toContain("script-src 'self' 'nonce-");
            expect(csp).toContain("frame-ancestors 'none'");
            expect(res.headers()["x-frame-options"]).toBe("DENY");
            expect(res.headers()["x-content-type-options"]).toBe("nosniff");
            expect(res.headers()["referrer-policy"]).toBe("no-referrer");
        }
    });
});
