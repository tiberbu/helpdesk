/*
 * Helpdesk Redesigned Login — Sprints 3+4 controller
 *
 * Single ES module, no framework, no third-party imports. Loaded by
 * apps/helpdesk/helpdesk/www/login_preview.html.
 *
 * Architectural references:
 *   - PRD.md FR-AU, FR-MFA, FR-PR, FR-SEC sections
 *   - architecture.md AD-03 (Frappe MFA wiring), AD-04 (single ES module),
 *     AD-05 (server-driven lockout), AD-08 (server-trusted redirect)
 *
 * Tested via apps/helpdesk/desk/src/login/__tests__/login.spec.ts.
 */

const VIEWS = [
    "sign-in",
    "mfa-otp",
    "new-password",
    "forgot",
    "reset-success",
    "locked-out",
];

/*
 * Sprint 6 — i18n.
 *
 * The server (login_preview.py) renders a JSON dict into window.__hdLoginI18n
 * before this module runs. Every visible string the controller renders into
 * the DOM is keyed off that dict so Crowdin-fed translations apply. The
 * `_FALLBACK_I18N` map below mirrors the canonical English strings so
 * unit tests (which don't render the template) keep working unchanged. If a
 * key is missing from the live dict at runtime — e.g., the page was rendered
 * before this module was deployed — we fall back to English rather than
 * showing `undefined`.
 *
 * Strings with positional substitution use `{seconds}` placeholders.
 */
const _FALLBACK_I18N = {
    show_password: "Show password",
    hide_password: "Hide password",
    https_required: "This page must be served over HTTPS to sign in.",
    network_error:
        "Couldn't reach the server. Check your connection and try again.",
    bad_credentials: "Email or password is incorrect.",
    bad_otp: "That code didn't work. Try again.",
    locked_out:
        "Your account is temporarily locked. Try again later or reset your password.",
    locked_out_countdown:
        "Too many attempts. Try again in {seconds} seconds, or reset your password.",
    submitting: "Signing in…",
    reset_submitting: "Sending…",
    reset_success:
        "If an account exists for this address, we've sent a reset link. Check your inbox.",
    post_reset_banner: "Password updated. Please sign in.",
    passwords_dont_match: "Passwords don't match.",
    resend_in: "Resend in {seconds}s",
    resend_code: "Resend code",
    view_announcement_sign_in: "Sign in form.",
    view_announcement_mfa:
        "One-time code required. Enter the 6-digit code from your authenticator app.",
    view_announcement_forgot: "Reset your password.",
    view_announcement_reset_success: "Reset link sent if the account exists.",
    view_announcement_locked_out: "Account temporarily locked.",
    view_announcement_new_password: "Set a new password.",
};

function pickI18nSource(win) {
    const live = win && win.__hdLoginI18n;
    if (live && typeof live === "object") return live;
    return _FALLBACK_I18N;
}

function _interpolate(template, vars) {
    if (!vars) return template;
    return template.replace(/\{(\w+)\}/g, (m, k) =>
        Object.prototype.hasOwnProperty.call(vars, k) ? String(vars[k]) : m
    );
}

/*
 * Sprint 7 — Telemetry envelope.
 *
 * Single audit point for PII (per AD-07 / FR-TEL-01). Every event leaving
 * this module flows through `track()`. `track()` consults the server-supplied
 * window.__hdTelemetry object for:
 *   - whether telemetry is enabled at all (HD Settings.enable_telemetry +
 *     posthog config),
 *   - the event-name allow-list,
 *   - the property-key allow-list,
 *   - the per-request `request_id` and `brand_slug`.
 *
 * If the live config is missing (template not rendered, e.g., unit tests),
 * `_FALLBACK_TELEMETRY` keeps the controller running without crashing, with
 * telemetry disabled.
 *
 * The actual transport is `posthog.capture()` if window.posthog is present;
 * otherwise this module is a no-op. login_preview.html does NOT bundle
 * posthog.js — Frappe's bootinfo path loads it for authenticated users via
 * the existing telemetry plugin. For the redesigned login page (which runs
 * pre-auth for end users), we lazy-load it from
 * /assets/frappe/js/lib/posthog.js when telemetry is enabled.
 */
