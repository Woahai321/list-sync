<template>
  <Card 
    variant="default" 
    class="overflow-hidden relative group/card"
    :class="[
      isRunning ? 'border-green-500/40' : 'border-purple-500/30'
    ]"
  >
    <!-- Animated gradient background -->
    <div 
      class="absolute inset-0 opacity-60 group-hover/card:opacity-80 transition-opacity duration-500"
      :class="[
        isRunning 
          ? 'bg-gradient-to-br from-green-600/10 via-green-500/5 to-transparent' 
          : 'bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent'
      ]"
    />
    
    <div class="relative py-3 px-4">
      <div class="flex items-center justify-between gap-3">
        <!-- Status Icon and Text -->
        <div class="flex items-center gap-2.5 flex-1 min-w-0">
          <div 
            class="relative"
            :class="isRunning ? 'animate-pulse' : ''"
          >
            <div 
              v-if="isRunning"
              class="absolute inset-0 rounded-full animate-ping"
              :class="[
                'bg-green-500/20'
              ]"
            />
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="[
                isRunning 
                  ? 'bg-green-500/20 border-2 border-green-500/40' 
                  : 'bg-purple-500/20 border-2 border-purple-500/30'
              ]"
            >
              <component 
                :is="isRunning ? RefreshIcon : CheckCircleIcon" 
                :size="16" 
                :class="[
                  isRunning 
                    ? 'text-green-400 animate-spin' 
                    : 'text-purple-400'
                ]"
              />
            </div>
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span 
                class="text-xs sm:text-sm font-bold uppercase tracking-wide"
                :class="[
                  isRunning ? 'text-green-400' : 'text-purple-300'
                ]"
              >
                {{ isRunning ? 'Sync In Progress' : 'Sync Idle' }}
              </span>
              <span 
                v-if="syncType"
                class="text-[10px] sm:text-xs px-1.5 py-0.5 rounded-full"
                :class="[
                  isRunning 
                    ? 'bg-green-500/20 border border-green-500/30 text-green-300' 
                    : 'bg-purple-500/20 border border-purple-500/30 text-purple-300'
                ]"
              >
                {{ syncType === 'full' ? 'Full' : 'Single' }}
              </span>
              
              <!-- Next Sync Countdown (only show when idle) -->
              <span 
                v-if="!isRunning && nextSyncCountdown"
                class="text-xs text-muted-foreground flex items-center gap-1"
              >
                <component :is="ClockIcon" :size="12" />
                Next: {{ nextSyncCountdown }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <!-- Sync Now Button (only show when idle) -->
          <Button
            v-if="!isRunning"
            variant="primary"
            size="sm"
            :icon="PlayIcon"
            :loading="isTriggeringSync"
            @click="handleSyncNow"
            class="text-xs sm:text-sm"
          >
            <span class="hidden sm:inline">Sync Now</span>
            <span class="sm:hidden">Sync</span>
          </Button>
          
          <!-- View Logs Button (only show when running) -->
          <Button
            v-if="isRunning"
            variant="ghost"
            size="sm"
            @click="$router.push('/logs')"
            class="flex-shrink-0 text-xs sm:text-sm"
          >
            View Logs
          </Button>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Play as PlayIcon,
  Clock as ClockIcon,
} from 'lucide-vue-next'

const syncStore = useSyncStore()
const systemStore = useSystemStore()
const { showSuccess, showError } = useToast()

// Debounced running state to prevent flickering
const isRunningDebounced = ref(false)
let debounceTimeout: NodeJS.Timeout | null = null

// Watch sync store and debounce changes to prevent flickering
watch(() => syncStore.isSyncing, (newValue) => {
  if (newValue) {
    // When sync starts, immediately show indicator
    isRunningDebounced.value = true
    if (debounceTimeout) {
      clearTimeout(debounceTimeout)
      debounceTimeout = null
    }
  } else {
    // When sync stops, keep showing for 3 seconds to prevent flicker
    // This helps if there's a brief moment where the API returns idle incorrectly
    if (debounceTimeout) {
      clearTimeout(debounceTimeout)
    }
    debounceTimeout = setTimeout(() => {
      // Only hide if still not running (double-check)
      if (!syncStore.isSyncing) {
        isRunningDebounced.value = false
      } else {
        // If sync started again during the delay, keep showing
        isRunningDebounced.value = true
      }
    }, 3000) // Keep showing for 3 seconds after sync appears to stop
  }
}, { immediate: true })

// Use debounced state for display
const isRunning = computed(() => isRunningDebounced.value)

const syncType = computed(() => syncStore.liveSyncStatus?.sync_type)

// Get next sync time from system store
const nextSync = computed(() => systemStore.health?.next_sync || null)

// Countdown to next sync
const nextSyncCountdown = ref('')
const isTriggeringSync = ref(false)

const updateCountdown = () => {
  if (!nextSync.value) {
    nextSyncCountdown.value = ''
    return
  }

  try {
    const now = new Date()
    const next = new Date(nextSync.value)
    const diff = next.getTime() - now.getTime()

    if (diff <= 0) {
      nextSyncCountdown.value = 'Due now'
      return
    }

    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)

    if (hours > 0) {
      nextSyncCountdown.value = `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      nextSyncCountdown.value = `${minutes}m ${seconds}s`
    } else {
      nextSyncCountdown.value = `${seconds}s`
    }
  } catch {
    nextSyncCountdown.value = ''
  }
}

// Handle sync now button
const handleSyncNow = async () => {
  if (isTriggeringSync.value || isRunning.value) return
  
  try {
    isTriggeringSync.value = true
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Synchronization has been triggered')
  } catch (error: any) {
    showError('Sync Failed', error.message || 'Failed to start sync')
  } finally {
    isTriggeringSync.value = false
  }
}

// Update countdown every second when idle
onMounted(() => {
  if (process.client) {
    updateCountdown()
    const interval = setInterval(() => {
      if (!isRunning.value) {
        updateCountdown()
      }
    }, 1000)
    
    onUnmounted(() => clearInterval(interval))
  }
})

// Watch for next sync changes
watch(() => nextSync.value, () => {
  updateCountdown()
})

onUnmounted(() => {
  if (debounceTimeout) {
    clearTimeout(debounceTimeout)
    debounceTimeout = null
  }
})
</script>

