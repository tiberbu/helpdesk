<template>
  <SettingsLayoutBase
    :title="__('Brands')"
    :description="
      __('Configure brand identities for separate portals, email routing, and chat widgets.')
    "
  >
    <template #header-actions>
      <Button
        :label="__('New Brand')"
        theme="gray"
        variant="solid"
        icon-left="plus"
        @click="openCreateDialog"
      />
    </template>

    <template #content>
      <!-- List -->
      <div v-if="!brands.loading && brands.data?.length > 0" class="w-full h-full -ml-2">
        <div class="flex text-sm text-gray-600 ml-2 mb-1">
          <div class="flex-1">{{ __("Brand Name") }}</div>
          <div class="w-48">{{ __("Support Email") }}</div>
          <div class="w-36">{{ __("Portal Domain") }}</div>
          <div class="w-16 text-center">{{ __("Active") }}</div>
          <div class="w-10" />
        </div>
        <hr class="mx-2 mt-1 mb-1" />
        <div v-for="(brand, index) in brands.data" :key="brand.name">
          <div class="flex items-center cursor-pointer hover:bg-gray-50 rounded px-2 py-3">
            <div class="flex-1 font-medium text-ink-gray-7 text-base">
              {{ brand.brand_name }}
            </div>
            <div class="w-48 text-sm text-gray-600 truncate">
              {{ brand.support_email || "—" }}
            </div>
            <div class="w-36 text-sm text-gray-600 truncate">
              {{ brand.portal_domain || "—" }}
            </div>
            <div class="w-16 flex justify-center">
              <Badge
                :label="brand.is_active ? __('Active') : __('Inactive')"
                :theme="brand.is_active ? 'green' : 'gray'"
                variant="subtle"
              />
            </div>
            <div class="w-10 flex justify-end">
              <Dropdown placement="left" :options="dropdownOptions(brand)">
                <Button icon="more-horizontal" variant="ghost" />
              </Dropdown>
            </div>
          </div>
          <hr v-if="index !== brands.data.length - 1" class="mx-2" />
        </div>
        <div class="flex justify-center mt-2">
          <Button
            v-if="!brands.loading && brands.hasNextPage"
            class="mt-2"
            @click="brands.next()"
            :loading="brands.loading"
            :label="__('Load More')"
            icon-left="refresh-cw"
          />
        </div>
      </div>

      <!-- Loading -->
      <div v-if="brands.loading" class="flex mt-28 justify-center w-full">
        <Button :loading="true" variant="ghost" class="w-full" size="2xl" />
      </div>

      <!-- Empty state -->
      <div
        v-if="!brands.loading && !brands.data?.length"
        class="flex flex-col items-center justify-center gap-4 h-full"
      >
        <div class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center">
          <LucideTag class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">{{ __("No brands configured") }}</div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{ __("Add a brand to configure separate portals and email routing.") }}
          </div>
        </div>
        <Button :label="__('New Brand')" variant="outline" icon-left="plus" @click="openCreateDialog" />
      </div>
    </template>
  </SettingsLayoutBase>

  <!-- Create/Edit Dialog -->
  <Dialog
    v-model="showDialog"
    :options="{ title: editingBrand ? __('Edit Brand') : __('New Brand'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          :label="__('Brand Name')"
          v-model="form.brand_name"
          :required="true"
          autofocus
        />
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            :label="__('Support Email')"
            v-model="form.support_email"
            type="email"
            :placeholder="__('support@acme.com')"
          />
          <FormControl
            :label="__('Portal Domain')"
            v-model="form.portal_domain"
            :placeholder="__('support.acme.com')"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            :label="__('Default Team')"
            v-model="form.default_team"
            type="link"
            :doctype="'HD Team'"
          />
          <FormControl
            :label="__('Default SLA')"
            v-model="form.default_sla"
            type="link"
            :doctype="'HD Service Level Agreement'"
          />
        </div>
        <FormControl
          :label="__('CSAT Survey Template')"
          v-model="form.csat_template"
          type="link"
          :doctype="'HD CSAT Survey Template'"
        />
        <div class="grid grid-cols-2 gap-4">
          <FormControl
            :label="__('Primary Color')"
            v-model="form.primary_color"
            type="color"
          />
          <FormControl
            :label="__('Chat Greeting')"
            v-model="form.chat_greeting"
            :placeholder="__('Hi! How can we help you today?')"
          />
        </div>
        <FormControl
          :label="__('Active')"
          v-model="form.is_active"
          type="checkbox"
        />
      </div>
    </template>
    <template #actions>
      <Button variant="ghost" :label="__('Cancel')" @click="showDialog = false" />
      <Button
        variant="solid"
        :label="editingBrand ? __('Save') : __('Create')"
        :loading="saving"
        @click="saveBrand"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Badge, createListResource, createResource, Dialog, Dropdown, FormControl, toast } from "frappe-ui";
