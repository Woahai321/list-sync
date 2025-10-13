<template>
  <div class="relative inline-flex items-center justify-center" :style="{ width: `${size}px`, height: `${size}px` }">
    <!-- Background Circle -->
    <svg class="progress-ring -rotate-90 transform" :width="size" :height="size">
      <circle
        class="text-muted/20"
        stroke="currentColor"
        :stroke-width="strokeWidth"
        fill="transparent"
        :r="radius"
        :cx="center"
        :cy="center"
      />
      <!-- Progress Circle -->
      <circle
        class="transition-all duration-500 ease-out"
        :class="progressColorClass"
        stroke="currentColor"
        :stroke-width="strokeWidth"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="strokeDashoffset"
        stroke-linecap="round"
        fill="transparent"
        :r="radius"
        :cx="center"
        :cy="center"
      />
    </svg>

    <!-- Center Content -->
    <div class="absolute inset-0 flex items-center justify-center">
      <slot>
        <span v-if="showPercentage" class="text-sm font-bold text-foreground">
          {{ Math.round(progress) }}%
        </span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  progress: number // 0-100
  size?: number
  strokeWidth?: number
  color?: 'primary' | 'success' | 'warning' | 'error'
  showPercentage?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 80,
  strokeWidth: 6,
  color: 'primary',
  showPercentage: true,
})

const center = computed(() => props.size / 2)
const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

const strokeDashoffset = computed(() => {
  const percentage = Math.min(Math.max(props.progress, 0), 100)
  return circumference.value - (percentage / 100) * circumference.value
})

const progressColorClass = computed(() => {
  const colorClasses = {
    primary: 'text-purple-500',
    success: 'text-green-500',
    warning: 'text-yellow-500',
    error: 'text-red-500',
  }
  return colorClasses[props.color]
})
</script>

