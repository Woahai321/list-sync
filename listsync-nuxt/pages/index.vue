<template>
  <div class="space-y-8">
    <!-- Welcome Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Dashboard
        </h1>
        <p class="text-muted-foreground mt-1">
          Welcome back! Here's what's happening with your sync.
        </p>
      </div>

      <Button
        variant="primary"
        :icon="RefreshIcon"
        :loading="isRefreshing"
        @click="refreshData"
      >
        Refresh
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="isInitialLoading" class="flex items-center justify-center py-20">
      <div class="text-center space-y-4">
        <LoadingSpinner size="lg" :text="loadError ? 'Retrying...' : 'Loading dashboard...'" />
        <div v-if="loadError" class="space-y-2">
          <p class="text-sm text-yellow-400">
            {{ loadError }}
          </p>
          <p class="text-xs text-muted-foreground">
            Waiting for first sync to complete... (Attempt {{ retryCount }}/{{ maxRetries }})
          </p>
          <p class="text-xs text-muted-foreground">
            Retrying in 5 seconds...
          </p>
        </div>
        <p v-else class="text-sm text-muted-foreground">
          Initializing dashboard components...
        </p>
      </div>
    </div>

    <!-- Error State (after max retries) -->
    <Card v-else-if="loadError && retryCount >= maxRetries" variant="default" class="glass-card">
      <div class="text-center py-12">
        <component :is="LayersIcon" :size="48" class="mx-auto text-red-400 mb-4" />
        <h3 class="text-lg font-semibold mb-2 text-foreground">Unable to Load Dashboard</h3>
        <p class="text-sm text-muted-foreground mb-4">
          {{ loadError }}
        </p>
        <p class="text-sm text-muted-foreground mb-6">
          This usually happens when the first sync hasn't completed yet. Please wait a few moments and try again.
        </p>
        <div class="flex items-center justify-center gap-3">
          <Button
            variant="primary"
            :icon="RefreshIcon"
            @click="() => { retryCount = 0; isInitialLoading = true; fetchDashboardData() }"
          >
            Retry Now
          </Button>
          <Button
            variant="secondary"
            @click="$router.push('/logs')"
          >
            View Logs
          </Button>
        </div>
      </div>
    </Card>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Quick Actions -->
      <QuickActions />

      <!-- Stats Overview with View All Link -->
      <div v-if="statsStore.syncStats" class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-foreground titillium-web-bold">
            Statistics Overview
          </h2>
          <NuxtLink
            to="/items"
            class="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group"
          >
            View All Items
            <component :is="ArrowRightIcon" :size="16" class="group-hover:translate-x-1 transition-transform" />
          </NuxtLink>
        </div>
        <StatsOverview :stats="statsStore.syncStats" />
      </div>

      <!-- Sync History Overview -->
      <div v-if="syncHistoryStats" class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-foreground titillium-web-bold">
            Sync History
          </h2>
          <NuxtLink
            to="/sync-history"
            class="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group"
          >
            View All History
            <component :is="ArrowRightIcon" :size="16" class="group-hover:translate-x-1 transition-transform" />
          </NuxtLink>
        </div>
        <SyncHistoryOverview :stats="syncHistoryStats" />
      </div>

      <!-- System Health & Recent Activity with Headers -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- System Status -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold text-foreground titillium-web-bold">
              System Status
            </h2>
            <NuxtLink
              to="/settings"
              class="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group"
            >
              Settings
              <component :is="ArrowRightIcon" :size="16" class="group-hover:translate-x-1 transition-transform" />
            </NuxtLink>
          </div>
          <SystemStatus :health="systemStore.health" />
        </div>

        <!-- Recent Activity -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold text-foreground titillium-web-bold">
              Recent Activity
            </h2>
            <NuxtLink
              to="/recent-activity"
              class="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group"
            >
              View All
              <component :is="ArrowRightIcon" :size="16" class="group-hover:translate-x-1 transition-transform" />
            </NuxtLink>
          </div>
          <RecentActivity :activities="recentActivities" :loading="activitiesLoading" />
        </div>
      </div>

      <!-- Empty State -->
      <EmptyState
        v-if="!statsStore.hasStats"
        :icon="LayersIcon"
        title="No Lists Configured"
        description="Add your first list to start syncing media to Overseerr"
        action-label="Add Your First List"
        @action="$router.push('/lists?action=add')"
      />
    </template>

    <!-- Connection Status - Hidden (polling works fine) -->
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Layers as LayersIcon,
  ArrowRight as ArrowRightIcon,
} from 'lucide-vue-next'
import type { RecentActivity, SyncHistoryStats } from '~/types'

