// Copyright (c) 2023, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Ticket", {
  onload(frm) {
    if (frm.is_new()) return;
    frm.call("mark_seen");
    apply_itil_mode(frm);
  },

  refresh(frm) {
    apply_itil_mode(frm);
  },

  impact(frm) {
    update_priority_read_only(frm);
  },

  urgency(frm) {
    update_priority_read_only(frm);
  },
});

function apply_itil_mode(frm) {
  frappe.db.get_single_value("HD Settings", "itil_mode_enabled").then((itil_mode_enabled) => {
    const itil_fields = ["impact", "urgency", "category", "sub_category"];

    if (itil_mode_enabled) {
      // ITIL Mode: show ITIL fields
      itil_fields.forEach((field) => {
        frm.set_df_property(field, "hidden", 0);
      });
      // Priority is read-only only when both impact and urgency are set (AC #3, #6)
      update_priority_read_only(frm);
    } else {
      // Simple Mode: hide ITIL fields, priority is editable
      itil_fields.forEach((field) => {
        frm.set_df_property(field, "hidden", 1);
      });
      frm.set_df_property("priority", "read_only", 0);
    }

    frm.refresh_fields(["priority", ...itil_fields]);
  });
}

/**
 * Make priority read-only when ITIL matrix applies (both impact AND urgency are set).
 * Legacy tickets with empty impact/urgency retain editable priority (AC #6).
 */
function update_priority_read_only(frm) {
  const matrix_active = frm.doc.impact && frm.doc.urgency;
  frm.set_df_property("priority", "read_only", matrix_active ? 1 : 0);
  frm.refresh_field("priority");
}
