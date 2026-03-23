import { defineConfig, Plugin } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import path from "path";

// Stub all unplugin-icons ~icons/* imports so tests don't need real SVGs
const iconStubPlugin: Plugin = {
  name: "vitest-icon-stub",
  resolveId(id) {
    if (id.startsWith("~icons/")) return "\0vitest-icon-stub";
  },
  load(id) {
    if (id === "\0vitest-icon-stub") {
      return `import { defineComponent, h } from 'vue'
export default defineComponent({ render: () => h('span') })`;
    }
  },
};

export default defineConfig({
  plugins: [iconStubPlugin, vue()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
});
