<template>
  <div
    :class="[
      'animate-pulse bg-gradient-to-r from-muted/20 via-muted/40 to-muted/20 bg-[length:200%_100%]',
      'rounded-lg',
      widthClass,
      heightClass,
    ]"
    :style="{ animationDuration: '1.5s', backgroundPosition: '200% 0' }"
  >
    <span class="sr-only">Loading...</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  width?: 'full' | 'auto' | '1/2' | '1/3' | '1/4' | '2/3' | '3/4'
  height?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
}

const props = withDefaults(defineProps<Props>(), {
  width: 'full',
  height: 'md',
})

const widthClass = computed(() => {
  const widthMap = {
    full: 'w-full',
    auto: 'w-auto',
    '1/2': 'w-1/2',
    '1/3': 'w-1/3',
    '1/4': 'w-1/4',
    '2/3': 'w-2/3',
    '3/4': 'w-3/4',
  }
  return widthMap[props.width]
})

const heightClass = computed(() => {
  const heightMap = {
    xs: 'h-4',
    sm: 'h-6',
    md: 'h-10',
    lg: 'h-16',
    xl: 'h-24',
    '2xl': 'h-32',
  }
  return heightMap[props.height]
})
</script>

<style scoped>
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.animate-pulse {
  animation: shimmer 1.5s ease-in-out infinite;
}
</style>

