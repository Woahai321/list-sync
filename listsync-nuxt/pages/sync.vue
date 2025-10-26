<template>
  <div class="space-y-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Sync Management
        </h1>
        <p class="text-muted-foreground mt-1">
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

// Trigger sync
const handleTriggerSync = async () => {
  try {
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Synchronization has been triggered')
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
  
  // Auto-refresh every 30 seconds (client-side only)
  if (process.client) {
    const { startPolling } = useSmartPolling(async () => {
      await Promise.all([
        syncStore.fetchLiveSyncStatus(),
        systemStore.checkHealth(),
      ])
    }, 30000)
    
    startPolling()
  }
})
</script>

