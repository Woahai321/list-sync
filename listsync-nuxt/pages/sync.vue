<template>
  <div class="space-y-6 sm:space-y-8 px-2 sm:px-0">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Sync Management
        </h1>
        <p class="text-muted-foreground mt-1.5 sm:mt-2 text-sm sm:text-base">
          Trigger and monitor synchronization operations
        </p>
      </div>

      <Button
        variant="primary"
        :icon="RefreshIcon"
        :loading="isRefreshing"
        @click="handleRefresh"
        class="w-full sm:w-auto touch-manipulation"
      >
        Refresh
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="isInitialLoading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading sync data..." />
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Sync Control Section -->
      <div class="space-y-3 sm:space-y-4">
        <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
          Sync Control
        </h2>
        <SyncTrigger
          :is-syncing="syncStore.isSyncing"
          :last-sync="systemStore.health?.last_sync || null"
          :next-sync="systemStore.health?.next_sync || null"
          @trigger-sync="handleTriggerSync"
          @stop-sync="handleStopSync"
        />
      </div>

      <!-- Sync Status Section -->
      <div class="space-y-3 sm:space-y-4">
        <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
          Sync Status
        </h2>
        <SyncStatusCards
          :current-status="syncStore.status"
          :last-sync="systemStore.health?.last_sync || null"
          :next-sync="systemStore.health?.next_sync || null"
          :is-syncing="syncStore.isSyncing"
        />
      </div>

      <!-- Sync Configuration Section -->
      <div class="space-y-3 sm:space-y-4">
        <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
          Sync Configuration
        </h2>
        <IntervalConfig
          :current-interval="syncStore.syncInterval?.interval_hours || 24"
          :interval-source="syncStore.syncInterval?.source === 'env' ? 'env' : 'database'"
          @update-interval="handleUpdateInterval"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
} from 'lucide-vue-next'
import { watch } from 'vue'

const syncStore = useSyncStore()
const systemStore = useSystemStore()
const { showSuccess, showError } = useToast()
const api = useApiService()

// Set page title
useHead({
  title: 'Sync Management - ListSync',
})

// State
const isInitialLoading = ref(true)
const isRefreshing = ref(false)

// Fetch initial data
const fetchSyncData = async () => {
  try {
    await Promise.all([
      syncStore.fetchLiveSyncStatus(),
      syncStore.fetchSyncInterval(),
      systemStore.checkHealth(), // Get last_sync and next_sync
    ])
  } catch (error) {
    console.error('Error loading sync data:', error)
  } finally {
    isInitialLoading.value = false
  }
}

// Refresh data
const handleRefresh = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      syncStore.fetchLiveSyncStatus(),
      syncStore.fetchSyncInterval(),
      systemStore.checkHealth(),
    ])
    showSuccess('Sync data refreshed')
  } catch (error: any) {
    showError('Refresh Failed', error.message)
  } finally {
    isRefreshing.value = false
  }
}

// Trigger sync and navigate to logs
const handleTriggerSync = async () => {
  try {
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Synchronization has been triggered')
    navigateTo('/logs')
  } catch (error: any) {
    showError('Sync Failed', error.message)
  }
}

// Stop/cancel running sync
const handleStopSync = async () => {
  try {
    await syncStore.stopSync()
    showSuccess('Sync Stopped', 'Synchronization has been terminated immediately')
  } catch (error: any) {
    showError('Stop Failed', error.message)
  }
}

// Update interval
const handleUpdateInterval = async (newInterval: number) => {
  try {
    await syncStore.updateSyncInterval(newInterval)
    showSuccess('Interval Updated', `Sync interval set to ${newInterval} hours`)
  } catch (error: any) {
    showError('Update Failed', error.message)
  }
}

// Fetch data on mount
onMounted(async () => {
  await fetchSyncData()
  
  // Auto-refresh every 5 seconds when syncing, 30 seconds otherwise (client-side only)
  if (process.client) {
    let pollingInterval: NodeJS.Timeout | null = null
    
    const startPolling = () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
      
      const poll = async () => {
        await Promise.all([
          syncStore.fetchLiveSyncStatus(),
          systemStore.checkHealth(),
        ])
      }
      
      // Poll immediately
      poll()
      
      // Then poll at dynamic interval
      const updateInterval = () => {
        const interval = syncStore.isSyncing ? 5000 : 30000
        if (pollingInterval) {
          clearInterval(pollingInterval)
        }
        pollingInterval = setInterval(poll, interval)
      }
      
      updateInterval()
      
      // Watch for sync status changes and update interval
      watch(() => syncStore.isSyncing, () => {
        updateInterval()
      }, { immediate: false })
    }
    
    startPolling()
    
    // Cleanup on unmount
    onUnmounted(() => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    })
  }
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

