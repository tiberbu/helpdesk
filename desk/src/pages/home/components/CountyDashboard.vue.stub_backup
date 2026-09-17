<template>
  <!--
    CountyDashboard placeholder.

    NOTE: This file was missing from the repo while being imported from three
    places (Home.vue, ChartItem.vue, CountyDashboardPage.vue), which broke the
    Vite build and therefore the Docker image build.

    This stub is intentionally minimal to unblock the build pipeline. The real
    County Tier dashboard (L0/L1/L2/L3 tier-aware widgets) still needs to be
    implemented. When doing so, replace this placeholder with the full
    component and keep the default export shape compatible with existing
    callers (no required props; optional `ref` usage from Home.vue).
  -->
  <div
    v-if="visible"
    class="rounded border border-outline-gray-1 p-4 text-ink-gray-5 text-sm"
  >
    {{ __("County Dashboard coming soon.") }}
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { __ } from "@/translation";

// Kept visible=false by default so this stub doesn't add visual noise in
// production; set to true during local development if you want to see it.
const visible = ref(false);

// Exposed API surface kept empty on purpose — the real component can extend
// this when it replaces the stub. Home.vue keeps a `ref` to it but doesn't
// currently call anything, so no methods are required.
defineExpose({});
</script>
