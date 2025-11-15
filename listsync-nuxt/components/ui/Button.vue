<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    :aria-label="ariaLabel"
    :aria-busy="loading"
    :aria-disabled="disabled || loading"
    class="group relative overflow-hidden active:scale-98 transition-transform duration-100"
    @click="handleClick"
  >
    <!-- Ripple effect background -->
    <span class="absolute inset-0 rounded-lg overflow-hidden" aria-hidden="true">
      <span class="absolute inset-0 bg-white opacity-0 group-active:opacity-10 transition-opacity duration-300" />
    </span>
    
    <!-- Content wrapper -->
    <span class="relative flex items-center justify-center">
      <!-- Loading Spinner -->
      <span 
        v-if="loading" 
        class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        aria-label="Loading"
        role="status"
      >
        <span class="sr-only">Loading...</span>
      </span>
      
      <!-- Icon (left) -->
      <component 
        v-if="icon && !iconRight && !loading" 
        :is="icon" 
        :size="iconSize" 
        class="mr-2 transition-transform group-hover:scale-110 duration-200"
        aria-hidden="true"
      />
      
      <!-- Default Slot -->
      <slot />
      
      <!-- Icon (right) -->
      <component 
        v-if="icon && iconRight && !loading" 
        :is="icon" 
        :size="iconSize" 
        class="ml-2 transition-transform group-hover:scale-110 duration-200"
        aria-hidden="true"
      />
    </span>
  </button>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  icon?: Component
  iconRight?: boolean
  iconSize?: number
  fullWidth?: boolean
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  iconRight: false,
  iconSize: 16,
  fullWidth: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}

const buttonClasses = computed(() => {
  const baseClasses = [
    'inline-flex items-center justify-center',
    'rounded-lg font-semibold',
    'transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'touch-manipulation',  // Better touch handling on mobile
  ]

  // Size classes (optimized for touch targets - minimum 44px height for mobile)
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',  // 36px for tight spaces
    md: 'px-4 py-2.5 text-base min-h-[44px]',  // 44px touch target
    lg: 'px-6 py-3 text-lg min-h-[48px]',  // 48px for prominent buttons
  }

  // Variant classes
  const variantClasses = {
    primary: [
      'glass-button-primary',
      'focus:ring-purple-500',
    ],
    secondary: [
      'glass-button',
      'focus:ring-purple-500',
    ],
    ghost: [
      'bg-transparent hover:bg-white/5',
      'border border-transparent hover:border-purple-500/30',
      'text-foreground',
      'focus:ring-purple-500',
    ],
    danger: [
      'bg-red-600 hover:bg-red-700',
      'border border-red-500',
      'text-white',
      'focus:ring-red-500',
    ],
    success: [
      'bg-green-600 hover:bg-green-700',
      'border border-green-500',
      'text-white',
      'focus:ring-green-500',
    ],
  }

  const widthClass = props.fullWidth ? 'w-full' : ''

  return [
    ...baseClasses,
    sizeClasses[props.size],
    ...variantClasses[props.variant],
    widthClass,
  ].filter(Boolean).join(' ')
})
</script>

