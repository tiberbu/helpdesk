import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import RuleActionList from "../RuleActionList.vue";
import { ACTION_OPTIONS } from "../actionOptions";

describe("RuleActionList — exports", () => {
  it("exports at least 10 action types", () => {
    expect(ACTION_OPTIONS.length).toBeGreaterThanOrEqual(10);
  });

  it("includes the required core action types", () => {
    const values = ACTION_OPTIONS.map((a) => a.value);
    expect(values).toContain("assign_to_agent");
    expect(values).toContain("assign_to_team");
    expect(values).toContain("set_priority");
    expect(values).toContain("set_status");
    expect(values).toContain("send_email");
    expect(values).toContain("add_internal_note");
    expect(values).toContain("trigger_webhook");
  });
});

describe("RuleActionList — empty state", () => {
  it("shows empty state message and Add Action button", () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: [] } });
    expect(wrapper.text()).toContain("Add at least one action");
    expect(wrapper.text()).toContain("Add Action");
  });

  it("emits a new default action when Add Action is clicked", async () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: [] } });
    const addBtn = wrapper.find("button");
    await addBtn.trigger("click");
    await wrapper.vm.$nextTick();
    const emitted = wrapper.emitted("update:modelValue");
    expect(emitted).toBeTruthy();
    const payload = emitted![0][0] as any[];
    expect(payload).toHaveLength(1);
    expect(payload[0]).toMatchObject({ type: "", value: "" });
  });
});

describe("RuleActionList — with actions", () => {
  const twoActions = [
    { type: "set_priority", value: "High" },
    { type: "assign_to_team", value: "Support" },
  ];

  it("shows move up/down buttons when multiple actions exist", () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: twoActions } });
    expect(wrapper.find("button[title='Move up']").exists()).toBe(true);
    expect(wrapper.find("button[title='Move down']").exists()).toBe(true);
  });

  it("shows remove button for each action", () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: twoActions } });
    const removeBtns = wrapper.findAll("button[title='Remove action']");
    expect(removeBtns).toHaveLength(2);
  });

  it("emits removal when remove button is clicked", async () => {
    const wrapper = mount(RuleActionList, {
      props: { modelValue: [{ type: "set_priority", value: "High" }] },
    });
    const removeBtn = wrapper.find("button[title='Remove action']");
    await removeBtn.trigger("click");
    await wrapper.vm.$nextTick();
    const emitted = wrapper.emitted("update:modelValue");
    expect(emitted).toBeTruthy();
    expect(emitted![0][0]).toHaveLength(0);
  });

  it("first action has move-up disabled", () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: twoActions } });
    const moveUpBtns = wrapper.findAll("button[title='Move up']");
    expect(moveUpBtns[0].attributes("disabled")).toBeDefined();
  });

  it("last action has move-down disabled", () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: twoActions } });
    const moveDownBtns = wrapper.findAll("button[title='Move down']");
    expect(moveDownBtns[moveDownBtns.length - 1].attributes("disabled")).toBeDefined();
  });

  it("emits reordered actions when move-down is clicked on first item", async () => {
    const wrapper = mount(RuleActionList, { props: { modelValue: twoActions } });
    const moveDownBtns = wrapper.findAll("button[title='Move down']");
    await moveDownBtns[0].trigger("click");
    await wrapper.vm.$nextTick();
    const emitted = wrapper.emitted("update:modelValue");
    expect(emitted).toBeTruthy();
    const payload = emitted![0][0] as any[];
    // First and second are swapped
    expect(payload[0].type).toBe("assign_to_team");
    expect(payload[1].type).toBe("set_priority");
  });
});
