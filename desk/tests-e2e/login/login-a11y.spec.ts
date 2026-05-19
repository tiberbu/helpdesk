/**
 * Sprint 8 — axe-core scan for FR-A11Y-01.
 *
 * The acceptance criterion (PRD §FR-A11Y-01 §1) is: "0 critical and 0
 * serious findings on /login, /login (MFA state), and /login (reset state)."
 * The serious-finding gate fires if anyone removes a label, breaks colour
 * contrast, or strips a `for` attribute. Less-than-serious findings
 * (incomplete, minor) are allowed to bubble up as a warning in the report.
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { gotoPreview, mockLogin } from "./_fixtures";

const SEVERITY_BLOCKERS = ["critical", "serious"];

function summarise(violations: any[]) {
    return violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.length,
        helpUrl: v.helpUrl,
    }));
}

test.describe("axe-core a11y scan (FR-A11Y-01)", () => {
    test("sign-in view: 0 critical + 0 serious findings", async ({ page }) => {
        await gotoPreview(page);
        const results = await new AxeBuilder({ page })
            .include(".hd-login")
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze();
        const blockers = results.violations.filter((v) =>
            SEVERITY_BLOCKERS.includes(v.impact || "")
        );
        if (blockers.length) {
            console.log("axe blockers:", JSON.stringify(summarise(blockers), null, 2));
        }
        expect(blockers).toHaveLength(0);
    });

    test("MFA-OTP view: 0 critical + 0 serious findings", async ({ page }) => {
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

        const results = await new AxeBuilder({ page })
            .include(".hd-login")
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze();
        const blockers = results.violations.filter((v) =>
            SEVERITY_BLOCKERS.includes(v.impact || "")
        );
        if (blockers.length) {
            console.log("axe blockers:", JSON.stringify(summarise(blockers), null, 2));
        }
        expect(blockers).toHaveLength(0);
    });

    test("forgot-password view: 0 critical + 0 serious findings", async ({
        page,
    }) => {
        await gotoPreview(page);
        await page.locator('a[href="#forgot"]').click();
        await expect(page.locator("[data-view='forgot']")).toBeVisible();

        const results = await new AxeBuilder({ page })
            .include(".hd-login")
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze();
        const blockers = results.violations.filter((v) =>
            SEVERITY_BLOCKERS.includes(v.impact || "")
        );
        if (blockers.length) {
            console.log("axe blockers:", JSON.stringify(summarise(blockers), null, 2));
        }
        expect(blockers).toHaveLength(0);
    });

    test("locked-out view: 0 critical + 0 serious findings", async ({ page }) => {
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

        const results = await new AxeBuilder({ page })
            .include(".hd-login")
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze();
        const blockers = results.violations.filter((v) =>
            SEVERITY_BLOCKERS.includes(v.impact || "")
        );
        if (blockers.length) {
            console.log("axe blockers:", JSON.stringify(summarise(blockers), null, 2));
        }
        expect(blockers).toHaveLength(0);
    });
});
