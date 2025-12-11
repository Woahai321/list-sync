<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="handleBackdropClick"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/90 backdrop-blur-md" />

        <!-- Modal Content -->
        <div
          :class="modalClasses"
          class="relative z-10 w-full rounded-2xl glass-card shadow-2xl max-h-[90vh] overflow-hidden"
          role="dialog"
          aria-modal="true"
        >
          <!-- Close Button -->
          <button
            v-if="closable"
            type="button"
            class="absolute right-4 top-4 z-20 text-muted-foreground hover:text-foreground transition-colors touch-manipulation p-2 rounded-full hover:bg-purple-500/20"
            @click="close"
            aria-label="Close modal"
          >
            <component :is="XIcon" :size="20" />
          </button>

          <!-- Header -->
          <div v-if="$slots.header || title" class="border-b border-purple-500/10 px-4 sm:px-6 py-3 sm:py-4 pr-14">
            <slot name="header">
              <h2 class="text-xl font-bold text-foreground">
                {{ title }}
              </h2>
            </slot>
          </div>

          <!-- Body -->
          <div :class="bodyClasses">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="border-t border-purple-500/10 px-4 sm:px-6 py-3 sm:py-4 sticky bottom-0 bg-background/95 backdrop-blur-sm">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { X as XIcon } from 'lucide-vue-next'

interface Props {
  modelValue: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full'
  closable?: boolean
  closeOnBackdrop?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  closable: true,
  closeOnBackdrop: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    close()
  }
}

const modalClasses = computed(() => {
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-[95vw] sm:max-w-4xl',
    full: 'max-w-[95vw] sm:max-w-5xl lg:max-w-6xl',
  }

  return sizeClasses[props.size]
})

const bodyClasses = computed(() => {
  // For full-size modals, use more height
  if (props.size === 'full') {
    return 'px-4 sm:px-6 py-3 sm:py-4 max-h-[80vh] sm:max-h-[80vh] overflow-y-auto custom-scrollbar'
  }
  // For 3xl modals, let content control its own layout (for split-panel layouts like AddListModal)
  if (props.size === '3xl') {
    return 'px-4 sm:px-6 py-3 sm:py-4'
  }
  // For 2xl modals, let content control its own height/overflow (for split-panel layouts)
  if (props.size === '2xl') {
    return 'px-4 sm:px-6 py-3 sm:py-4'
  }
  return 'px-4 sm:px-6 py-3 sm:py-4 max-h-[75vh] sm:max-h-[70vh] overflow-y-auto custom-scrollbar'
})

// Lock body scroll when modal is open
watch(() => props.modelValue, (isOpen) => {
  if (process.client) {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (process.client) {
    document.body.style.overflow = ''
  }
})

// Handle ESC key
onMounted(() => {
  if (process.client) {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && props.modelValue && props.closable) {
        close()
      }
    }
    window.addEventListener('keydown', handleEsc)
    
    onUnmounted(() => {
      window.removeEventListener('keydown', handleEsc)
    })
  }
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: scale(0.90) translateY(-20px);
  opacity: 0;
}

/* Backdrop animation */
.modal-enter-active > div:first-child,
.modal-leave-active > div:first-child {
  transition: opacity 0.25s ease;
}

.modal-enter-from > div:first-child,
.modal-leave-to > div:first-child {
  opacity: 0;
}

/* Custom scrollbar for modal */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}
</style>

