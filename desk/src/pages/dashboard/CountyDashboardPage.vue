<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">{{ __("County Dashboard") }}</div>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5 max-w-6xl w-full mx-auto">
      <CountyDashboard />
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import { __ } from "@/translation";
import CountyDashboard from "@/pages/home/components/CountyDashboard.vue";
</script>
