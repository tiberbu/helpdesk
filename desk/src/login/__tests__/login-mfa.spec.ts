/**
 * Sprint 4 unit tests — MFA OTP grid, server-driven lockout, forced
 * password change, and the sign-in submit interceptor.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
// @ts-expect-error -- vanilla ES module, no .d.ts
import { createLoginController } from "../../../../helpdesk/public/js/login.js";

const MFA_DOC = `
<meta name="csrf-token" content="t-token">
<div class="hd-login">
  <div class="hd-login__card">
    <div class="hd-login__view" data-view="sign-in">
      <form data-view-form="sign-in" method="post" action="/api/method/login">
        <input id="hd-login-email" type="email" name="usr">
        <div class="hd-login__password-wrap">
          <input id="hd-login-password" type="password" name="pwd">
          <button type="button" data-toggle-password="hd-login-password"
                  aria-pressed="false" aria-label="Show password">eye</button>
        </div>
        <input type="checkbox" name="remember_me" value="1">
        <a class="hd-login__link" href="#forgot">Forgot</a>
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Sign in</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="mfa-otp" hidden>
      ${[0, 1, 2, 3, 4, 5].map(() => '<input data-otp-cell maxlength="1">').join("")}
      <div class="hd-login__error" data-error hidden></div>
      <button type="button" data-resend-otp>Resend</button>
    </div>
    <div class="hd-login__view" data-view="new-password" hidden>
      <form data-view-form="new-password">
        <input name="new_password" type="password">
        <input name="confirm_password" type="password">
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Set</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="locked-out" hidden>
      <span data-lockout-message></span>
    </div>
    <div data-post-reset-banner hidden></div>
  </div>
</div>
`;

function setupDom() {
    document.body.innerHTML = MFA_DOC;
    return document.querySelector(".hd-login") as HTMLElement;
}

function makeWindowStub(): any {
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
        matchMedia: vi.fn().mockReturnValue({ matches: false }),
        innerWidth: 1280,
        // Sprint 7 — disabled by default so existing tests stay focused on
        // their own assertions; Sprint 7 specs override.
        __hdTelemetry: { enabled: false },
    };
}

function makeRes({
    ok = true,
    status = 200,
    headers = {},
    json = {},
}: { ok?: boolean; status?: number; headers?: Record<string, string>; json?: any } = {}) {
    const headerMap = new Headers(headers);
    return {
        ok,
        status,
        headers: headerMap,
        json: async () => json,
    };
}

async function flush(n = 5) {
    for (let i = 0; i < n; i += 1) {
        await Promise.resolve();
    }
}

describe("MFA OTP flow", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it("sign-in response with verification block swaps to mfa-otp view", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({
                json: {
                    verification: { type: "OTP App" },
                    tmp_id: "abc123",
                },
            })
        );
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(ctrl.view).toBe("mfa-otp");
        expect(ctrl.tmpId).toBe("abc123");
        expect(ctrl.mfaMethod).toBe("OTP App");
    });

    it("OTP cell input auto-advances focus", () => {
        const root = setupDom();
        const win = makeWindowStub();
        createLoginController(root, { window: win, fetch: win.fetch });

        const cells = Array.from(
            root.querySelectorAll("[data-otp-cell]")
        ) as HTMLInputElement[];
        cells[0].value = "1";
        cells[0].dispatchEvent(new Event("input", { bubbles: true }));
        expect(document.activeElement).toBe(cells[1]);
    });

    it("OTP backspace on empty cell focuses previous and clears it", () => {
        const root = setupDom();
        const win = makeWindowStub();
        createLoginController(root, { window: win, fetch: win.fetch });

        const cells = Array.from(
            root.querySelectorAll("[data-otp-cell]")
        ) as HTMLInputElement[];
        cells[0].value = "1";
        cells[1].focus();
        const ev = new KeyboardEvent("keydown", { key: "Backspace", bubbles: true, cancelable: true });
        cells[1].dispatchEvent(ev);
        expect(cells[0].value).toBe("");
        expect(document.activeElement).toBe(cells[0]);
    });

    it("OTP arrow keys move focus between cells", () => {
        const root = setupDom();
        const win = makeWindowStub();
        createLoginController(root, { window: win, fetch: win.fetch });

        const cells = Array.from(
            root.querySelectorAll("[data-otp-cell]")
        ) as HTMLInputElement[];
        cells[2].focus();
        cells[2].dispatchEvent(
            new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true, cancelable: true })
        );
        expect(document.activeElement).toBe(cells[1]);

        cells[1].dispatchEvent(
            new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, cancelable: true })
        );
        expect(document.activeElement).toBe(cells[2]);
    });

    it("OTP paste of 6 digits fills all cells and triggers submit", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ json: { redirect_to: "/helpdesk" } })
        );
        const navigate = vi.fn();
        const ctrl = createLoginController(root, {
            window: win,
            fetch: fetchSpy,
            navigate,
        });

        // Get into MFA state.
        ctrl.handleAuthResponse(
            makeRes({ json: { verification: { type: "OTP App" }, tmp_id: "tid" } }),
            { verification: { type: "OTP App" }, tmp_id: "tid" },
            { usr: "u@x", pwd: "p" }
        );
        await flush();

        const cells = Array.from(
            root.querySelectorAll("[data-otp-cell]")
        ) as HTMLInputElement[];
        const pasteEvent = new Event("paste", { bubbles: true, cancelable: true }) as any;
        pasteEvent.clipboardData = { getData: () => "123456" };
        cells[0].dispatchEvent(pasteEvent);

        // Cells filled
        expect(cells.map((c) => c.value).join("")).toBe("123456");
        await flush();

        // submitOtp issued a fetch with otp + tmp_id
        const otpCall = fetchSpy.mock.calls.find(([, init]) =>
            (init as any).body?.includes("otp=123456")
        );
        expect(otpCall).toBeTruthy();
        expect((otpCall![1] as any).body).toContain("tmp_id=tid");
    });

    it("Retry-After header on 429 puts UI into locked-out view with countdown", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({
                ok: false,
                status: 429,
                headers: { "Retry-After": "30" },
                json: {},
            })
        );
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(ctrl.view).toBe("locked-out");
        const msg = root.querySelector("[data-lockout-message]") as HTMLElement;
        expect(msg.textContent).toMatch(/Try again in 30 seconds/);
    });

    it("LoginAttemptTracker lockout (no Retry-After) shows generic message", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({
                ok: false,
                status: 417,
                json: { _server_messages: "[\"Account locked. Resume after 600 seconds\"]" },
            })
        );
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(ctrl.view).toBe("locked-out");
        const msg = root.querySelector("[data-lockout-message]") as HTMLElement;
        expect(msg.textContent).toMatch(/temporarily locked/);
        expect(msg.textContent).not.toMatch(/Try again in/);
    });

    it("invalid credentials shows the combined error message", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ ok: false, status: 401, json: { message: "Invalid login" } })
        );
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "wrong";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(ctrl.view).toBe("sign-in");
        const err = root.querySelector(
            "[data-view='sign-in'] [data-error]"
        ) as HTMLElement;
        expect(err.hidden).toBe(false);
        expect(err.textContent).toMatch(/incorrect/i);
    });

    it("successful auth redirects to server-supplied redirect_to", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ json: { message: { redirect_to: "/helpdesk" } } })
        );
        const navigate = vi.fn();
        createLoginController(root, { window: win, fetch: fetchSpy, navigate });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(navigate).toHaveBeenCalledWith("/helpdesk");
    });

    it("successful OTP verify clears tmp_id and redirects", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi
            .fn()
            // Initial sign-in returns MFA challenge.
            .mockResolvedValueOnce(
                makeRes({ json: { verification: { type: "OTP App" }, tmp_id: "tid" } })
            )
            // OTP verify succeeds.
            .mockResolvedValueOnce(makeRes({ json: { redirect_to: "/helpdesk" } }));
        const navigate = vi.fn();
        const ctrl = createLoginController(root, {
            window: win,
            fetch: fetchSpy,
            navigate,
        });

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();
        expect(ctrl.view).toBe("mfa-otp");

        // Fill the cells.
        const cells = Array.from(
            root.querySelectorAll("[data-otp-cell]")
        ) as HTMLInputElement[];
        cells.forEach((c, i) => {
            c.value = String(i + 1);
        });
        await ctrl.submitOtp();
        await flush();

        expect(navigate).toHaveBeenCalledWith("/helpdesk");
        expect(ctrl.tmpId).toBeNull();
    });
});
