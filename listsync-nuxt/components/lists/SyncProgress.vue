<template>
  <Transition name="fade">
    <div v-if="isVisible" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <Card class="w-full max-w-md">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">Sync in Progress</h3>
            <Badge :variant="getStatusVariant(status)" size="sm">
              {{ status }}
            </Badge>
          </div>
        </template>

        <div class="space-y-6">
          <!-- Progress Ring -->
          <div class="flex items-center justify-center">
            <ProgressRing
              :progress="progressPercentage"
              :size="120"
              :stroke-width="8"
              :color="getProgressColor()"
            >
              <div class="text-center">
                <p class="text-2xl font-bold text-foreground">{{ progressPercentage }}%</p>
                <p class="text-xs text-muted-foreground mt-1">{{ itemsProcessed }}/{{ totalItems }}</p>
              </div>
            </ProgressRing>
          </div>

          <!-- Current Item -->
          <div v-if="currentItem" class="space-y-2">
            <p class="text-sm text-muted-foreground text-center">Processing:</p>
            <div class="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <p class="text-sm font-medium text-foreground text-center truncate" :title="currentItem">
                {{ currentItem }}
              </p>
            </div>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center p-3 rounded-lg bg-black/20">
              <p class="text-xs text-muted-foreground mb-1">Processed</p>
              <p class="text-lg font-bold text-foreground">{{ itemsProcessed }}</p>
            </div>

            <div class="text-center p-3 rounded-lg bg-black/20">
              <p class="text-xs text-muted-foreground mb-1">Total</p>
              <p class="text-lg font-bold text-foreground">{{ totalItems }}</p>
            </div>

            <div class="text-center p-3 rounded-lg bg-black/20">
              <p class="text-xs text-muted-foreground mb-1">Remaining</p>
              <p class="text-lg font-bold text-foreground">{{ remaining }}</p>
            </div>
          </div>

          <!-- Status Message -->
          <div v-if="statusMessage" class="flex items-start gap-2 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <component :is="InfoIcon" :size="16" class="text-blue-400 flex-shrink-0 mt-0.5" />
            <p class="text-xs text-muted-foreground">
              {{ statusMessage }}
            </p>
          </div>

          <!-- Error Messages -->
          <div v-if="errors.length > 0" class="space-y-2">
            <p class="text-sm text-red-400 font-medium">Errors ({{ errors.length }}):</p>
            <div class="max-h-32 overflow-y-auto custom-scrollbar space-y-1">
              <div
                v-for="(error, index) in errors"
                :key="index"
                class="p-2 rounded bg-red-500/10 border border-red-500/20"
              >
                <p class="text-xs text-red-300">{{ error }}</p>
              </div>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex items-center justify-between">
            <Button
              v-if="canCancel"
              variant="ghost"
              size="sm"
              :icon="XIcon"
              :disabled="isCancelling"
              @click="handleCancel"
            >
              Cancel
            </Button>

            <Button
              v-else
              variant="primary"
              size="sm"
              class="ml-auto"
              @click="handleClose"
            >
              Close
            </Button>
          </div>
        </template>
      </Card>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import {
  Info as InfoIcon,
  X as XIcon,
} from 'lucide-vue-next'

interface Props {
  isVisible: boolean
  status: string
  currentItem?: string | null
  itemsProcessed: number
  totalItems: number
  statusMessage?: string
  errors?: string[]
  canCancel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  currentItem: null,
  statusMessage: '',
  errors: () => [],
  canCancel: true,
})

const emit = defineEmits<{
  cancel: []
  close: []
}>()

// State
const isCancelling = ref(false)

// Computed
const progressPercentage = computed(() => {
  if (props.totalItems === 0) return 0
  return Math.round((props.itemsProcessed / props.totalItems) * 100)
})

const remaining = computed(() => {
  return Math.max(0, props.totalItems - props.itemsProcessed)
})

// Get status variant
const getStatusVariant = (status: string): 'success' | 'warning' | 'error' | 'info' => {
  const statusMap: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    running: 'warning',
    syncing: 'warning',
    completed: 'success',
    success: 'success',
    failed: 'error',
    error: 'error',
    cancelled: 'error',
  }
  return statusMap[status.toLowerCase()] || 'info'
}

// Get progress color
const getProgressColor = (): 'success' | 'warning' | 'error' | 'primary' => {
  if (props.status === 'completed' || props.status === 'success') return 'success'
  if (props.status === 'failed' || props.status === 'error') return 'error'
  if (progressPercentage.value > 75) return 'success'
  if (progressPercentage.value > 50) return 'warning'
  return 'primary'
}

// Handlers
const handleCancel = async () => {
  if (!confirm('Are you sure you want to cancel this sync?')) return

  isCancelling.value = true
  try {
    emit('cancel')
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    isCancelling.value = false
  }
}

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

