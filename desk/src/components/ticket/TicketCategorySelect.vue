<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center text-base leading-5">
      <div class="w-[126px] text-sm text-gray-600">Category</div>
      <FormControl
        class="flex-1"
        type="select"
        :options="categoryOptions"
        :value="category"
        placeholder="Select Category"
        @change="onCategoryChange"
      />
    </div>
    <div v-if="category" class="flex items-center text-base leading-5">
      <div class="w-[126px] text-sm text-gray-600">Sub Category</div>
      <FormControl
        class="flex-1"
        type="select"
        :options="subCategoryOptions"
        :value="subCategory"
        placeholder="Select Sub Category"
        @change="onSubCategoryChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { FormControl, createListResource } from "frappe-ui";
import { computed, watch } from "vue";

const props = defineProps({
  ticketId: {
    type: [String, Number],
    default: null,
  },
  category: {
    type: String,
    default: "",
  },
  subCategory: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:category", "update:subCategory"]);

const categoryList = createListResource({
  doctype: "HD Ticket Category",
  fields: ["name"],
  filters: { parent_category: ["is", "not set"], is_active: 1 },
  orderBy: "name asc",
  auto: true,
});

const subCategoryList = createListResource({
  doctype: "HD Ticket Category",
  fields: ["name"],
  filters: { parent_category: props.category || "__none__", is_active: 1 },
  orderBy: "name asc",
  auto: false,
});

const categoryOptions = computed(() => {
  const items = categoryList.data || [];
  return [
    { label: "", value: "" },
    ...items.map((c: { name: string }) => ({ label: c.name, value: c.name })),
  ];
});

const subCategoryOptions = computed(() => {
  const items = subCategoryList.data || [];
  return [
    { label: "", value: "" },
    ...items.map((c: { name: string }) => ({ label: c.name, value: c.name })),
  ];
});

watch(
  () => props.category,
  (newCategory) => {
    if (newCategory) {
      subCategoryList.update({
        filters: { parent_category: newCategory, is_active: 1 },
      });
      subCategoryList.reload();
    }
  },
  { immediate: true }
);

function onCategoryChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value;
  emit("update:category", value);
  if (!value) {
    emit("update:subCategory", "");
  }
}

function onSubCategoryChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value;
  emit("update:subCategory", value);
}
</script>
