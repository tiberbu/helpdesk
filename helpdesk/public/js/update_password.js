/*
 * Helpdesk Redesigned /update-password — controller module.
 *
 * Companion to login.js. Single ES module, no framework, no third-party
 * imports. Loaded by helpdesk/www/update_password.html (when the redesigned
 * page is enabled via HD Settings.new_login_page_enabled).
 *
 * Posts to frappe.core.doctype.user.user.update_password — same server
 * endpoint as the framework's update-password page — and on success
 * redirects to /login?password_reset=1 so the redesigned login banner picks
 * it up.
 */

const STRINGS = {
    show_password: "Show password",
    hide_password: "Hide password",
    passwords_dont_match: "Passwords don't match.",
    too_short: "Password must be at least 8 characters.",
    too_weak:
        "Pick a stronger password — mix letters, digits, and symbols.",
    invalid_link:
        "This reset link is invalid or has expired. Please request a new one.",
    network_error:
        "Couldn't reach the server. Check your connection and try again.",
    generic_error: "Something went wrong. Please try again.",
    submitting: "Updating…",
    success: "Password updated. Redirecting you to sign in…",
};

const MIN_LEN = 8;

export function createUpdatePasswordController(root, options = {}) {
    const win = options.window ?? window;
    const fetchImpl = options.fetch ?? win.fetch.bind(win);
    const navigate = options.navigate ?? ((url) => (win.location.href = url));

    const $ = (sel) => root.querySelector(sel);
    const $$ = (sel) => Array.from(root.querySelectorAll(sel));

    const $form = $("[data-view-form='update-password']");
    const $err = $("[data-error]");
    const $newPwd = $("#hd-update-new-password");
    const $confirmPwd = $("#hd-update-confirm-password");
    const $oldPwd = $("#hd-update-old-password");

    function csrfToken() {
        const meta = root.ownerDocument.querySelector(
            'meta[name="csrf-token"]'
        );
        return meta ? meta.content : "";
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
            // non-JSON — leave data null
        }
        return { res, data };
    }

    function showError(message) {
        if (!$err) return;
        $err.textContent = message;
        $err.hidden = false;
        // Mark each input that describes the same error region as invalid so
        // AT users hear "invalid entry" the next time they focus the field.
        root.querySelectorAll("input[aria-describedby]").forEach((input) => {
            if (input.getAttribute("aria-describedby")?.includes("hd-update-error")) {
                input.setAttribute("aria-invalid", "true");
            }
        });
    }

    function clearError() {
        if (!$err) return;
        $err.textContent = "";
        $err.hidden = true;
        root.querySelectorAll("input[aria-describedby]").forEach((input) => {
            if (input.getAttribute("aria-describedby")?.includes("hd-update-error")) {
                input.setAttribute("aria-invalid", "false");
            }
        });
    }

    function bindPasswordToggles() {
        $$("[data-toggle-password]").forEach((btn) => {
            const targetId = btn.getAttribute("data-toggle-password");
            const target = root.querySelector(`#${targetId}`);
            if (!target) return;
            btn.addEventListener("click", () => {
                const showing = target.type === "text";
                target.type = showing ? "password" : "text";
                btn.setAttribute("aria-pressed", showing ? "false" : "true");
                btn.setAttribute(
                    "aria-label",
                    showing ? STRINGS.show_password : STRINGS.hide_password
                );
            });
        });
    }

    function validate(values) {
        if (!values.new_password || !values.confirm_password) {
            return STRINGS.generic_error;
        }
        if (values.new_password.length < MIN_LEN) {
            return STRINGS.too_short;
        }
        if (values.new_password !== values.confirm_password) {
            return STRINGS.passwords_dont_match;
        }
        return null;
    }

    function bindSubmit() {
        if (!$form) return;
        $form.addEventListener("submit", async (event) => {
            event.preventDefault();
            clearError();

            const formData = new FormData($form);
            const values = {
                key: formData.get("key") || "",
                old_password: formData.get("old_password") || "",
                new_password: formData.get("new_password") || "",
                confirm_password: formData.get("confirm_password") || "",
                logout_all_sessions: formData.get("logout_all_sessions") || "1",
            };

            const validationMsg = validate(values);
            if (validationMsg) {
                showError(validationMsg);
                return;
            }

            const $submit = $form.querySelector("button[type='submit']");
            const originalLabel = $submit?.textContent;
            if ($submit) {
                $submit.disabled = true;
                $submit.setAttribute("aria-busy", "true");
                $submit.textContent = STRINGS.submitting;
            }

            try {
                const { res, data } = await postForm(
                    "/api/method/frappe.core.doctype.user.user.update_password",
                    values
                );
                if (res.ok) {
                    showSuccess();
                    return;
                }
                if (res.status === 410) {
                    showError(
                        (data && data.message) || STRINGS.invalid_link
                    );
                } else if (res.status === 401) {
                    showError(STRINGS.generic_error);
                } else {
                    const msg =
                        (data && (data.message || data._server_messages)) ||
                        STRINGS.generic_error;
                    showError(typeof msg === "string" ? msg : STRINGS.generic_error);
                }
            } catch {
                showError(STRINGS.network_error);
            } finally {
                if ($submit) {
                    $submit.disabled = false;
                    $submit.removeAttribute("aria-busy");
                    if (originalLabel) $submit.textContent = originalLabel;
                }
            }
        });
    }

    function showSuccess() {
        const $form_view = $("[data-view='update-password']");
        const $success_view = $("[data-view='update-success']");
        if ($form_view) $form_view.hidden = true;
        if ($success_view) $success_view.hidden = false;
        // Land on the redesigned login with a confirmation banner.
        win.setTimeout(() => navigate("/login?password_reset=1"), 1500);
    }

    function init() {
        bindPasswordToggles();
        bindSubmit();
    }

    init();

    return {
        postForm,
        validate,
        showError,
        clearError,
    };
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
    const boot = () => {
        const root = document.querySelector(".hd-login");
        if (root) createUpdatePasswordController(root);
    };
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
}
