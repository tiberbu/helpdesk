import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import RuleConditionBuilder from "../RuleConditionBuilder.vue";

const empty = { logic: "AND", conditions: [] as any[] };

describe("RuleConditionBuilder — empty state", () => {
  it("shows empty state message and Add Condition button", () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: empty } });
    expect(wrapper.text()).toContain("No conditions");
    expect(wrapper.text()).toContain("Add Condition");
  });

  it("emits a new default condition when Add Condition is clicked", async () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: empty } });
    // The Add Condition button is the last (and only) button
    const addBtn = wrapper.find("button");
    await addBtn.trigger("click");
    await wrapper.vm.$nextTick();
    const emitted = wrapper.emitted("update:modelValue");
    expect(emitted).toBeTruthy();
    const payload = emitted![0][0] as any;
    expect(payload.conditions).toHaveLength(1);
    expect(payload.conditions[0]).toMatchObject({ field: "", operator: "equals", value: "" });
  });
});

describe("RuleConditionBuilder — single condition", () => {
  const singleModel = {
    logic: "AND",
    conditions: [{ field: "priority", operator: "equals", value: "High" }],
  };

  it("does not show AND/OR toggle with one condition", () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: singleModel } });
    // Toggle section is hidden when conditions.length <= 1
    expect(wrapper.text()).not.toContain("Match");
  });

  it("shows value input for 'equals' operator", () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: singleModel } });
    // The value FormControl renders as <input> (not hidden)
    const inputs = wrapper.findAll("input");
    // At least one input visible (the value input)
    expect(inputs.length).toBeGreaterThan(0);
  });

  it("hides value input for is_set operator and shows placeholder text", () => {
    const model = {
      logic: "AND",
      conditions: [{ field: "priority", operator: "is_set", value: "" }],
    };
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: model } });
    expect(wrapper.text()).toContain("no value needed");
  });

  it("hides value input for is_not_set operator", () => {
    const model = {
      logic: "AND",
      conditions: [{ field: "priority", operator: "is_not_set", value: "" }],
    };
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: model } });
    expect(wrapper.text()).toContain("no value needed");
  });

  it("emits removal when remove button is clicked", async () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: singleModel } });
    const removeBtn = wrapper.find("button[title='Remove condition']");
    expect(removeBtn.exists()).toBe(true);
    await removeBtn.trigger("click");
    await wrapper.vm.$nextTick();
    const emitted = wrapper.emitted("update:modelValue");
    expect(emitted).toBeTruthy();
    const payload = emitted![0][0] as any;
    expect(payload.conditions).toHaveLength(0);
  });
});

describe("RuleConditionBuilder — multiple conditions", () => {
  const multiModel = {
    logic: "AND",
    conditions: [
      { field: "priority", operator: "equals", value: "High" },
      { field: "status", operator: "equals", value: "Open" },
    ],
  };

  it("shows ALL/ANY toggle when more than one condition exists", () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: multiModel } });
    expect(wrapper.text()).toContain("Match");
    expect(wrapper.text()).toContain("ALL");
    expect(wrapper.text()).toContain("ANY");
  });

  it("shows AND label between conditions", () => {
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: multiModel } });
    expect(wrapper.text()).toContain("AND");
  });

  it("shows OR label when logicOperator is OR", async () => {
    const model = { logic: "OR", conditions: multiModel.conditions };
    const wrapper = mount(RuleConditionBuilder, { props: { modelValue: model } });
    expect(wrapper.text()).toContain("OR");
  });
});
