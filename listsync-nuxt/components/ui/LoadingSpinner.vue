<template>
  <div :class="containerClasses">
    <div :class="spinnerClasses" :style="spinnerStyle" />
    <p v-if="text" :class="textClasses">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'white' | 'muted'
  text?: string
  fullScreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  color: 'primary',
  fullScreen: false,
})

const sizeMap = {
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
}

const colorMap = {
  primary: 'border-purple-500',
  white: 'border-white',
  muted: 'border-muted-foreground',
}

const containerClasses = computed(() => {
  const base = 'flex flex-col items-center justify-center gap-3'
  
  if (props.fullScreen) {
    return `${base} fixed inset-0 z-50 bg-black/50 backdrop-blur-sm`
  }
  
  return base
})

const spinnerClasses = computed(() => {
  return [
    'animate-spin rounded-full border-2 border-t-transparent',
    colorMap[props.color],
  ].join(' ')
})

const spinnerStyle = computed(() => {
  const size = sizeMap[props.size]
  return {
    width: `${size}px`,
    height: `${size}px`,
  }
})

const textClasses = computed(() => {
  return 'text-sm font-medium text-muted-foreground animate-pulse'
})
</script>

