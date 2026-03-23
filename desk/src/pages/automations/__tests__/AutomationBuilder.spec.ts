import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";

// vi.mock is hoisted — do NOT reference outer variables inside factories
vi.mock("frappe-ui", () => ({
  Badge: { template: "<span>{{ label }}<slot /></span>", props: ["label", "theme", "variant"] },
  Button: {
    template: "<button @click=\"$emit('click')\">{{ label }}<slot name='prefix' /></button>",
    props: ["variant", "label", "loading", "disabled"],
    emits: ["click"],
  },
  Dialog: {
    template: "<div v-if='modelValue'><slot name='body-content' /></div>",
    props: ["modelValue", "options"],
    emits: ["update:modelValue"],
  },
  FormControl: {
    template: "<input :value='modelValue' @input=\"$emit('update:modelValue', $event.target.value)\" />",
    props: ["type", "modelValue", "placeholder", "rows"],
    emits: ["update:modelValue"],
  },
  LoadingIndicator: { template: "<div class='loading' />" },
  call: vi.fn(),
  usePageMeta: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRoute: vi.fn(() => ({ params: { id: "new" } })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({ isAdmin: true })),
}));

vi.mock("@/translation", () => ({ __: (s: string) => s }));

vi.mock("@/components/automation/RuleTriggerSelect.vue", () => ({
  default: {
    template: "<div data-testid='trigger-select' />",
    props: ["modelValue"],
    emits: ["update:modelValue"],
  },
}));

vi.mock("@/components/automation/RuleConditionBuilder.vue", () => ({
  default: {
    template: "<div data-testid='condition-builder' />",
    props: ["modelValue"],
    emits: ["update:modelValue"],
  },
}));

vi.mock("@/components/automation/RuleActionList.vue", () => ({
  default: {
    template: "<div data-testid='action-list' />",
    props: ["modelValue"],
    emits: ["update:modelValue"],
  },
}));

// Import AFTER mocks are established
import AutomationBuilder from "../AutomationBuilder.vue";
import { call } from "frappe-ui";
import { useRoute, useRouter } from "vue-router";

const mockCall = call as ReturnType<typeof vi.fn>;
const mockUseRoute = useRoute as ReturnType<typeof vi.fn>;
const mockUseRouter = useRouter as ReturnType<typeof vi.fn>;

describe("AutomationBuilder — new rule", () => {
  beforeEach(() => {
    mockCall.mockReset();
    mockUseRoute.mockReturnValue({ params: { id: "new" } });
    mockUseRouter.mockReturnValue({ push: vi.fn() });
  });

  it("renders breadcrumb with 'New Rule'", () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    expect(wrapper.text()).toContain("New Rule");
    expect(wrapper.text()).toContain("Automation Rules");
  });

  it("renders WHEN / IF / THEN section labels", () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    expect(wrapper.text()).toContain("Trigger");
    expect(wrapper.text()).toContain("Conditions");
    expect(wrapper.text()).toContain("Actions");
  });

  it("does not show Test Rule button for new rules", () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    expect(wrapper.text()).not.toContain("Test Rule");
  });

  it("shows Save button", () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    expect(wrapper.text()).toContain("Save");
  });

  it("alerts validation when saving without rule name", async () => {
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    const saveBtn = wrapper.findAll("button").find((b) => b.text().includes("Save"));
    await saveBtn?.trigger("click");
    expect(alertSpy).toHaveBeenCalledWith("Rule name is required.");
    alertSpy.mockRestore();
  });

  it("calls frappe.client.insert when saving a valid new rule", async () => {
    mockCall.mockResolvedValue({});
    const wrapper = mount(AutomationBuilder, { props: { id: "new" } });
    const vm = wrapper.vm as any;
    vm.formState.rule_name = "Test Rule";
    vm.formState.trigger_type = "ticket_created";
    vm.actionsState = [{ type: "set_priority", value: "High" }];
    await wrapper.vm.$nextTick();

    const saveBtn = wrapper.findAll("button").find((b) => b.text().includes("Save"));
    await saveBtn?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(mockCall).toHaveBeenCalledWith(
      "frappe.client.insert",
      expect.objectContaining({
        doc: expect.objectContaining({ doctype: "HD Automation Rule", rule_name: "Test Rule" }),
      })
    );
  });
});

describe("AutomationBuilder — existing rule", () => {
  const existingRule = {
    rule_name: "Escalate Urgent",
    description: "Escalates urgent tickets",
    trigger_type: "ticket_created",
    priority_order: 10,
    enabled: 1,
    failure_count: 0,
    conditions: "[]",
    actions: '[{"type":"set_priority","value":"High"}]',
  };

  beforeEach(() => {
    mockCall.mockReset();
    mockUseRoute.mockReturnValue({ params: { id: "Escalate-Urgent" } });
    mockCall.mockResolvedValue(existingRule);
  });

  it("shows Test Rule button for existing rules", async () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "Escalate-Urgent" } });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("Test Rule");
  });

  it("shows rule name in breadcrumb after load", async () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "Escalate-Urgent" } });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("Escalate Urgent");
  });

  it("displays 'Rule WOULD fire' in test modal when testResult.would_fire is true", async () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "Escalate-Urgent" } });
    await wrapper.vm.$nextTick();

    const vm = wrapper.vm as any;
    vm.showTestModal = true;
    vm.testTicketId = "HD-0001";
    vm.testResult = {
      would_fire: true,
      conditions: [],
      actions: [{ type: "set_priority", value: "High", would_execute: true }],
    };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Rule WOULD fire");
  });

  it("displays 'Rule would NOT fire' in test modal when testResult.would_fire is false", async () => {
    const wrapper = mount(AutomationBuilder, { props: { id: "Escalate-Urgent" } });
    await wrapper.vm.$nextTick();

    const vm = wrapper.vm as any;
    vm.showTestModal = true;
    vm.testResult = {
      would_fire: false,
      conditions: [{ field: "priority", operator: "equals", value: "Low", matched: false }],
      actions: [],
    };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Rule would NOT fire");
  });
});
