/**
 * Sprint 7 — telemetry envelope, allow-list enforcement, failure-category
 * mapping, and the in-process source-scan lint.
 *
 * The lint test (at the end) reads login.js as text and asserts that no
 * client-side secret-storage primitives are referenced. This stands in for
 * an ESLint rule until the desk app's lint config is extended in Sprint 8.
 */

import fs from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
// @ts-expect-error -- vanilla ES module, no .d.ts
import { createLoginController } from "../../../../helpdesk/public/js/login.js";

const TEL_DOC = `
<meta name="csrf-token" content="t-token">
<div class="hd-login">
  <div data-view-announcer aria-live="polite"></div>
  <div class="hd-login__card">
    <div class="hd-login__view" data-view="sign-in">
      <form data-view-form="sign-in" method="post" action="/api/method/login">
        <input id="hd-login-email" type="email" name="usr">
        <div class="hd-login__password-wrap">
          <input id="hd-login-password" type="password" name="pwd">
          <button type="button" data-toggle-password="hd-login-password"
                  aria-pressed="false" aria-label="Show password">eye</button>
        </div>
        <a class="hd-login__link" href="#forgot">Forgot</a>
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Sign in</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="forgot" hidden>
      <form data-view-form="forgot">
        <input type="email" required>
        <div class="hd-login__error" data-error hidden></div>
        <button type="submit">Send</button>
      </form>
    </div>
    <div class="hd-login__view" data-view="reset-success" hidden></div>
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

const ALLOW_LIST = [
    "login_page_view",
    "login_attempt",
    "login_success",
    "login_failed",
    "mfa_step_shown",
    "mfa_success",
    "mfa_failed",
    "mfa_resend_requested",
    "forgot_password_clicked",
    "reset_link_requested",
    "lockout_triggered",
];

const PROP_ALLOW_LIST = [
    "route",
    "mfa_method",
    "failure_category",
    "reduced_motion",
    "viewport_bucket",
    "request_id",
    "brand_slug",
];

function setupDom() {
    document.body.innerHTML = TEL_DOC;
    return document.querySelector(".hd-login") as HTMLElement;
}

function makeWindowStub({
    enabled = true,
    posthog,
    innerWidth = 1280,
}: {
    enabled?: boolean;
    posthog?: { capture: (...args: any[]) => void; init?: (...args: any[]) => void };
    innerWidth?: number;
} = {}): any {
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
        innerWidth,
        __hdLoginI18n: undefined,
        __hdTelemetry: {
            enabled,
            posthog_host: "https://posthog.example",
            posthog_project_id: "phc_test",
            request_id: "rid-abc",
            brand_slug: "Tiberbu",
            viewport_bucket: "desktop",
            event_allow_list: ALLOW_LIST,
            property_allow_list: PROP_ALLOW_LIST,
        },
        posthog,
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

describe("Sprint 7 — track() envelope", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("no-ops when telemetry is disabled in the server config", () => {
        const root = setupDom();
        const captured: any[] = [];
        const win = makeWindowStub({
            enabled: false,
            posthog: { capture: (...args) => captured.push(args) },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });

        ctrl.track("login_attempt");
        expect(captured).toHaveLength(0);
    });

    it("drops events whose name is not on the allow-list", () => {
        const root = setupDom();
        const captured: any[] = [];
        const win = makeWindowStub({
            posthog: { capture: (...args) => captured.push(args) },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        captured.length = 0; // drop the boot login_page_view

        ctrl.track("password_logged_to_external_service", {
            failure_category: "bad_credentials",
        });
        expect(captured).toHaveLength(0);
    });

    it("drops properties not on the allow-list before forwarding to PostHog", () => {
        const root = setupDom();
        const captured: any[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name, props) => captured.push({ name, props }) },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        captured.length = 0;

        ctrl.track("login_attempt", {
            failure_category: "bad_credentials",
            // The next four MUST NOT survive the envelope.
            email: "leak@example.com",
            password: "hunter2",
            otp: "123456",
            tmp_id: "leakable",
        });

        expect(captured).toHaveLength(1);
        const { props } = captured[0];
        expect(props.failure_category).toBe("bad_credentials");
        expect(props).not.toHaveProperty("email");
        expect(props).not.toHaveProperty("password");
        expect(props).not.toHaveProperty("otp");
        expect(props).not.toHaveProperty("tmp_id");
    });

    it("always attaches request_id, brand_slug, route, viewport_bucket, reduced_motion", () => {
        const root = setupDom();
        const captured: any[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name, props) => captured.push({ name, props }) },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        captured.length = 0;

        ctrl.track("login_attempt");
        expect(captured).toHaveLength(1);
        const { props } = captured[0];
        expect(props.request_id).toBe("rid-abc");
        expect(props.brand_slug).toBe("Tiberbu");
        expect(props.route).toBe("/login_preview");
        expect(props.viewport_bucket).toBe("desktop");
        expect(props.reduced_motion).toBe(false);
    });

    it("viewport_bucket follows window.innerWidth", () => {
        const root = setupDom();
        const captured: any[] = [];
        const win = makeWindowStub({
            innerWidth: 600,
            posthog: { capture: (name, props) => captured.push({ name, props }) },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        captured.length = 0;

        ctrl.track("login_attempt");
        expect(captured[0].props.viewport_bucket).toBe("mobile");
    });

    it("posthog.capture failures are caught and never bubble up", () => {
        const root = setupDom();
        const win = makeWindowStub({
            posthog: {
                capture: () => {
                    throw new Error("boom");
                },
            },
        });
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        // Should not throw.
        expect(() => ctrl.track("login_attempt")).not.toThrow();
    });
});

describe("Sprint 7 — failure_category classifier", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("429 → rate_limited", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.classifyFailure(makeRes({ ok: false, status: 429 }), {})).toBe(
            "rate_limited"
        );
    });

    it("server message containing 'lock' → rate_limited", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        const res = makeRes({ ok: false, status: 417 });
        expect(
            ctrl.classifyFailure(res, {
                _server_messages: '["Account locked. Resume after 600 seconds"]',
            })
        ).toBe("rate_limited");
    });

    it("401 with no lock hint → bad_credentials", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(
            ctrl.classifyFailure(
                makeRes({ ok: false, status: 401 }),
                { message: "Invalid login" }
            )
        ).toBe("bad_credentials");
    });

    it("500 → unknown", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.classifyFailure(makeRes({ ok: false, status: 500 }), {})).toBe(
            "unknown"
        );
    });

    it("missing response → network_error", () => {
        const root = setupDom();
        const win = makeWindowStub();
        const ctrl = createLoginController(root, { window: win, fetch: win.fetch });
        expect(ctrl.classifyFailure(null, null)).toBe("network_error");
    });
});

describe("Sprint 7 — funnel events", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("fires login_attempt + login_success on a 200 OK", async () => {
        const root = setupDom();
        const events: string[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name) => events.push(name) },
        });
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ json: { redirect_to: "/helpdesk" } })
        );
        const navigate = vi.fn();
        createLoginController(root, { window: win, fetch: fetchSpy, navigate });

        events.length = 0; // drop boot login_page_view

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(events).toContain("login_attempt");
        expect(events).toContain("login_success");
    });

    it("fires login_failed with bad_credentials on a 401", async () => {
        const root = setupDom();
        const calls: any[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name, props) => calls.push({ name, props }) },
        });
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({ ok: false, status: 401, json: { message: "Invalid login" } })
        );
        createLoginController(root, { window: win, fetch: fetchSpy });
        calls.length = 0;

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "wrong";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        const failed = calls.find((c) => c.name === "login_failed");
        expect(failed).toBeTruthy();
        expect(failed.props.failure_category).toBe("bad_credentials");
    });

    it("fires lockout_triggered on a 429", async () => {
        const root = setupDom();
        const events: string[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name) => events.push(name) },
        });
        const fetchSpy = vi.fn().mockResolvedValue(
            makeRes({
                ok: false,
                status: 429,
                headers: { "Retry-After": "30" },
                json: {},
            })
        );
        createLoginController(root, { window: win, fetch: fetchSpy });
        events.length = 0;

        (root.querySelector("#hd-login-email") as HTMLInputElement).value = "u@x";
        (root.querySelector("#hd-login-password") as HTMLInputElement).value = "p";
        const form = root.querySelector("[data-view-form='sign-in']") as HTMLFormElement;
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(events).toContain("lockout_triggered");
        expect(events).toContain("login_failed");
    });

    it("forgot_password_clicked + reset_link_requested fire on the reset path", async () => {
        const root = setupDom();
        const events: string[] = [];
        const win = makeWindowStub({
            posthog: { capture: (name) => events.push(name) },
        });
        const fetchSpy = vi.fn().mockResolvedValue(makeRes({ json: {} }));
        createLoginController(root, { window: win, fetch: fetchSpy });
        events.length = 0;

        (root.querySelector('a[href="#forgot"]') as HTMLElement).click();
        expect(events).toContain("forgot_password_clicked");

        const form = root.querySelector(
            "[data-view-form='forgot']"
        ) as HTMLFormElement;
        (form.querySelector("input[type='email']") as HTMLInputElement).value =
            "anybody@example.com";
        form.dispatchEvent(new Event("submit", { cancelable: true }));
        await flush();

        expect(events).toContain("reset_link_requested");
    });
});

describe("Sprint 7 — source-scan lint (no client secret storage)", () => {
    const SOURCE_PATH = path.resolve(
        __dirname,
        "../../../../helpdesk/public/js/login.js"
    );
    const source = fs.readFileSync(SOURCE_PATH, "utf8");

    it("does not reference localStorage anywhere", () => {
        expect(source).not.toMatch(/\blocalStorage\b/);
    });

    it("does not reference sessionStorage anywhere", () => {
        expect(source).not.toMatch(/\bsessionStorage\b/);
    });

    it("does not write to document.cookie", () => {
        // Read-side `document.cookie` is acceptable (CSRF helpers historically
        // do that), but writes are forbidden because we never persist auth
        // state ourselves. Match `document.cookie =` or `document.cookie+=`.
        expect(source).not.toMatch(/document\.cookie\s*[+]?=/);
    });

    it("does not pull in any third-party imports", () => {
        // `import` from anywhere — the file is supposed to be a pure ES
        // module with zero deps. If this regex ever fires, the audit point
        // (single-file controller) is broken.
        expect(source).not.toMatch(/^\s*import\s/m);
    });

    it("documents the property allow-list in source", () => {
        // Cheap sanity check: the property allow-list constant is
        // referenced by name. Keeps the contract visible to future
        // contributors via grep.
        expect(source).toMatch(/property_allow_list/);
        expect(source).toMatch(/event_allow_list/);
    });
});