const _FALLBACK_TELEMETRY = {
    enabled: false,
    posthog_host: "",
    posthog_project_id: "",
    request_id: "",
    brand_slug: "",
    viewport_bucket: "unknown",
    event_allow_list: [],
    property_allow_list: [],
};

function pickTelemetryConfig(win) {
    const live = win && win.__hdTelemetry;
    if (live && typeof live === "object") return live;
    return _FALLBACK_TELEMETRY;
}

const OTP_LENGTH = 6;

/**
 * Boot the controller against a root element. Returns the controller
 * for tests; production callers ignore the return value.
 */
export function createLoginController(root, options = {}) {
    const win = options.window ?? window;
    const fetchImpl = options.fetch ?? win.fetch.bind(win);
    const navigate = options.navigate ?? ((url) => (win.location.href = url));

    const $ = (sel) => root.querySelector(sel);
    const $$ = (sel) => Array.from(root.querySelectorAll(sel));

    // Sprint 6 — locale + reduced-motion preferences.
    const i18nSource = pickI18nSource(win);
    function t(key, vars) {
        const template =
            (i18nSource && i18nSource[key]) ||
            _FALLBACK_I18N[key] ||
            key;
        return _interpolate(template, vars);
    }
    function prefersReducedMotion() {
        const mm = win.matchMedia
            ? win.matchMedia("(prefers-reduced-motion: reduce)")
            : null;
        return Boolean(mm && mm.matches);
    }

    // Sprint 7 — Telemetry envelope (AD-07).
    const telemetryConfig = pickTelemetryConfig(win);
    const _eventAllowSet = new Set(telemetryConfig.event_allow_list || []);
    const _propAllowSet = new Set(telemetryConfig.property_allow_list || []);

    function _viewportBucket() {
        const w = win.innerWidth || 0;
        if (w === 0) return telemetryConfig.viewport_bucket || "unknown";
        if (w < 768) return "mobile";
        if (w < 1024) return "tablet";
        return "desktop";
    }

    /**
     * Map a fetch response + parsed body to a failure_category enum.
     * The set mirrors FR-TEL-01: bad_credentials | rate_limited |
     * network_error | unknown.
     */
    function classifyFailure(res, data) {
        if (!res) return "network_error";
        if (res.status === 429) return "rate_limited";
        const msg = (data?._server_messages || data?.message || "").toString();
        if (/lock|resume after/i.test(msg)) return "rate_limited";
        if (res.status === 401 || res.status === 417) return "bad_credentials";
        return "unknown";
    }

    /**
     * Drop everything not on the property allow-list and emit the event.
     * No-op if telemetry is disabled, the event name is not in the
     * event allow-list, or window.posthog is missing.
     */
    function track(name, props) {
        if (!telemetryConfig.enabled) return;
        if (_eventAllowSet.size && !_eventAllowSet.has(name)) return;

        const safe = {
            // Always-on properties (every event carries these).
            route: "/login_preview",
            request_id: telemetryConfig.request_id || "",
            brand_slug: telemetryConfig.brand_slug || "",
            reduced_motion: prefersReducedMotion(),
            viewport_bucket: _viewportBucket(),
        };
        if (props && typeof props === "object") {
            for (const key of Object.keys(props)) {
                if (_propAllowSet.has(key)) {
                    safe[key] = props[key];
                }
                // else: silently dropped (this is intentional — the envelope
                // is the audit point; logging the drop would itself be noise).
            }
        }

        const ph = win.posthog;
        if (ph && typeof ph.capture === "function") {
            try {
                ph.capture(name, safe);
            } catch {
                // Telemetry must never break the auth flow.
            }
        }
        return safe;
    }

    const state = {
        view: "sign-in",
        lastEmail: "",
        // MFA state — held in closure only, never persisted (FR-MFA-01).
        tmpId: null,
        mfaMethod: null,
        // Lockout state.
        lockoutUntil: 0,
        countdownTimer: null,
    };

    // ---------- DOM refs ----------

    const $form = $("[data-view-form='sign-in']");
    const $emailInput = $("#hd-login-email");
    const $passwordInput = $("#hd-login-password");
    const $passwordToggle = $("[data-toggle-password]");
    const $forgotLink = $('a[href$="#forgot"]');
    const $card = $(".hd-login__card");

    // ---------- view swap ----------

    function setView(name) {
        if (!VIEWS.includes(name)) return;
        state.view = name;
        if ($card) {
            $card.dataset.view = name;
        }
        // The CSS hides views via [hidden]; the active one must have it cleared.
        $$(".hd-login__view").forEach((view) => {
            view.hidden = view.dataset.view !== name;
        });
        // Reflect in the URL hash for back-button friendliness.
        if (name === "forgot" && win.location.hash !== "#forgot") {
            win.history.pushState(null, "", "#forgot");
        }
        if (name === "sign-in" && win.location.hash) {
            win.history.pushState(null, "", win.location.pathname + win.location.search);
        }
        announceView(name);
        focusFirstField(name);
    }

    function announceView(name) {
        // Sprint 6 — write a one-line summary into the polite live region so
        // a screen reader announces the view swap without yanking focus.
        const $announcer = root.querySelector("[data-view-announcer]");
        if (!$announcer) return;
        const key = "view_announcement_" + name.replace(/-/g, "_");
        $announcer.textContent = t(key);
    }

    function focusFirstField(name) {
        const target = root.querySelector(
            `[data-view="${name}"] input:not([type='hidden']):not([disabled])`
        );
        if (target) target.focus();
    }

    // ---------- helpers ----------

    function csrfToken() {
        const meta = root.ownerDocument.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : "";
    }

    function isHttpsOrLocalhost() {
        const proto = win.location.protocol;
        const host = win.location.hostname;
        if (proto === "https:") return true;
        return host === "localhost" || host === "127.0.0.1" || host.endsWith(".localhost");
    }

    async function postForm(url, body) {
        const headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            Accept: "application/json",
            "X-Frappe-CSRF-Token": csrfToken(),
        };
        const res = await fetchImpl(url, {
            method: "POST",
            headers,
            credentials: "same-origin",
            body: new URLSearchParams(body).toString(),
        });
        let data = null;
        try {
            data = await res.json();
        } catch {
            // non-JSON response — leave data null
        }
        return { res, data };
    }

    function safeRedirect(target) {
        // AD-08: only navigate to a URL the SERVER returned. If a caller
        // hands us something that doesn't start with "/" or our origin, drop it.
        if (!target) return;
        if (typeof target !== "string") return;
        if (target.startsWith("/")) {
            navigate(target);
            return;
        }
        try {
            const u = new URL(target, win.location.origin);
            if (u.origin === win.location.origin) navigate(u.pathname + u.search + u.hash);
        } catch {
            // ignore malformed redirect targets
        }
    }

    // ---------- show/hide password ----------

    function bindPasswordToggle() {
        if (!$passwordToggle || !$passwordInput) return;
        $passwordToggle.addEventListener("click", () => {
            const showing = $passwordInput.type === "text";
            $passwordInput.type = showing ? "password" : "text";
            $passwordToggle.setAttribute("aria-pressed", showing ? "false" : "true");
            $passwordToggle.setAttribute(
                "aria-label",
                showing ? t("show_password") : t("hide_password")
            );
        });
    }

    // ---------- sign-in submit (Sprint 4 — JS intercepts to handle MFA) ----------

    function bindSignInSubmit() {
        if (!$form) return;
        $form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!isHttpsOrLocalhost()) {
                showError($form, t("https_required"));
                return;
            }
            await submitSignIn();
        });
    }

    async function submitSignIn() {
        clearError($form);
        const usr = $emailInput?.value || "";
        const pwd = $passwordInput?.value || "";
        const remember = $form?.querySelector("input[name='remember_me']")?.checked
            ? "1"
            : "0";

        const $submit = $form?.querySelector("button[type='submit']");
        if ($submit) {
            $submit.disabled = true;
            $submit.setAttribute("aria-busy", "true");
        }

        track("login_attempt");

        try {
            const { res, data } = await postForm("/api/method/login", {
                cmd: "login",
                usr,
                pwd,
                remember_me: remember,
            });
            await handleAuthResponse(res, data, { usr, pwd });
        } catch {
            showError($form, t("network_error"));
            track("login_failed", { failure_category: "network_error" });
        } finally {
            if ($submit) {
                $submit.disabled = false;
                $submit.removeAttribute("aria-busy");
            }
        }
    }

    /**
     * Route an /api/method/login response. Handles:
     *   - MFA challenge (verification block + tmp_id) → swap to OTP view.
     *   - Forced password reset (message === "Password Reset" + redirect_to).
     *   - 429 with Retry-After → lockout view with countdown.
     *   - Generic 4xx → bad-credentials error.
     *   - 200 success → safeRedirect to server-supplied target.
     */
    async function handleAuthResponse(res, data, ctx) {
        if (res.status === 429) {
            const retry = parseInt(res.headers?.get?.("Retry-After") || "0", 10);
            track("login_failed", { failure_category: "rate_limited" });
            beginLockout(retry);
            return;
        }

        if (!res.ok) {
            // LoginAttemptTracker fail path returns a thrown exception with no
            // Retry-After; the response message contains "locked"/"resume after"
            // (translated). We treat any 4xx with a "locked" hint as a generic
            // lockout (no countdown — server didn't supply one).
            const msg = (data?._server_messages || data?.message || "").toString();
            if (/lock|resume after/i.test(msg)) {
                track("login_failed", { failure_category: "rate_limited" });
                beginLockout(0);
                return;
            }
            showError($form, t("bad_credentials"));
            track("login_failed", {
                failure_category: classifyFailure(res, data),
            });
            return;
        }

        // 200 OK from /api/method/login. Check for MFA challenge first.
        const verification = data?.verification || data?.message?.verification;
        const tmpId = data?.tmp_id || data?.message?.tmp_id;
        if (verification && tmpId) {
            state.tmpId = tmpId;
            state.mfaMethod = verification.type || verification.method || "OTP App";
            // Stash usr+pwd so step 2 can re-POST. We do NOT persist them.
            state._pendingUsr = ctx.usr;
            state._pendingPwd = ctx.pwd;
            setView("mfa-otp");
            track("mfa_step_shown", { mfa_method: state.mfaMethod });
            return;
        }

        // Forced password reset path.
        const messageText = data?.message?.message || data?.message || "";
        if (typeof messageText === "string" && /password reset/i.test(messageText)) {
            const target = data?.message?.redirect_to || data?.redirect_to;
            if (target) safeRedirect(target);
            return;
        }

        // Plain success.
        track("login_success");
        const redirectTo = data?.redirect_to || data?.message?.redirect_to || "/helpdesk";
        safeRedirect(redirectTo);
    }

    // ---------- MFA OTP grid ----------

    function bindOtpGrid() {
        const cells = $$("[data-otp-cell]");
        if (!cells.length) return;

        cells.forEach((cell, index) => {
            cell.addEventListener("input", (event) => {
                const v = (event.target.value || "").replace(/\D/g, "").slice(-1);
                event.target.value = v;
                if (v && index < cells.length - 1) {
                    cells[index + 1].focus();
                }
                if (cells.every((c) => c.value)) {
                    submitOtp();
                }
            });

            cell.addEventListener("keydown", (event) => {
                if (event.key === "Backspace" && !event.target.value && index > 0) {
                    cells[index - 1].focus();
                    cells[index - 1].value = "";
                    event.preventDefault();
                } else if (event.key === "ArrowLeft" && index > 0) {
                    cells[index - 1].focus();
                    event.preventDefault();
                } else if (event.key === "ArrowRight" && index < cells.length - 1) {
                    cells[index + 1].focus();
                    event.preventDefault();
                }
            });

            cell.addEventListener("paste", (event) => {
                const text = (event.clipboardData?.getData("text") || "")
                    .replace(/\D/g, "")
                    .slice(0, OTP_LENGTH);
                if (!text) return;
                event.preventDefault();
                cells.forEach((c, i) => {
                    c.value = text[i] || "";
                });
                const lastFilled = Math.min(text.length, OTP_LENGTH) - 1;
                if (lastFilled >= 0) cells[Math.min(lastFilled, cells.length - 1)].focus();
                if (text.length === OTP_LENGTH) submitOtp();
            });
        });

        const $resend = $("[data-resend-otp]");
        if ($resend) {
            $resend.addEventListener("click", async (event) => {
                event.preventDefault();
                if ($resend.disabled) return;
                $resend.disabled = true;
                track("mfa_resend_requested", { mfa_method: state.mfaMethod });
                const TOTAL = 30;
                let remaining = TOTAL;
                if (prefersReducedMotion()) {
                    // Sprint 6 — no per-second ticking on reduced-motion. The
                    // button shows a single "wait" state and re-enables after
                    // the full window. (Same gate, just no animated count.)
                    $resend.textContent = t("resend_in", { seconds: TOTAL });
                    setTimeout(() => {
                        $resend.disabled = false;
                        $resend.textContent = t("resend_code");
                    }, TOTAL * 1000);
                } else {
                    $resend.textContent = t("resend_in", { seconds: remaining });
                    state.countdownTimer = setInterval(() => {
                        remaining -= 1;
                        if (remaining <= 0) {
                            clearInterval(state.countdownTimer);
                            state.countdownTimer = null;
                            $resend.disabled = false;
                            $resend.textContent = t("resend_code");
                            return;
                        }
                        $resend.textContent = t("resend_in", { seconds: remaining });
                    }, 1000);
                }
                // Trigger fresh challenge by re-POSTing primary auth.
                await postForm("/api/method/login", {
                    cmd: "login",
                    usr: state._pendingUsr || "",
                    pwd: state._pendingPwd || "",
                });
            });
        }
    }

    async function submitOtp() {
        const cells = $$("[data-otp-cell]");
        const otp = cells.map((c) => c.value).join("");
        if (otp.length !== OTP_LENGTH) return;
        if (!state.tmpId) {
            showError($("[data-view='mfa-otp']"), t("network_error"));
            return;
        }

        const $otpScope = $("[data-view='mfa-otp']");
        clearError($otpScope);

        try {
            const { res, data } = await postForm("/api/method/login", {
                cmd: "login",
                usr: state._pendingUsr || "",
                pwd: state._pendingPwd || "",
                otp,
                tmp_id: state.tmpId,
            });

            if (res.status === 429) {
                const retry = parseInt(res.headers?.get?.("Retry-After") || "0", 10);
                track("mfa_failed", { failure_category: "rate_limited" });
                beginLockout(retry);
                return;
            }

            if (!res.ok) {
                showError($otpScope, t("bad_otp"));
                cells.forEach((c) => (c.value = ""));
                cells[0]?.focus();
                track("mfa_failed", {
                    failure_category: classifyFailure(res, data),
                });
                return;
            }

            // Success: clear sensitive state and redirect.
            track("mfa_success", { mfa_method: state.mfaMethod });
            state.tmpId = null;
            state.mfaMethod = null;
            state._pendingUsr = null;
            state._pendingPwd = null;
            const redirectTo = data?.redirect_to || data?.message?.redirect_to || "/helpdesk";
            safeRedirect(redirectTo);
        } catch {
            showError($otpScope, t("network_error"));
            track("mfa_failed", { failure_category: "network_error" });
        }
    }

    // ---------- lockout ----------

    function beginLockout(seconds) {
        track("lockout_triggered");
        clearLockoutTimer();
        if (seconds > 0) {
            state.lockoutUntil = Date.now() + seconds * 1000;
            renderLockout(seconds);
            state.countdownTimer = setInterval(() => {
                const remaining = Math.ceil((state.lockoutUntil - Date.now()) / 1000);
                if (remaining <= 0) {
                    clearLockoutTimer();
                    setView("sign-in");
                    return;
                }
                renderLockout(remaining);
            }, 1000);
        } else {
            renderLockout(0);
        }
        setView("locked-out");
    }

    function renderLockout(remaining) {
        const $msg = $("[data-lockout-message]");
        if (!$msg) return;
        $msg.textContent =
            remaining > 0
                ? t("locked_out_countdown", { seconds: remaining })
                : t("locked_out");
    }

    function clearLockoutTimer() {
        if (state.countdownTimer) {
            clearInterval(state.countdownTimer);
            state.countdownTimer = null;
        }
    }

    // ---------- forced password change (FR-AU-04) ----------

    function bindNewPasswordForm() {
        const $form = $("[data-view-form='new-password']");
        if (!$form) return;
        $form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const $newPwd = $form.querySelector("[name='new_password']");
            const $confirmPwd = $form.querySelector("[name='confirm_password']");
            const newPwd = $newPwd?.value || "";
            const confirmPwd = $confirmPwd?.value || "";
            clearError($form);

            if (newPwd !== confirmPwd) {
                showError($form, t("passwords_dont_match"));
                return;
            }

            // Frappe's update_password endpoint takes {key, new_password} where
            // `key` comes from the reset link in the email. For forced first-login
            // change, the server includes a token in the redirect_to URL we
            // received. Sprint 4 wires the form, but the redirect-link key flow
            // is naturally driven by the redirect target, so we just submit the
            // form and follow the response.
            const $submit = $form.querySelector("button[type='submit']");
            if ($submit) $submit.disabled = true;
            try {
                const { res, data } = await postForm(
                    "/api/method/frappe.core.doctype.user.user.update_password",
                    { new_password: newPwd, key: state._resetKey || "" }
                );
                if (res.ok) {
                    safeRedirect("/login_preview?password_reset=1");
                } else {
                    showError($form, data?.message || t("network_error"));
                }
            } catch {
                showError($form, t("network_error"));
            } finally {
                if ($submit) $submit.disabled = false;
            }
        });
    }

    // ---------- forgot password ----------

    function bindForgot() {
        if (!$forgotLink) return;
        $forgotLink.addEventListener("click", (event) => {
            event.preventDefault();
            track("forgot_password_clicked");
            // Carry the email value across the swap.
            state.lastEmail = $emailInput?.value || "";
            setView("forgot");
            const $forgotEmail = $("[data-view='forgot'] input[type='email']");
            if ($forgotEmail) $forgotEmail.value = state.lastEmail;
        });

        const $forgotForm = $("[data-view-form='forgot']");
        const $backLink = $("[data-back-to-signin]");

        if ($backLink) {
            $backLink.addEventListener("click", (event) => {
                event.preventDefault();
                setView("sign-in");
            });
        }

        if ($forgotForm) {
            $forgotForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                const $emailField = $forgotForm.querySelector("input[type='email']");
                const email = $emailField ? $emailField.value : "";
                const $submit = $forgotForm.querySelector("button[type='submit']");
                if ($submit) $submit.disabled = true;
                clearError($forgotForm);

                try {
                    await postForm(
                        "/api/method/helpdesk.api.forgot_password.request_reset",
                        { user: email }
                    );
                    // Privacy-preserving: always show success, regardless of result.
                    // Telemetry is therefore non-leaky too (no failure_category
                    // attached) — see FR-PR-02 / FR-TEL-01 §3.
                    track("reset_link_requested");
                    setView("reset-success");
                } catch {
                    // Even on network error we show success to avoid enumeration.
                    track("reset_link_requested");
                    setView("reset-success");
                } finally {
                    if ($submit) $submit.disabled = false;
                }
            });
        }
    }

    // ---------- post-reset banner ----------

    function maybeShowPostResetBanner() {
        const params = new URLSearchParams(win.location.search);
        if (params.get("password_reset") !== "1") return;
        const $banner = $("[data-post-reset-banner]");
        if ($banner) {
            $banner.hidden = false;
            // Auto-dismiss after 8s or first form interaction.
            const dismiss = () => {
                $banner.hidden = true;
                $form?.removeEventListener("focusin", dismiss);
            };
            setTimeout(dismiss, 8000);
            $form?.addEventListener("focusin", dismiss, { once: true });
        }
        // Strip the param so the banner doesn't reappear on hash changes.
        const url = new URL(win.location.href);
        url.searchParams.delete("password_reset");
        win.history.replaceState(null, "", url.pathname + url.search);
    }

    // ---------- error / status ----------

    function showError(scope, message) {
        const $err = scope.querySelector("[data-error]");
        if (!$err) return;
        $err.textContent = message;
        $err.hidden = false;
        // Sprint 6 — flag the inputs in this scope as invalid so AT users
        // hear "invalid entry" when they revisit the field.
        scope
            .querySelectorAll("input[aria-describedby]")
            .forEach((input) => input.setAttribute("aria-invalid", "true"));
    }

    function clearError(scope) {
        const $err = scope.querySelector("[data-error]");
        if ($err) {
            $err.textContent = "";
            $err.hidden = true;
        }
        scope
            .querySelectorAll("input[aria-describedby]")
            .forEach((input) => input.setAttribute("aria-invalid", "false"));
    }

    // ---------- hash sync ----------

    function syncFromHash() {
        if (win.location.hash === "#forgot") {
            setView("forgot");
        }
    }

    // ---------- telemetry boot ----------

    /**
     * If the page wants telemetry but posthog.js hasn't been loaded yet,
     * fetch it from the framework's bundled copy and initialise. This runs
     * exactly once per page load. The script tag carries no nonce because
     * the source URL is same-origin (CSP `script-src 'self'` covers it).
     */
    function ensurePosthogLoaded() {
        if (!telemetryConfig.enabled) return;
        if (win.posthog && typeof win.posthog.capture === "function") return;
        const doc = root.ownerDocument;
        if (!doc) return;
        if (doc.querySelector("script[data-hd-posthog]")) return;
        const script = doc.createElement("script");
        script.src = "/assets/frappe/js/lib/posthog.js";
        script.async = true;
        script.defer = true;
        script.dataset.hdPosthog = "1";
        script.addEventListener("load", () => {
            const ph = win.posthog;
            if (ph && typeof ph.init === "function") {
                try {
                    ph.init(telemetryConfig.posthog_project_id, {
                        api_host: telemetryConfig.posthog_host,
                        // Login surface runs pre-auth; identify nothing.
                        capture_pageview: false,
                        autocapture: false,
                        disable_session_recording: true,
                        persistence: "memory",
                    });
                    track("login_page_view");
                } catch {
                    // posthog init failures must never break the auth flow.
                }
            }
        });
        doc.head.appendChild(script);
    }

    // ---------- boot ----------

    function init() {
        bindPasswordToggle();
        bindSignInSubmit();
        bindOtpGrid();
        bindNewPasswordForm();
        bindForgot();
        maybeShowPostResetBanner();
        syncFromHash();
        win.addEventListener("hashchange", () => {
            const target = win.location.hash === "#forgot" ? "forgot" : "sign-in";
            if (state.view !== target) setView(target);
        });
        ensurePosthogLoaded();
        // If posthog was already on the page (e.g., the desk app loaded it
        // earlier in the same tab), fire the page-view directly.
        if (win.posthog && typeof win.posthog.capture === "function") {
            track("login_page_view");
        }
    }

    init();

    // Public surface for tests.
    return {
        get view() {
            return state.view;
        },
        get tmpId() {
            return state.tmpId;
        },
        get mfaMethod() {
            return state.mfaMethod;
        },
        setView,
        postForm,
        safeRedirect,
        isHttpsOrLocalhost,
        csrfToken,
        // Sprint 4 surfaces — exposed for tests.
        handleAuthResponse,
        beginLockout,
        submitOtp,
        // Sprint 6 surfaces — exposed for tests.
        t,
        prefersReducedMotion,
        // Sprint 7 surfaces — exposed for tests.
        track,
        classifyFailure,
        telemetryConfig,
    };
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
    // Module scripts execute after DOMContentLoaded has already fired, so a
    // plain `addEventListener("DOMContentLoaded", ...)` here would register a
    // listener for an event that already happened and the callback would
    // never run. Boot synchronously when the DOM is already ready; otherwise
    // wait. (Same race that defer-with-async script tags hit.)
    const boot = () => {
        const root = document.querySelector(".hd-login");
        if (root) createLoginController(root);
    };
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
}
