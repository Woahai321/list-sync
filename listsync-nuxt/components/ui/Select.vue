<template>
  <div class="w-full">
    <!-- Label -->
    <label v-if="label" :for="selectId" class="mb-1.5 block text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <!-- Select Container -->
    <div class="relative">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        :class="selectClasses"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled class="bg-card text-foreground">{{ placeholder }}</option>
        <option
          v-for="option in normalizedOptions"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
          class="bg-card text-foreground py-2"
        >
          {{ option.label }}
        </option>
      </select>

      <!-- Chevron Icon -->
      <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">
        <component :is="ChevronDownIcon" :size="18" />
      </div>
    </div>

    <!-- Helper Text / Error -->
    <p v-if="helperText || error" :class="helperClasses" class="mt-1.5 text-sm">
      {{ error || helperText }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown as ChevronDownIcon } from 'lucide-vue-next'

interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  options: Array<SelectOption | string | number>
  disabled?: boolean
  required?: boolean
  error?: string
  helperText?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  change: [value: string | number]
}>()

const selectId = computed(() => `select-${Math.random().toString(36).substr(2, 9)}`)

// Normalize options to SelectOption format
const normalizedOptions = computed(() => {
  return props.options.map(option => {
    if (typeof option === 'string' || typeof option === 'number') {
      return {
        label: String(option),
        value: option,
        disabled: false,
      }
    }
    return option
  })
})

const handleChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const value = target.value
  emit('update:modelValue', value)
  emit('change', value)
}

const selectClasses = computed(() => {
  const baseClasses = [
    'w-full rounded-lg',
    'bg-black/40 backdrop-blur-sm',
    'border transition-colors',
    'text-foreground',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'px-3 py-2 pr-10',
    'appearance-none',
    'cursor-pointer',
    // Dark theme option styling
    '[&>option]:bg-card',
    '[&>option]:text-foreground',
    '[&>option]:py-2',
  ]

  // Error or normal border
  if (props.error) {
    baseClasses.push('border-red-500 focus:ring-red-500')
  } else {
    baseClasses.push('border-purple-500/20 focus:border-purple-500 focus:ring-purple-500')
  }

  return baseClasses.join(' ')
})

const helperClasses = computed(() => {
  return props.error 
    ? 'text-red-400' 
    : 'text-muted-foreground'
})
</script>

