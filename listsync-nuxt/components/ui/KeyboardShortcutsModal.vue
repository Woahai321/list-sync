<template>
  <Modal
    v-model="isOpen"
    title="Keyboard Shortcuts"
    size="md"
  >
    <div class="space-y-6">
      <!-- Navigation -->
      <div>
        <h4 class="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <NavigationIcon :size="16" class="text-purple-400" />
          Navigation
        </h4>
        <div class="space-y-2">
          <ShortcutItem shortcut="d" description="Go to Dashboard" />
          <ShortcutItem shortcut="l" description="Go to Lists" />
          <ShortcutItem shortcut="h" description="Go to History" />
        </div>
      </div>

      <!-- Actions -->
      <div>
        <h4 class="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <ZapIcon :size="16" class="text-blue-400" />
          Actions
        </h4>
        <div class="space-y-2">
          <ShortcutItem ctrl shortcut="s" description="Trigger Sync" />
          <ShortcutItem ctrl shortcut="n" description="Add New List" />
          <ShortcutItem ctrl shortcut="k" description="Focus Search" />
        </div>
      </div>

      <!-- General -->
      <div>
        <h4 class="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <SettingsIcon :size="16" class="text-green-400" />
          General
        </h4>
        <div class="space-y-2">
          <ShortcutItem shortcut="/" description="Focus Search" />
          <ShortcutItem shortcut="Esc" description="Close Modal" />
          <ShortcutItem shift shortcut="?" description="Show This Help" />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <Button variant="primary" @click="isOpen = false">
          Got it!
        </Button>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  Navigation as NavigationIcon,
  Zap as ZapIcon,
  Settings as SettingsIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
</script>
