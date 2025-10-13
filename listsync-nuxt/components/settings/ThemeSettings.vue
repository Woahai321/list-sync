<template>
  <Card class="glass-card">
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center gap-3">
        <div class="p-3 rounded-lg bg-success/10">
          <PaletteIcon class="w-5 h-5 text-success" />
        </div>
        <div>
          <h3 class="text-lg font-semibold titillium-web-semibold">
            Theme Settings
          </h3>
          <p class="text-sm text-muted-foreground">
            Customize the appearance of ListSync
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="space-y-6">
        <!-- Accent Color -->
        <div>
          <label class="block text-sm font-medium mb-3">
            Accent Color <span class="text-xs text-muted-foreground ml-2">(Currently: {{ getCurrentColorLabel() }})</span>
          </label>
          <div class="grid grid-cols-4 gap-3">
            <button
              v-for="color in accentColors"
              :key="color.value"
              type="button"
              :class="[
                'relative p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2',
                localValue.accentColor === color.value
                  ? 'border-white bg-white/5 shadow-lg'
                  : 'border-border hover:border-white/30'
              ]"
              @click="setAccentColor(color.value)"
            >
              <!-- Selected Checkmark -->
              <div 
                v-if="localValue.accentColor === color.value"
                class="absolute -top-2 -right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-lg"
              >
                <CheckIcon :size="14" class="text-black" />
              </div>
              
              <div
                class="w-10 h-10 rounded-full ring-2 ring-white/20"
                :style="{ backgroundColor: color.hex }"
              />
              <span class="text-xs font-medium">{{ color.label }}</span>
            </button>
          </div>
          <p class="text-xs text-muted-foreground mt-3">
            Changes apply instantly to all UI elements
          </p>
        </div>
      </div>

      <!-- Preview Box -->
      <div class="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
        <div class="flex items-center gap-2 mb-2">
          <SparklesIcon class="w-4 h-4 text-primary" />
          <span class="text-sm font-medium">Theme Preview</span>
        </div>
        <p class="text-sm text-muted-foreground">
          Your current theme settings will be applied immediately. The glassmorphic design with purple accents creates a modern, elegant interface.
        </p>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Palette as PaletteIcon,
  Sparkles as SparklesIcon,
  Check as CheckIcon,
} from 'lucide-vue-next'

interface ThemeSettings {
  mode: 'dark' | 'light'
  accentColor: string
  fontSize: string
}

interface Props {
  modelValue: ThemeSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: ThemeSettings]
}>()

// Use the theme composable
const { theme, setMode: applyMode, setAccentColor: applyAccentColor, setFontSize: applyFontSize } = useTheme()

// Use theme state directly
const localValue = computed(() => ({
  mode: theme.value.mode,
  accentColor: theme.value.accentColor,
  fontSize: theme.value.fontSize,
}))

// Accent colors (using fixed hex values so they don't change with theme)
const accentColors = [
  { label: 'Purple', value: 'purple', hex: '#9d34da' },
  { label: 'Blue', value: 'blue', hex: '#3b82f6' },
  { label: 'Green', value: 'green', hex: '#22c55e' },
  { label: 'Red', value: 'red', hex: '#ef4444' },
]

// Get current color label
const getCurrentColorLabel = () => {
  const current = accentColors.find(c => c.value === localValue.value.accentColor)
  return current?.label || 'Purple'
}

// Emit updates to parent (for unsaved changes detection)
const emitUpdate = () => {
  emit('update:modelValue', { ...localValue.value })
}

// Set mode - applies immediately AND emits
const setMode = (mode: 'dark' | 'light') => {
  applyMode(mode)
  emitUpdate()
}

// Set accent color - applies immediately AND emits
const setAccentColor = (color: string) => {
  applyAccentColor(color as any)
  emitUpdate()
}

// Set font size - applies immediately AND emits
const setFontSize = (size: string) => {
  applyFontSize(size as any)
  emitUpdate()
}
</script>

