<template>
  <span :class="badgeClasses">
    <component v-if="icon" :is="icon" :size="12" class="mr-1" />
    <slot />
  </span>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md' | 'lg'
  icon?: Component
  pill?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
  pill: false,
})

const badgeClasses = computed(() => {
  const baseClasses = [
    'inline-flex items-center justify-center',
    'font-medium',
    'border',
    'transition-colors',
  ]

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  }

  // Variant classes
  const variantClasses = {
    default: 'bg-muted/50 border-border text-muted-foreground',
    primary: 'status-info',
    success: 'status-success',
    warning: 'status-warning',
    error: 'status-error',
    info: 'bg-blue-500/15 border-blue-500/30 text-blue-300',
  }

  // Rounded classes
  const roundedClass = props.pill ? 'rounded-full' : 'rounded-md'

  return [
    ...baseClasses,
    sizeClasses[props.size],
    variantClasses[props.variant],
    roundedClass,
  ].join(' ')
})
</script>

