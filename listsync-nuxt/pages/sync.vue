<template>
  <div class="space-y-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Sync Management
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          Trigger and monitor synchronization operations
        </p>
      </div>

      <Button
        variant="secondary"
        :icon="RefreshIcon"
        :loading="isRefreshing"
        @click="handleRefresh"
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
      <!-- Sync In Progress Banner -->
      <Transition name="slide-down">
        <Card 
          v-if="syncStore.isSyncing" 
          variant="default" 
          class="glass-card border-2 border-purple-500/50 bg-gradient-to-r from-purple-600/20 to-purple-500/10"
        >
          <div class="flex items-center gap-4 py-4">
            <div class="flex-shrink-0">
              <RefreshIcon class="w-6 h-6 text-purple-400 animate-spin" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-bold text-foreground">
                Sync in Progress
              </h3>
              <p class="text-sm text-muted-foreground">
                {{ syncStore.liveSyncStatus?.sync_type === 'full' ? 'Full sync' : 'Single list sync' }} is currently running. Please wait...
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="navigateTo('/logs')"
            >
              View Logs
            </Button>
          </div>
        </Card>
      </Transition>

      <!-- Sync Trigger -->
      <SyncTrigger
        :is-syncing="syncStore.isSyncing"
        :last-sync="systemStore.health?.last_sync || null"
        :next-sync="systemStore.health?.next_sync || null"
        @trigger-sync="handleTriggerSync"
      />

      <!-- Sync Status Cards -->
      <SyncStatusCards
        :current-status="syncStore.status"
        :last-sync="systemStore.health?.last_sync || null"
        :next-sync="systemStore.health?.next_sync || null"
        :is-syncing="syncStore.isSyncing"
      />

      <!-- Interval Configuration -->
      <IntervalConfig
        :current-interval="syncStore.syncInterval?.interval_hours || 24"
        :interval-source="syncStore.syncInterval?.source === 'env' ? 'env' : 'database'"
        @update-interval="handleUpdateInterval"
      />
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