import { markRaw, ref } from "vue";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import LucideTag from "~icons/lucide/tag";
import { ConfirmDelete } from "@/utils";

const showDialog = ref(false);
const editingBrand = ref<string | null>(null);
const saving = ref(false);
const isConfirmingDelete = ref(false);

const emptyForm = () => ({
  brand_name: "",
  support_email: "",
  portal_domain: "",
  primary_color: "#4F46E5",
  chat_greeting: "Hi! How can we help you today?",
  default_team: "",
  default_sla: "",
  csat_template: "",
  is_active: 1,
});

const form = ref(emptyForm());

const brands = createListResource({
  doctype: "HD Brand",
  fields: ["name", "brand_name", "support_email", "portal_domain", "is_active"],
  auto: true,
  orderBy: "brand_name asc",
  pageLength: 50,
});

const brandDoc = createResource({
  url: "frappe.client.get",
  onSuccess(data) {
    form.value = {
      brand_name: data.brand_name || "",
      support_email: data.support_email || "",
      portal_domain: data.portal_domain || "",
      primary_color: data.primary_color || "#4F46E5",
      chat_greeting: data.chat_greeting || "Hi! How can we help you today?",
      default_team: data.default_team || "",
      default_sla: data.default_sla || "",
      csat_template: data.csat_template || "",
      is_active: data.is_active ?? 1,
    };
    showDialog.value = true;
  },
});

function openCreateDialog() {
  editingBrand.value = null;
  form.value = emptyForm();
  showDialog.value = true;
}

function openEditDialog(brand: any) {
  editingBrand.value = brand.name;
  brandDoc.fetch({ doctype: "HD Brand", name: brand.name });
}

async function saveBrand() {
  if (!form.value.brand_name) {
    toast.error(__("Brand Name is required"));
    return;
  }

  saving.value = true;
  try {
    if (editingBrand.value) {
      await createResource({
        url: "frappe.client.set_value",
      }).fetch({
        doctype: "HD Brand",
        name: editingBrand.value,
        fieldname: form.value,
      });
      toast.success(__("Brand updated"));
    } else {
      await createResource({
        url: "frappe.client.insert",
      }).fetch({
        doc: { doctype: "HD Brand", ...form.value },
      });
      toast.success(__("Brand created"));
    }
    showDialog.value = false;
    brands.reload();
  } catch (e: any) {
    toast.error(e?.message || __("Failed to save brand"));
  } finally {
    saving.value = false;
  }
}

async function deleteBrand(brand: any) {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  brands.delete.submit(brand.name, {
    onSuccess() {
      toast.success(__("Brand deleted"));
      isConfirmingDelete.value = false;
    },
    onError(e: any) {
      toast.error(e?.message || __("Failed to delete brand"));
      isConfirmingDelete.value = false;
    },
  });
}

const dropdownOptions = (brand: any) => [
  {
    label: __("Edit"),
    icon: "edit",
    onClick: () => openEditDialog(brand),
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteBrand(brand),
    isConfirmingDelete,
  }),
];
</script>
