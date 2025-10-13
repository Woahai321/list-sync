<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast-list">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="toastClasses(toast.type)"
          class="pointer-events-auto"
        >
          <!-- Icon -->
          <div class="flex-shrink-0">
            <component :is="getIcon(toast.type)" :size="20" />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm">{{ toast.title }}</p>
            <p v-if="toast.message" class="text-sm opacity-90 mt-0.5">
              {{ toast.message }}
            </p>
          </div>

          <!-- Close Button -->
          <button
            type="button"
            class="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
            @click="removeToast(toast.id)"
          >
            <component :is="XIcon" :size="16" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import {
  CheckCircle2 as SuccessIcon,
  XCircle as ErrorIcon,
  Info as InfoIcon,
  AlertTriangle as WarningIcon,
  X as XIcon,
} from 'lucide-vue-next'

const { toasts, removeToast } = useToast()

const getIcon = (type: string) => {
  switch (type) {
    case 'success':
      return SuccessIcon
    case 'error':
      return ErrorIcon
    case 'warning':
      return WarningIcon
    case 'info':
    default:
      return InfoIcon
  }
}

const toastClasses = (type: string) => {
  const baseClasses = [
    'flex items-start gap-3 p-4 rounded-lg shadow-lg',
    'min-w-[320px] max-w-md',
    'backdrop-blur-sm border',
    'animate-in slide-in-from-right',
  ]

  const typeClasses = {
    success: 'bg-green-600/90 text-white border-green-500',
    error: 'bg-red-600/90 text-white border-red-500',
    warning: 'bg-yellow-600/90 text-white border-yellow-500',
    info: 'bg-purple-600/90 text-white border-purple-500',
  }

  return [...baseClasses, typeClasses[type as keyof typeof typeClasses] || typeClasses.info].join(' ')
}
</script>

<style scoped>
.toast-list-enter-active,
.toast-list-leave-active {
  transition: all 0.3s ease;
}

.toast-list-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-list-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.toast-list-move {
  transition: transform 0.3s ease;
}
</style>