const statsStore = useStatsStore()
const systemStore = useSystemStore()
const syncStore = useSyncStore()
const { showSuccess, showError } = useToast()

// Polling-based updates (SSE disabled - backend doesn't support it yet)
const showConnectionStatus = ref(false)

// Set page title
useHead({
  title: 'Dashboard - ListSync',
})

// State
const isInitialLoading = ref(true)
const isRefreshing = ref(false)
const recentActivities = ref<RecentActivity[]>([])
const activitiesLoading = ref(false)
const syncHistoryStats = ref<SyncHistoryStats | null>(null)
const loadError = ref<string | null>(null)
const retryCount = ref(0)
const maxRetries = 10 // Retry for ~50 seconds (10 retries * 5 seconds)

// Fetch recent activities
const fetchRecentActivities = async () => {
  activitiesLoading.value = true
  try {
    const api = useApiService()
    const response: any = await api.getRecentActivity(20, 1) // Use max allowed limit, page 1
    
    // Map API response to component format - limit to 4 for dashboard
    if (response && response.items && Array.isArray(response.items)) {
      recentActivities.value = response.items.slice(0, 4).map((item: any, index: number) => ({
        id: index,
        title: item.title || 'Unknown',
        media_type: 'movie', // API doesn't return this, default to movie
        status: item.status || 'unknown',
        last_synced: item.timestamp || new Date().toISOString(),
        action: item.status || 'pending'
      }))
    } else {
      recentActivities.value = []
    }
  } catch (error) {
    console.error('Error fetching recent activities:', error)
    recentActivities.value = []
  } finally {
    activitiesLoading.value = false
  }
}

// Fetch sync history stats
const fetchSyncHistoryStats = async () => {
  try {
    const api = useApiService()
    syncHistoryStats.value = await api.getSyncHistoryStats()
  } catch (error) {
    console.error('Error fetching sync history stats:', error)
    syncHistoryStats.value = null
  }
}

// Fetch all dashboard data
const fetchDashboardData = async () => {
  try {
    loadError.value = null
    
    await Promise.all([
      statsStore.fetchStats().catch(err => {
        console.warn('Stats fetch failed (will retry):', err)
        throw err
      }),
      systemStore.checkHealth().catch(err => {
        console.warn('Health check failed (will retry):', err)
        throw err
      }),
      systemStore.checkOverseerr().catch(err => {
        console.warn('Overseerr check failed (will retry):', err)
        // Don't throw - Overseerr might not be configured yet
      }),
      syncStore.fetchSyncInterval().catch(err => {
        console.warn('Sync interval fetch failed (will retry):', err)
        // Don't throw - sync interval might not be set yet
      }),
      fetchRecentActivities().catch(err => {
        console.warn('Recent activities fetch failed (will retry):', err)
        // Don't throw - activities might not exist yet
      }),
      fetchSyncHistoryStats().catch(err => {
        console.warn('Sync history fetch failed (will retry):', err)
        // Don't throw - history might not exist yet
      }),
    ])
    
    // Successfully loaded
    retryCount.value = 0
    loadError.value = null
  } catch (error: any) {
    console.error('Error loading dashboard:', error)
    loadError.value = error.message || 'Failed to load dashboard data'
    
    // Retry if we haven't exceeded max retries
    if (retryCount.value < maxRetries) {
      retryCount.value++
      console.log(`Retrying dashboard load (attempt ${retryCount.value}/${maxRetries})...`)
      
      // Retry after 5 seconds
      setTimeout(() => {
        fetchDashboardData()
      }, 5000)
    } else {
      console.error('Max retries exceeded, giving up')
      isInitialLoading.value = false
    }
  } finally {
    // Only stop loading if we succeeded or exceeded retries
    if (loadError.value === null || retryCount.value >= maxRetries) {
      isInitialLoading.value = false
    }
  }
}

// Refresh data
const refreshData = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      statsStore.refresh(),
      systemStore.refresh(),
      fetchRecentActivities(),
      fetchSyncHistoryStats(),
    ])
    showSuccess('Dashboard refreshed')
  } catch (error: any) {
    showError('Failed to refresh', error.message)
  } finally {
    isRefreshing.value = false
  }
}

// Fetch data on mount and setup polling
onMounted(() => {
  fetchDashboardData()
  
  // Auto-refresh every 30 seconds via polling
  if (process.client) {
    const { startPolling } = useSmartPolling(async () => {
      await statsStore.fetchStats()
      await systemStore.checkHealth()
      await fetchRecentActivities()
      await fetchSyncHistoryStats()
    }, 30000)
    
    startPolling()
  }
})
</script>

