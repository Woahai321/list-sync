<template>
  <div
    v-if="show"
    class="fixed bottom-4 right-4 z-50 animate-slide-up"
  >
    <Card
      :class="[
        'glass-card border-2 shadow-lg max-w-sm',
        isConnected ? 'border-success/50' : 'border-danger/50'
      ]"
    >
      <div class="flex items-start gap-3">
        <!-- Status Icon -->
        <div
          :class="[
            'p-2 rounded-lg flex-shrink-0',
            isConnected ? 'bg-success/10' : 'bg-danger/10'
          ]"
        >
          <component
            :is="statusIcon"
            :class="[
              'w-5 h-5',
              isConnected ? 'text-success' : 'text-danger'
            ]"
          />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-2 mb-1">
            <h4
              :class="[
                'font-semibold text-sm',
                isConnected ? 'text-success' : 'text-danger'
              ]"
            >
              {{ statusTitle }}
            </h4>
            <button
              class="text-muted-foreground hover:text-foreground transition-colors"
              @click="hide"
            >
              <XIcon class="w-4 h-4" />
            </button>
          </div>

          <p class="text-xs text-muted-foreground mb-2">
            {{ statusMessage }}
          </p>

          <!-- Last Update -->
          <p v-if="lastUpdate && isConnected" class="text-xs text-muted-foreground flex items-center gap-1">
            <ClockIcon class="w-3 h-3" />
            Last update: {{ formatRelativeTime(lastUpdate) }}
          </p>

          <!-- Retry Button -->
          <Button
            v-if="!isConnected && showRetry"
            variant="danger"
            size="sm"
            class="mt-2"
            :loading="isRetrying"
            @click="handleRetry"
          >
            <RefreshIcon class="w-3 h-3 mr-2" />
            Retry Connection
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  X as XIcon,
  Clock as ClockIcon,
  RefreshCw as RefreshIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow } from 'date-fns'

interface Props {
  isConnected: boolean
  lastUpdate?: Date | string | null
  errorMessage?: string
  showRetry?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  lastUpdate: null,
  errorMessage: '',
  showRetry: true,
})

const emit = defineEmits<{
  retry: []
  hide: []
}>()

const show = ref(true)
const isRetrying = ref(false)

// Status computed
const statusIcon = computed(() => {
  return props.isConnected ? WifiIcon : WifiOffIcon
})

const statusTitle = computed(() => {
  return props.isConnected ? 'Connected' : 'Connection Lost'
})

const statusMessage = computed(() => {
  if (props.isConnected) {
    return 'Real-time updates are active'
  }
  return props.errorMessage || 'Failed to connect to the server'
})

// Format relative time
const formatRelativeTime = (timestamp: Date | string) => {
  try {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Handle retry
const handleRetry = async () => {
  isRetrying.value = true
  emit('retry')
  
  // Reset after a delay
  setTimeout(() => {
    isRetrying.value = false
  }, 2000)
}

// Hide
const hide = () => {
  show.value = false
  emit('hide')
}

// Watch connection status
watch(
  () => props.isConnected,
  (newValue) => {
    // Show notification when connection changes
    show.value = true
    
    // Auto-hide success notification after 5 seconds
    if (newValue) {
      setTimeout(() => {
        show.value = false
      }, 5000)
    }
  }
)
</script>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}
</style>

