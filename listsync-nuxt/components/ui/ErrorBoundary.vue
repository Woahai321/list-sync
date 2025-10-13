<template>
  <div>
    <template v-if="!error">
      <slot />
    </template>
    
    <template v-else>
      <Card variant="default" class="my-8">
        <div class="text-center py-8">
          <!-- Error Icon -->
          <div class="mb-4 flex justify-center">
            <div class="p-4 rounded-full bg-red-500/20">
              <AlertTriangleIcon :size="48" class="text-red-400" />
            </div>
          </div>
          
          <!-- Error Message -->
          <h3 class="text-xl font-bold text-foreground mb-2">
            Something Went Wrong
          </h3>
          <p class="text-muted-foreground mb-6">
            {{ errorMessage }}
          </p>
          
          <!-- Technical Details (dev only) -->
          <div v-if="showDetails" class="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-left max-w-2xl mx-auto">
            <p class="text-sm font-mono text-red-300 break-all">
              {{ error.toString() }}
            </p>
          </div>
          
          <!-- Actions -->
          <div class="flex items-center justify-center gap-3">
            <Button
              variant="primary"
              :icon="RefreshCwIcon"
              @click="handleRetry"
            >
              Try Again
            </Button>
            
            <Button
              variant="ghost"
              :icon="HomeIcon"
              @click="handleGoHome"
            >
              Go to Dashboard
            </Button>
          </div>
        </div>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  AlertTriangle as AlertTriangleIcon,
  RefreshCw as RefreshCwIcon,
  Home as HomeIcon,
} from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    fallbackMessage?: string
  }>(),
  {
    fallbackMessage: 'An unexpected error occurred. Please try reloading the page.',
  }
)

const error = ref<Error | null>(null)
const showDetails = process.dev

const errorMessage = computed(() => {
  if (!error.value) return props.fallbackMessage
  return error.value.message || props.fallbackMessage
})

// Catch errors from child components
onErrorCaptured((err) => {
  console.error('Error boundary caught:', err)
  error.value = err as Error
  return false // Prevent error from propagating
})

const handleRetry = () => {
  error.value = null
}

const handleGoHome = () => {
  navigateTo('/')
}
</script>

