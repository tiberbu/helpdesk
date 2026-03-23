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
});

function apply_itil_mode(frm) {
  frappe.db.get_single_value("HD Settings", "itil_mode_enabled").then((itil_mode_enabled) => {
    const itil_fields = ["impact", "urgency", "category", "sub_category"];

    if (itil_mode_enabled) {
      // ITIL Mode: show ITIL fields, make priority read-only (auto-calculated)
      itil_fields.forEach((field) => {
        frm.set_df_property(field, "hidden", 0);
      });
      frm.set_df_property("priority", "read_only", 1);
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
