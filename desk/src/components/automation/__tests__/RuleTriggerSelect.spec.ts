import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import RuleTriggerSelect from "../RuleTriggerSelect.vue";
import { TRIGGER_OPTIONS } from "../triggerOptions";

describe("RuleTriggerSelect", () => {
  it("exports at least 10 trigger options", () => {
    expect(TRIGGER_OPTIONS.length).toBeGreaterThanOrEqual(10);
  });

  it("renders labels for all triggers", () => {
    const wrapper = mount(RuleTriggerSelect, { props: { modelValue: "" } });
    expect(wrapper.text()).toContain("Ticket Created");
    expect(wrapper.text()).toContain("SLA Breached");
    expect(wrapper.text()).toContain("CSAT Response Received");
    expect(wrapper.text()).toContain("Chat Started");
    expect(wrapper.text()).toContain("Chat Ended");
  });

  it("renders one clickable card per trigger option", () => {
    const wrapper = mount(RuleTriggerSelect, { props: { modelValue: "" } });
    // Each trigger card is a div with cursor-pointer class
    const cards = wrapper.findAll(".cursor-pointer");
    expect(cards.length).toBe(TRIGGER_OPTIONS.length);
  });

  it("highlights the selected trigger with blue border", () => {
    const wrapper = mount(RuleTriggerSelect, {
      props: { modelValue: "ticket_created" },
    });
    const selected = wrapper.find(".border-blue-500");
    expect(selected.exists()).toBe(true);
    expect(selected.text()).toContain("Ticket Created");
  });

  it("does not highlight any card when nothing is selected", () => {
    const wrapper = mount(RuleTriggerSelect, { props: { modelValue: "" } });
    expect(wrapper.find(".border-blue-500").exists()).toBe(false);
  });

  it("emits update:modelValue with the trigger value when a card is clicked", async () => {
    const wrapper = mount(RuleTriggerSelect, { props: { modelValue: "" } });
    const firstCard = wrapper.findAll(".cursor-pointer")[0];
    await firstCard.trigger("click");
    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    expect(wrapper.emitted("update:modelValue")![0][0]).toBe(TRIGGER_OPTIONS[0].value);
  });

  it("emits the correct value for any trigger card", async () => {
    const wrapper = mount(RuleTriggerSelect, { props: { modelValue: "" } });
    const slaCard = wrapper.findAll(".cursor-pointer").find((c) =>
      c.text().includes("SLA Breached")
    );
    expect(slaCard).toBeDefined();
    await slaCard!.trigger("click");
    expect(wrapper.emitted("update:modelValue")![0][0]).toBe("sla_breached");
  });
});
