<template>
  <div
    ref="triggerRef"
    class="inline-block"
    @mouseenter="showTooltip"
    @mouseleave="hideTooltip"
    @focus="showTooltip"
    @blur="hideTooltip"
  >
    <slot />
    
    <Teleport to="body">
      <Transition name="tooltip">
        <div
          v-if="isVisible && content"
          ref="tooltipRef"
          :class="tooltipClasses"
          :style="tooltipStyle"
          role="tooltip"
        >
          {{ content }}
          <div :class="arrowClasses" :style="arrowStyle" />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
interface Props {
  content?: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
}

const props = withDefaults(defineProps<Props>(), {
  placement: 'top',
  delay: 200,
})

const triggerRef = ref<HTMLElement | null>(null)
const tooltipRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const tooltipStyle = ref({})
const arrowStyle = ref({})
let showTimeout: NodeJS.Timeout | null = null

const showTooltip = () => {
  if (showTimeout) clearTimeout(showTimeout)
  
  showTimeout = setTimeout(() => {
    isVisible.value = true
    nextTick(() => {
      updatePosition()
    })
  }, props.delay)
}

const hideTooltip = () => {
  if (showTimeout) {
    clearTimeout(showTimeout)
    showTimeout = null
  }
  isVisible.value = false
}

const updatePosition = () => {
  if (!triggerRef.value || !tooltipRef.value) return

  const triggerRect = triggerRef.value.getBoundingClientRect()
  const tooltipRect = tooltipRef.value.getBoundingClientRect()
  const spacing = 8

  let top = 0
  let left = 0

  switch (props.placement) {
    case 'top':
      top = triggerRect.top - tooltipRect.height - spacing
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
      break
    
    case 'bottom':
      top = triggerRect.bottom + spacing
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
      break
    
    case 'left':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
      left = triggerRect.left - tooltipRect.width - spacing
      break
    
    case 'right':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
      left = triggerRect.right + spacing
      break
  }

  // Ensure tooltip stays within viewport
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  if (left < spacing) left = spacing
  if (left + tooltipRect.width > viewportWidth - spacing) {
    left = viewportWidth - tooltipRect.width - spacing
  }
  
  if (top < spacing) top = spacing
  if (top + tooltipRect.height > viewportHeight - spacing) {
    top = viewportHeight - tooltipRect.height - spacing
  }

  tooltipStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
  }

  // Arrow positioning
  const arrowSize = 6
  switch (props.placement) {
    case 'top':
      arrowStyle.value = {
        top: '100%',
        left: '50%',
        transform: 'translateX(-50%)',
        borderLeft: `${arrowSize}px solid transparent`,
        borderRight: `${arrowSize}px solid transparent`,
        borderTop: `${arrowSize}px solid rgba(157, 52, 218, 0.95)`,
      }
      break
    
    case 'bottom':
      arrowStyle.value = {
        bottom: '100%',
        left: '50%',
        transform: 'translateX(-50%)',
        borderLeft: `${arrowSize}px solid transparent`,
        borderRight: `${arrowSize}px solid transparent`,
        borderBottom: `${arrowSize}px solid rgba(157, 52, 218, 0.95)`,
      }
      break
    
    case 'left':
      arrowStyle.value = {
        left: '100%',
        top: '50%',
        transform: 'translateY(-50%)',
        borderTop: `${arrowSize}px solid transparent`,
        borderBottom: `${arrowSize}px solid transparent`,
        borderLeft: `${arrowSize}px solid rgba(157, 52, 218, 0.95)`,
      }
      break
    
    case 'right':
      arrowStyle.value = {
        right: '100%',
        top: '50%',
        transform: 'translateY(-50%)',
        borderTop: `${arrowSize}px solid transparent`,
        borderBottom: `${arrowSize}px solid transparent`,
        borderRight: `${arrowSize}px solid rgba(157, 52, 218, 0.95)`,
      }
      break
  }
}

const tooltipClasses = computed(() => {
  return [
    'fixed z-[9999] px-3 py-2 text-sm font-medium text-white',
    'rounded-lg shadow-lg',
    'bg-purple-600/95 backdrop-blur-sm',
    'pointer-events-none',
    'max-w-xs',
  ].join(' ')
})

const arrowClasses = 'absolute w-0 h-0'

onUnmounted(() => {
  if (showTimeout) clearTimeout(showTimeout)
})
</script>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}
</style>

