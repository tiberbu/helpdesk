import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";

const mockRules = [
  { name: "RULE-001", rule_name: "Escalate Urgent", trigger_type: "ticket_created", enabled: 1, priority_order: 10, failure_count: 0 },
  { name: "RULE-002", rule_name: "SLA Alert", trigger_type: "sla_breached", enabled: 0, priority_order: 20, failure_count: 0 },
];

vi.mock("frappe-ui", () => ({
  Badge: { template: "<span>{{ label }}<slot /></span>", props: ["label", "theme", "variant"] },
  Button: {
    template: "<button @click=\"$emit('click')\">{{ label }}<slot name='prefix' /></button>",
    props: ["variant", "size", "label", "loading", "title"],
    emits: ["click"],
  },
  LoadingIndicator: { template: "<div class='loading' />" },
  createListResource: vi.fn(() => ({
    data: mockRules,
    loading: false,
    reload: vi.fn(),
  })),
  call: vi.fn().mockResolvedValue({}),
  usePageMeta: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({ isAdmin: true })),
}));

vi.mock("@/translation", () => ({ __: (s: string) => s }));

// Import AFTER mocks are established
import AutomationList from "../AutomationList.vue";
import { useAuthStore } from "@/stores/auth";

const mockUseAuthStore = useAuthStore as ReturnType<typeof vi.fn>;

describe("AutomationList", () => {
  beforeEach(() => {
    mockUseAuthStore.mockReturnValue({ isAdmin: true });
  });

  it("renders the page title", () => {
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("Automation Rules");
  });

  it("renders rule names from the list", () => {
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("Escalate Urgent");
    expect(wrapper.text()).toContain("SLA Alert");
  });

  it("shows New Rule button for admin", () => {
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("New Rule");
  });

  it("shows access denied state for non-admin", () => {
    mockUseAuthStore.mockReturnValueOnce({ isAdmin: false });
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("Access Restricted");
    expect(wrapper.text()).toContain("Only administrators");
  });

  it("shows trigger badges for each rule", () => {
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("Ticket Created");
    expect(wrapper.text()).toContain("SLA Breached");
  });

  it("renders enabled checkboxes for each rule", () => {
    const wrapper = mount(AutomationList);
    const checkboxes = wrapper.findAll("input[type='checkbox']");
    expect(checkboxes).toHaveLength(mockRules.length);
  });

  it("shows priority order values", () => {
    const wrapper = mount(AutomationList);
    expect(wrapper.text()).toContain("10");
    expect(wrapper.text()).toContain("20");
  });
});
