/**
 * Sprint 3 unit tests for the helpdesk redesigned login controller.
 *
 * Source under test lives at apps/helpdesk/helpdesk/public/js/login.js.
 * We import via a relative path that goes outside the desk Vite project — the
 * file is plain ESM with no framework dependencies, so that's safe.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
// @ts-expect-error -- vanilla ES module, no .d.ts
import { createLoginController } from "../../../../helpdesk/public/js/login.js";

const MINIMAL_DOCUMENT = `
<meta name="csrf-token" content="test-token">
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
        <a class="hd-login__link" href="#forgot">Forgot password?</a>
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Sign in</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="forgot" hidden>
      <form data-view-form="forgot">
        <input type="email" required>
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Send reset link</button>
        <a href="#" data-back-to-signin>Back</a>
      </form>
    </div>
    <div class="hd-login__view" data-view="reset-success" hidden>
      <div>If an account exists...</div>
    </div>
    <div data-post-reset-banner hidden>banner</div>
  </div>
</div>
`;

function setupDom(htmlOverride?: string) {
    document.body.innerHTML = htmlOverride ?? MINIMAL_DOCUMENT;
    return document.querySelector(".hd-login") as HTMLElement;
}

function makeWindowStub(opts: Partial<{ protocol: string; hostname: string; hash: string; reducedMotion: boolean; i18n: Record<string, string> }> = {}) {
    const stub: any = {
        location: {
            protocol: opts.protocol ?? "https:",
            hostname: opts.hostname ?? "support.tiberbu.app",
            hash: opts.hash ?? "",
            href: "https://support.tiberbu.app/login_preview",
            pathname: "/login_preview",
            search: "",
            origin: "https://support.tiberbu.app",
        },
        history: {
            pushState: vi.fn((_state, _title, url) => {
                if (typeof url === "string" && url.startsWith("#")) {
                    stub.location.hash = url;
                }
            }),
            replaceState: vi.fn(),
        },
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        fetch: vi.fn(),
        matchMedia: vi
            .fn()
            .mockReturnValue({ matches: Boolean(opts.reducedMotion) }),
        __hdLoginI18n: opts.i18n ?? undefined,
        __hdTelemetry: { enabled: false },
        innerWidth: 1280,
    };
    return stub;
}

describe("createLoginController", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("starts in the sign-in view", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.view).toBe("sign-in");
    });

    it("setView('forgot') updates state and DOM", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        ctrl.setView("forgot");
        expect(ctrl.view).toBe("forgot");
        expect(root.querySelector(".hd-login__card")?.getAttribute("data-view"))
            .toBe("forgot");
    });

    it("clicking the forgot link swaps to the forgot view", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        const link = root.querySelector('a[href="#forgot"]') as HTMLElement;
        link.click();
        expect(ctrl.view).toBe("forgot");
    });

    it("password toggle flips type and aria-pressed", () => {
        const root = setupDom();
        const win = makeWindowStub();
        createLoginController(root, { window: win, fetch: win.fetch });

        const input = root.querySelector("#hd-login-password") as HTMLInputElement;
        const btn = root.querySelector("[data-toggle-password]") as HTMLButtonElement;

        expect(input.type).toBe("password");
        btn.click();
        expect(input.type).toBe("text");
        expect(btn.getAttribute("aria-pressed")).toBe("true");
        btn.click();
        expect(input.type).toBe("password");
        expect(btn.getAttribute("aria-pressed")).toBe("false");
    });

    it("postForm attaches the CSRF token from the meta tag", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue({
            json: async () => ({}),
            headers: new Headers(),
            status: 200,
        });
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        await ctrl.postForm("/api/method/login", { usr: "x", pwd: "y" });

        expect(fetchSpy).toHaveBeenCalledTimes(1);
        const [, init] = fetchSpy.mock.calls[0];
        expect(init.headers["X-Frappe-CSRF-Token"]).toBe("test-token");
        expect(init.body).toContain("usr=x");
    });

    it("HTTPS guard returns false for plain HTTP on a non-localhost host", () => {
        const root = setupDom();
        const win = makeWindowStub({ protocol: "http:", hostname: "example.com" });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.isHttpsOrLocalhost()).toBe(false);
    });

    it("HTTPS guard allows localhost over plain HTTP", () => {
        const root = setupDom();
        const win = makeWindowStub({ protocol: "http:", hostname: "localhost" });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.isHttpsOrLocalhost()).toBe(true);
    });

    it("safeRedirect navigates to a server-supplied path but ignores cross-origin", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const navigate = vi.fn();
        const ctrl = createLoginController(root, {
            window: win,
            fetch: win.fetch,
            navigate,
        });

        ctrl.safeRedirect("/helpdesk");
        expect(navigate).toHaveBeenCalledWith("/helpdesk");

        ctrl.safeRedirect("https://evil.example/steal");
        expect(navigate).toHaveBeenCalledTimes(1); // unchanged
    });

    async function flushMicrotasks(n = 5) {
        for (let i = 0; i < n; i += 1) {
            await Promise.resolve();
        }
    }

    it("forgot form submit always shows reset-success (privacy-preserving)", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockResolvedValue({
            json: async () => ({}),
            headers: new Headers(),
            status: 200,
        });
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        ctrl.setView("forgot");
        const form = root.querySelector(
            "[data-view-form='forgot']"
        ) as HTMLFormElement;
        const email = form.querySelector("input[type='email']") as HTMLInputElement;
        email.value = "anybody@example.com";

        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flushMicrotasks();

        expect(ctrl.view).toBe("reset-success");
        expect(fetchSpy).toHaveBeenCalledWith(
            "/api/method/helpdesk.api.forgot_password.request_reset",
            expect.any(Object)
        );
    });

    it("forgot form submit shows reset-success even on network error", async () => {
        const root = setupDom();
        const win = makeWindowStub();
        const fetchSpy = vi.fn().mockRejectedValue(new Error("offline"));
        const ctrl = createLoginController(root, { window: win, fetch: fetchSpy });

        ctrl.setView("forgot");
        const form = root.querySelector(
            "[data-view-form='forgot']"
        ) as HTMLFormElement;

        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flushMicrotasks();

        expect(ctrl.view).toBe("reset-success");
    });
});
