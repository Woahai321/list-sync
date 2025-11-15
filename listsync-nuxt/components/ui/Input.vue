<template>
  <div class="w-full">
    <!-- Label -->
    <label v-if="label" :for="inputId" class="mb-1.5 block text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <!-- Input Container -->
    <div class="relative">
      <!-- Icon (left) -->
      <div v-if="icon" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
        <component :is="icon" :size="18" />
      </div>

      <!-- Input Field -->
      <input
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :readonly="readonly"
        :autocomplete="autocomplete"
        :class="inputClasses"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />

      <!-- Clear Button -->
      <button
        v-if="clearable && modelValue && !disabled && !readonly"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
        @click="handleClear"
      >
        <component :is="XIcon" :size="16" />
      </button>
    </div>

    <!-- Helper Text / Error -->
    <p v-if="helperText || error" :class="helperClasses" class="mt-1.5 text-sm">
      {{ error || helperText }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { X as XIcon } from 'lucide-vue-next'
import type { Component } from 'vue'

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'url' | 'search' | 'tel'
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  error?: string
  helperText?: string
  icon?: Component
  clearable?: boolean
  autocomplete?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  readonly: false,
  required: false,
  clearable: false,
  autocomplete: 'off',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  blur: [event: FocusEvent]
  focus: [event: FocusEvent]
}>()

const inputId = computed(() => `input-${Math.random().toString(36).substr(2, 9)}`)

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleClear = () => {
  emit('update:modelValue', '')
}

const inputClasses = computed(() => {
  const baseClasses = [
    'w-full rounded-xl',  // More rounded (12px)
    'h-11 sm:h-10',  // Larger on mobile (44px), standard on desktop (40px)
    'bg-black/40 backdrop-blur-sm',
    'border-2 transition-all duration-200',  // Thicker border, smooth transition
    'text-base sm:text-sm',  // Larger text on mobile for better readability
    'text-foreground placeholder:text-muted-foreground/60',
    'focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:ring-offset-0',
    'hover:border-purple-500/40',  // Hover state
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'px-4 py-2.5 sm:py-2',  // More padding on mobile
    'touch-manipulation',  // Better touch handling
  ]

  // Add padding for icon
  if (props.icon) {
    baseClasses.push('pl-10')
  }

  // Add padding for clear button
  if (props.clearable && props.modelValue) {
    baseClasses.push('pr-10')
  }

  // Error or normal border
  if (props.error) {
    baseClasses.push('border-red-500 focus:ring-red-500/50 focus:border-red-600')
  } else {
    baseClasses.push('border-purple-500/20 focus:border-purple-500')
  }

  return baseClasses.join(' ')
})

const helperClasses = computed(() => {
  return props.error 
    ? 'text-red-400' 
    : 'text-muted-foreground'
})
</script>

