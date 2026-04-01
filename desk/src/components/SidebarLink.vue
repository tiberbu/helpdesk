<template>
  <div
    class="-all flex h-7 cursor-pointer items-center rounded pl-2 pr-1 text-base duration-300 ease-in-out"
    :class="{
      'w-full': isExpanded,
      'w-8': !isExpanded,
      // --- Light mode ---
      'shadow-sm': isActive && !dark,
      [bgColor]: isActive && !dark,
      [hvColor]: !isActive && !dark,
      'text-gray-800': !dark,
      // --- Dark mode active ---
      'border-l-[3px] border-[#0891B2] bg-[#252A31] text-white !rounded-l-none': dark && isActive,
      // --- Dark mode inactive ---
      'text-[#B0B7C3] hover:bg-[#2D3239] hover:text-[#E4E7EB]': dark && !isActive,
    }"
    @click="handleNavigation"
  >
    <Tooltip :text="__(label)" v-if="!isExpanded">
      <span
        class="shrink-0"
        :class="{
          'text-[#B0B7C3]': dark && !isActive,
          'text-white': dark && isActive,
          'text-gray-700': !dark,
          'text-gray-900': !dark && !isExpanded,
          'icon-emoji': isMobileView,
        }"
      >
        <component :is="icon" class="h-4 w-4" />
      </span>
    </Tooltip>
    <span
      v-else
      class="shrink-0"
      :class="{
        'text-[#B0B7C3]': dark && !isActive,
        'text-white': dark && isActive,
        'text-gray-700': !dark,
        'text-gray-900': !dark && !isExpanded,
        'icon-emoji': isMobileView,
      }"
    >
      <component :is="icon" class="h-4 w-4" />
    </span>

    <div
      class="-all ml-2 flex shrink-0 grow items-center justify-between text-sm duration-300 ease-in-out"
      :class="{
        'opacity-100': isExpanded,
        'opacity-0': !isExpanded,
        '-z-50': !isExpanded,
      }"
    >
      {{ __(label) }}
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useScreenSize } from "@/composables/screen";
import { useRouter } from "vue-router";

interface P {
  icon?: unknown;
  label: string;
  isExpanded?: boolean;
  isActive?: boolean;
  onClick?: () => void;
  to?: string | object;
  bgColor?: string;
  hvColor?: string;
  dark?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  isActive: false,
  onClick: () => () => true,
  to: "",
  bgColor: "bg-white",
  hvColor: "hover:bg-gray-100",
  dark: false,
});
const router = useRouter();
const { isMobileView } = useScreenSize();

function handleNavigation() {
  props.onClick();
  if (!props.to) return;
  if (
    props.to === router.currentRoute.value.name &&
    !router.currentRoute.value.query.view
  )
    return;
  if (typeof props.to === "string") {
    router.push({
      name: props.to,
    });
    return;
  }
  router.push(props.to);
}
</script>

<style>
.icon-emoji > div {
  @apply flex items-center justify-center;
}
</style>
