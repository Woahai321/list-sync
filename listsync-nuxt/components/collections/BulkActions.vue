<template>
  <Transition name="slide-up">
    <div v-if="selectedCount > 0" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
      <Card class="shadow-2xl min-w-[400px] max-w-[90vw]">
        <div class="flex items-center justify-between gap-6">
          <!-- Selection Info -->
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-purple-500/20">
              <component :is="CheckSquareIcon" :size="20" class="text-purple-400" />
            </div>
            <div>
              <p class="text-sm font-semibold text-foreground">
                {{ selectedCount }} collection{{ selectedCount > 1 ? 's' : '' }} selected
              </p>
              <button
                type="button"
                class="text-xs text-muted-foreground hover:text-foreground transition-colors touch-manipulation"
                @click="$emit('deselect-all')"
              >
                Deselect all
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              :icon="RefreshCwIcon"
              :loading="isSyncing"
              :disabled="isSyncing"
              @click="handleBulkSync"
              class="touch-manipulation"
            >
              Sync {{ selectedCount }}
            </Button>

            <button
              type="button"
              class="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground touch-manipulation"
              :disabled="isSyncing"
              @click="$emit('deselect-all')"
            >
              <component :is="XIcon" :size="18" />
            </button>
          </div>
        </div>

        <!-- Progress Bar (when syncing) -->
        <div v-if="isSyncing && progress > 0" class="mt-4 pt-4 border-t border-purple-500/10">
          <div class="flex items-center justify-between text-xs text-muted-foreground mb-2">
            <span>Syncing collections...</span>
            <span>{{ progress }}% ({{ completed }}/{{ selectedCount }})</span>
          </div>
          <div class="h-2 bg-black/40 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-300"
              :style="{ width: `${progress}%` }"
            />
          </div>
        </div>
      </Card>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import {
  CheckSquare as CheckSquareIcon,
  RefreshCw as RefreshCwIcon,
  X as XIcon,
} from 'lucide-vue-next'

interface Props {
  selectedCount: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'bulk-sync': []
  'deselect-all': []
}>()

const { showSuccess, showError } = useToast()

// State
const isSyncing = ref(false)
const progress = ref(0)
const completed = ref(0)

// Handlers
const handleBulkSync = async () => {
  isSyncing.value = true
  progress.value = 0
  completed.value = 0

  try {
    emit('bulk-sync')
  } catch (error: any) {
    showError('Bulk Sync Failed', error.message)
    isSyncing.value = false
    progress.value = 0
    completed.value = 0
  }
}

// Expose methods for parent to update progress
defineExpose({
  setProgress: (value: number, completedValue: number) => {
    progress.value = value
    completed.value = completedValue
  },
  setSyncing: (value: boolean) => {
    isSyncing.value = value
  }
})
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translate(-50%, 20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}
</style>

