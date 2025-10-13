<template>
  <span ref="counterRef" class="counter-animate tabular-nums">
    {{ displayValue }}
  </span>
</template>

<script setup lang="ts">
interface Props {
  value: number
  duration?: number
  format?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  duration: 1000,
  format: true,
})

const counterRef = ref<HTMLElement | null>(null)
const displayValue = ref('0')
const currentValue = ref(0)

// Easing function
const easeOutExpo = (t: number): number => {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
}

// Animate counter
const animateCounter = (start: number, end: number) => {
  const startTime = Date.now()
  const difference = end - start

  const updateCounter = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / props.duration, 1)
    const easedProgress = easeOutExpo(progress)
    
    const value = Math.floor(start + difference * easedProgress)
    currentValue.value = value

    if (props.format) {
      displayValue.value = value.toLocaleString()
    } else {
      displayValue.value = value.toString()
    }

    if (progress < 1) {
      requestAnimationFrame(updateCounter)
    } else {
      currentValue.value = end
      displayValue.value = props.format ? end.toLocaleString() : end.toString()
    }
  }

  requestAnimationFrame(updateCounter)
}

// Watch for value changes
watch(() => props.value, (newValue, oldValue) => {
  const start = oldValue ?? currentValue.value
  animateCounter(start, newValue)
}, { immediate: true })

onMounted(() => {
  animateCounter(0, props.value)
})
</script>

<style scoped>
.counter-animate {
  display: inline-block;
}
</style>

