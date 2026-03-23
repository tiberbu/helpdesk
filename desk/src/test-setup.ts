import { vi } from "vitest";

// Mock frappe-ui — provide stub components and utilities globally
vi.mock("frappe-ui", () => ({
  Badge: {
    template: "<span>{{ label }}<slot /></span>",
    props: ["label", "theme", "variant", "size"],
  },
  Button: {
    template: "<button @click=\"$emit('click')\">{{ label }}<slot name='prefix' /><slot /></button>",
    props: ["variant", "size", "label", "loading", "disabled", "title"],
    emits: ["click"],
  },
  Dialog: {
    template: "<div v-if='modelValue'><slot name='body-content' /></div>",
    props: ["modelValue", "options"],
    emits: ["update:modelValue"],
  },
  FormControl: {
    template: "<input :type=\"type || 'text'\" :value='modelValue' @input=\"$emit('update:modelValue', $event.target.value)\" @change=\"$emit('change', $event)\" />",
    props: ["type", "modelValue", "value", "placeholder", "rows", "options"],
    emits: ["update:modelValue", "change"],
  },
  LoadingIndicator: { template: "<div class='loading' />" },
  createListResource: vi.fn(() => ({
    data: [],
    loading: false,
    reload: vi.fn(),
  })),
  call: vi.fn(),
  usePageMeta: vi.fn(),
}));

// Mock vue-router
vi.mock("vue-router", () => ({
  useRoute: vi.fn(() => ({ params: { id: "new" } })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}));

// Mock auth store
vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    isAdmin: true,
    isAgent: true,
    isLoggedIn: true,
  })),
}));

// Mock translation — pass-through
vi.mock("@/translation", () => ({
  __: (s: string) => s,
}));
