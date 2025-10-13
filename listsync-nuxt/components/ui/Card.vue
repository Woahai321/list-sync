<template>
  <div :class="cardClasses">
    <!-- Header -->
    <div v-if="$slots.header || title" class="border-b border-purple-500/10 px-6 py-4">
      <slot name="header">
        <h3 v-if="title" class="text-lg font-semibold text-foreground">
          {{ title }}
        </h3>
      </slot>
    </div>

    <!-- Content -->
    <div :class="contentClasses">
      <slot />
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="border-t border-purple-500/10 px-6 py-4">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  variant?: 'default' | 'hover' | 'flat'
  padding?: boolean
  noPadding?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  padding: true,
  noPadding: false,
})

const cardClasses = computed(() => {
  const baseClasses = [
    'rounded-xl',  // More rounded (12px)
    'overflow-hidden',
    'transition-all',
    'duration-300'
  ]

  const variantClasses = {
    default: 'glass-card',
    hover: 'glass-card hover:-translate-y-1 hover:shadow-2xl cursor-pointer',
    flat: 'bg-card border border-border hover:border-primary/50',
  }

  return [
    ...baseClasses,
    variantClasses[props.variant],
  ].join(' ')
})

const contentClasses = computed(() => {
  if (props.noPadding) return ''
  return props.padding ? 'px-6 py-4' : ''
})
</script>

