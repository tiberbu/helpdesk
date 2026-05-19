/**
 * Sprint 6 — accessibility, i18n, reduced-motion unit tests.
 *
 * These cover the additions made on top of the Sprint 3+4 controller:
 *   - window.__hdLoginI18n is honoured for visible strings, English fallback
 *     fires when a key is missing.
 *   - showError flips aria-invalid="true" on inputs in scope; clearError
 *     flips it back to "false".
 *   - The polite live region (data-view-announcer) gets an updated string on
 *     every view swap.
 *   - prefers-reduced-motion suppresses the per-second resend countdown
 *     (no setInterval; one setTimeout for the full window instead).
 *   - aria-busy is set/removed on the sign-in submit button.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
// @ts-expect-error -- vanilla ES module, no .d.ts
import { createLoginController } from "../../../../helpdesk/public/js/login.js";

const A11Y_DOC = `
<meta name="csrf-token" content="t-token">
<div class="hd-login">
  <div
      class="hd-login__visually-hidden"
      data-view-announcer
      aria-live="polite"
      aria-atomic="true"></div>
  <div class="hd-login__card">
    <div class="hd-login__view" data-view="sign-in">
      <form data-view-form="sign-in" method="post" action="/api/method/login">
        <input id="hd-login-email" type="email" name="usr"
               aria-describedby="hd-login-error-sign-in" aria-invalid="false">
        <div class="hd-login__password-wrap">
          <input id="hd-login-password" type="password" name="pwd"
                 aria-describedby="hd-login-error-sign-in" aria-invalid="false">
          <button type="button" data-toggle-password="hd-login-password"
                  aria-pressed="false" aria-label="Show password">eye</button>
        </div>
        <div class="hd-login__error" id="hd-login-error-sign-in"
             data-error role="alert" aria-live="assertive" hidden></div>
        <button type="submit">Sign in</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="forgot" hidden>
      <form data-view-form="forgot">
        <input type="email" required
               aria-describedby="hd-login-error-forgot" aria-invalid="false">
        <div class="hd-login__error" id="hd-login-error-forgot"
             data-error role="alert" aria-live="assertive" hidden></div>
        <button type="submit">Send</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="mfa-otp" hidden>
      ${[0, 1, 2, 3, 4, 5].map(() => '<input data-otp-cell maxlength="1">').join("")}
      <div class="hd-login__error" data-error hidden></div>
      <button type="button" data-resend-otp>Resend code</button>
    </div>
    <div class="hd-login__view" data-view="locked-out" hidden>
      <span data-lockout-message></span>
    </div>
  </div>
</div>
`;

function setupDom() {
    document.body.innerHTML = A11Y_DOC;
    return document.querySelector(".hd-login") as HTMLElement;
}

function makeWindowStub(opts: { reducedMotion?: boolean; i18n?: Record<string, string> } = {}): any {
    return {
        location: {
            protocol: "https:",
            hostname: "support.tiberbu.app",
            hash: "",
            href: "https://support.tiberbu.app/login_preview",
            pathname: "/login_preview",
            search: "",
            origin: "https://support.tiberbu.app",
        },
        history: { pushState: vi.fn(), replaceState: vi.fn() },
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        fetch: vi.fn(),
        matchMedia: vi
            .fn()
            .mockReturnValue({ matches: Boolean(opts.reducedMotion) }),
        __hdLoginI18n: opts.i18n,
        __hdTelemetry: { enabled: false },
        innerWidth: 1280,
    };
}

function makeRes({
    ok = true,
    status = 200,
    headers = {},
    json = {},
}: { ok?: boolean; status?: number; headers?: Record<string, string>; json?: any } = {}) {
    return {
        ok,
        status,
        headers: new Headers(headers),
        json: async () => json,
    };
}

async function flush(n = 5) {
    for (let i = 0; i < n; i += 1) {
        await Promise.resolve();
    }
}

describe("Sprint 6 — i18n", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("uses translated strings from window.__hdLoginI18n when provided", () => {
        const root = setupDom();
        const win = makeWindowStub({
            i18n: {
                bad_credentials: "Email ou mot de passe incorrect.",
                show_password: "Afficher le mot de passe",
            },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.t("bad_credentials")).toBe("Email ou mot de passe incorrect.");
        expect(ctrl.t("show_password")).toBe("Afficher le mot de passe");
    });

    it("falls back to English when a key is missing from the live dict", () => {
        const root = setupDom();
        // Live dict missing `bad_credentials`.
        const win = makeWindowStub({ i18n: { show_password: "Voir" } });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.t("bad_credentials")).toBe(
            "Email or password is incorrect."
        );
    });

    it("interpolates {seconds} into translated countdown strings", () => {
        const root = setupDom();
        const win = makeWindowStub({
            i18n: {
                locked_out_countdown:
                    "Réessayez dans {seconds} secondes.",
            },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.t("locked_out_countdown", { seconds: 30 })).toBe(
            "Réessayez dans 30 secondes."
        );
    });
});

describe("Sprint 6 — ARIA wiring", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("flips aria-invalid='true' on described inputs when an error is shown", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ ok: false, status: 401, json: { message: "Invalid login" } })
        );
        createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "wrong";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        const email = root.querySelector("#hd-login-email") as HTMLInputElement;
        const pwd = root.querySelector("#hd-login-password") as HTMLInputElement;
        expect(email.getAttribute("aria-invalid")).toBe("true");
        expect(pwd.getAttribute("aria-invalid")).toBe("true");
    });

    it("sets aria-busy on the submit button while the sign-in request is in flight", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        let resolveFetch: (v: any) => void = () => {};
        const fetchSpy = vi.fn(
            () => new Promise((resolve) => (resolveFetch = resolve))
        );
        createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        const submit = form.querySelector("button[type='submit']") as HTMLButtonElement;

        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();
        expect(submit.getAttribute("aria-busy")).toBe("true");
        expect(submit.disabled).toBe(true);

        resolveFetch(makeRes({ ok: true, status: 200, json: {} }));
        await flush();
        expect(submit.hasAttribute("aria-busy")).toBe(false);
        expect(submit.disabled).toBe(false);
    });

    it("announces every view swap into the polite live region", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });

        const announcer = root.querySelector(
            "[data-view-announcer]"
        ) as HTMLElement;

        ctrl.setView("forgot");
        expect(announcer.textContent).toMatch(/Reset your password\.?/);

        ctrl.setView("locked-out");
        expect(announcer.textContent).toMatch(/Account temporarily locked\.?/);

        ctrl.setView("sign-in");
        expect(announcer.textContent).toMatch(/Sign in form\.?/);
    });
});

describe("Sprint 6 — reduced motion", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it("prefersReducedMotion() returns true when the media query matches", () => {
        const root = setupDom();
        const win = makeWindowStub({ reducedMotion: true });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.prefersReducedMotion()).toBe(true);
    });

    it("resend countdown does NOT tick per-second when reduced motion is on", async () => {
        const root = setupDom();
        const win = makeWindowStub({ reducedMotion: true });
        const fetchSpy = vi.fn().mockResolvedValue(makeRes({ json: {} }));
        createLoginController(root, { window: win, fetch: fetchSpy });

        const resend = root.querySelector(
            "[data-resend-otp]"
        ) as HTMLButtonElement;

        // Click once.
        resend.click();
        await flush();

        // The button is disabled with the full-window text. It should NOT
        // change one second later (which is what the animated path does).
        const initialText = resend.textContent || "";
        expect(resend.disabled).toBe(true);
        vi.advanceTimersByTime(1000);
        await flush();
        expect(resend.textContent).toBe(initialText);
        expect(resend.disabled).toBe(true);

        // After the full 30s window the button re-enables.
        vi.advanceTimersByTime(30 * 1000);
        await flush();
        expect(resend.disabled).toBe(false);
    });

    it("resend countdown DOES tick per-second when reduced motion is off", async () => {
        const root = setupDom();
        const win = makeWindowStub({ reducedMotion: false });
        const fetchSpy = vi.fn().mockResolvedValue(makeRes({ json: {} }));
        createLoginController(root, { window: win, fetch: fetchSpy });

        const resend = root.querySelector(
            "[data-resend-otp]"
        ) as HTMLButtonElement;

        resend.click();
        await flush();

        const t0 = resend.textContent || "";
        expect(t0).toMatch(/30/);
        vi.advanceTimersByTime(1000);
        await flush();
        expect(resend.textContent).not.toBe(t0);
        expect(resend.textContent).toMatch(/29/);
    });
});
