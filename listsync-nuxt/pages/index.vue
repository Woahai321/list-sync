<template>
  <div class="space-y-6 sm:space-y-8 px-2 sm:px-0">
    <!-- Welcome Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p class="text-muted-foreground mt-1.5 sm:mt-2 text-sm sm:text-base">
          Welcome back! Here's what's happening with your sync.
        </p>
      </div>

      <Button
        variant="primary"
        :icon="RefreshIcon"
        :loading="isRefreshing"
        @click="refreshData"
        class="w-full sm:w-auto touch-manipulation"
      >
        Refresh
      </Button>
    </div>

    <!-- Loading State with Skeletons -->
    <template v-if="isInitialLoading">
      <!-- Error Message (if any) -->
      <div v-if="loadError" class="mb-4 sm:mb-6">
        <Card variant="default" class="glass-card border-yellow-500/30">
          <div class="text-center py-4 sm:py-6 px-4">
            <p class="text-xs sm:text-sm text-yellow-400 mb-2">
              {{ loadError }}
            </p>
            <p class="text-xs text-muted-foreground">
              Waiting for first sync to complete... (Attempt {{ retryCount }}/{{ maxRetries }})
            </p>
            <p class="text-xs text-muted-foreground mt-1">
              Retrying in 5 seconds...
            </p>
          </div>
        </Card>
      </div>

      <!-- Dashboard Skeleton -->
      <div class="space-y-6 sm:space-y-8">
        <!-- Stats Overview Skeleton -->
        <div class="space-y-3 sm:space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
            <SkeletonLoader width="1/4" height="md" />
            <SkeletonLoader width="1/4" height="xs" />
          </div>
          <StatsOverviewSkeleton />
        </div>

        <!-- Recent Items Skeleton -->
        <div class="space-y-3 sm:space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
            <SkeletonLoader width="1/4" height="md" />
            <SkeletonLoader width="1/4" height="xs" />
          </div>
          <Card variant="default" class="glass-card">
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 sm:gap-4 p-2 sm:p-0">
              <PosterCardSkeleton v-for="i in 6" :key="`skeleton-${i}`" />
            </div>
          </Card>
        </div>

        <!-- System Status & Sync History Skeleton -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div class="space-y-3 sm:space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
              <SkeletonLoader width="1/3" height="md" />
              <SkeletonLoader width="1/4" height="xs" />
            </div>
            <SystemStatusSkeleton />
          </div>

          <div class="space-y-3 sm:space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
              <SkeletonLoader width="1/3" height="md" />
              <SkeletonLoader width="1/4" height="xs" />
            </div>
            <SyncHistoryOverviewSkeleton />
          </div>
        </div>
      </div>
    </template>

    <!-- Error State (after max retries) -->
    <Card v-else-if="loadError && retryCount >= maxRetries" variant="default" class="glass-card">
      <div class="text-center py-8 sm:py-12 px-4">
        <component :is="LayersIcon" :size="40" class="sm:w-12 sm:h-12 mx-auto text-red-400 mb-3 sm:mb-4" />
        <h3 class="text-base sm:text-lg font-semibold mb-2 text-foreground">Unable to Load Dashboard</h3>
        <p class="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4 px-2">
          {{ loadError }}
        </p>
        <p class="text-xs sm:text-sm text-muted-foreground mb-4 sm:mb-6 px-2">
          This usually happens when the first sync hasn't completed yet. Please wait a few moments and try again.
        </p>
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-2 sm:gap-3 px-2">
          <Button
            variant="primary"
            :icon="RefreshIcon"
            @click="() => { retryCount = 0; isInitialLoading = true; fetchDashboardData() }"
            class="w-full sm:w-auto touch-manipulation"
          >
            Retry Now
          </Button>
          <Button
            variant="secondary"
            @click="$router.push('/logs')"
            class="w-full sm:w-auto touch-manipulation"
          >
            View Logs
          </Button>
        </div>
      </div>
    </Card>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Sync Progress Indicator (Top) -->
      <SyncProgressIndicator />
      
      <!-- Stats Overview with View All Link -->
      <div v-if="statsStore.syncStats" class="space-y-3 sm:space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
          <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
            Statistics Overview
          </h2>
          <NuxtLink
            to="/items"
            class="text-xs sm:text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group touch-manipulation min-h-[44px] sm:min-h-0"
          >
            View All Items
            <component :is="ArrowRightIcon" :size="14" class="sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform" />
          </NuxtLink>
        </div>
        <StatsOverview :stats="statsStore.syncStats" />
      </div>

      <!-- Recent Items -->
      <div class="space-y-3 sm:space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
          <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
            Recently Synced
          </h2>
          <NuxtLink
            to="/items"
            class="text-xs sm:text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group touch-manipulation min-h-[44px] sm:min-h-0"
          >
            View All Items
            <component :is="ArrowRightIcon" :size="14" class="sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform" />
          </NuxtLink>
        </div>
        <Card variant="default" class="glass-card">
          <div v-if="recentItemsLoading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 sm:gap-4 p-2 sm:p-0">
            <PosterCardSkeleton v-for="i in 6" :key="`skeleton-${i}`" />
          </div>
          <div v-else-if="recentItems.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 sm:gap-4 p-2 sm:p-0">
            <PosterCard
              v-for="item in recentItems"
              :key="item.id"
              :item="item"
            />
          </div>
          <div v-else class="text-center py-8 sm:py-12 px-4">
            <p class="text-xs sm:text-sm text-muted-foreground">No items synced yet</p>
          </div>
        </Card>
      </div>

      <!-- System Status & Sync History -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <!-- System Status -->
        <div class="space-y-3 sm:space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
            <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
              System Status
            </h2>
            <NuxtLink
              to="/settings"
              class="text-xs sm:text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group touch-manipulation min-h-[44px] sm:min-h-0"
            >
              Settings
              <component :is="ArrowRightIcon" :size="14" class="sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform" />
            </NuxtLink>
          </div>
          <SystemStatus :health="systemStore.health" />
        </div>

        <!-- Sync History -->
        <div class="space-y-3 sm:space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0">
            <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
              Sync History
            </h2>
            <NuxtLink
              v-if="syncHistoryStats && syncHistoryStats.total_sessions > 0"
              to="/sync-history"
              class="text-xs sm:text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 group touch-manipulation min-h-[44px] sm:min-h-0"
            >
              View All History
              <component :is="ArrowRightIcon" :size="14" class="sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform" />
            </NuxtLink>
          </div>
          
          <!-- First Sync in Progress Message -->
          <Card v-if="!syncHistoryStats || syncHistoryStats.total_sessions === 0" variant="default" class="glass-card">
            <div class="text-center py-6 sm:py-8 px-4">
              <component :is="LayersIcon" :size="32" class="sm:w-10 sm:h-10 mx-auto text-purple-400 mb-2 sm:mb-3 animate-pulse" />
              <h3 class="text-sm sm:text-base font-semibold mb-1 sm:mb-1.5 text-foreground">First Sync in Progress</h3>
              <p class="text-xs sm:text-sm text-muted-foreground px-2">
                Your sync is running. History will appear here once the first sync completes.
              </p>
            </div>
          </Card>
          
          <!-- Sync History Stats (when available) -->
          <SyncHistoryOverview v-else :stats="syncHistoryStats" />
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

    <!-- Floating Quick Actions Menu -->
    <QuickActions />

    <!-- Sync In Progress Modal/Indicator -->
    <Transition name="fade">
      <div
        v-if="syncStore.isSyncing"
        class="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 left-4 sm:left-auto z-50 max-w-sm sm:max-w-sm mx-auto sm:mx-0"
      >
        <Card
          variant="default"
          class="glass-card border-2 border-purple-500/50 bg-gradient-to-r from-purple-600/20 to-purple-500/10 shadow-2xl"
        >
          <div class="flex items-center gap-2 sm:gap-3 p-3 sm:p-4">
            <div class="flex-shrink-0">
              <RefreshIcon class="w-4 h-4 sm:w-5 sm:h-5 text-purple-400 animate-spin" />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-xs sm:text-sm font-bold text-foreground truncate">
                Sync in Progress
              </h4>
              <p class="text-[10px] sm:text-xs text-muted-foreground truncate">
                {{ syncStore.liveSyncStatus?.sync_type === 'full' ? 'Full sync' : 'Single list sync' }} is running...
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="navigateTo('/logs')"
              class="flex-shrink-0 touch-manipulation text-xs sm:text-sm min-h-[36px] sm:min-h-[44px]"
            >
              View Logs
            </Button>
          </div>
        </Card>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Layers as LayersIcon,
  ArrowRight as ArrowRightIcon,
} from 'lucide-vue-next'
import { Transition, watch } from 'vue'
import type { RecentActivity, SyncHistoryStats } from '~/types'
import PosterCard from '~/components/items/PosterCard.vue'
import PosterCardSkeleton from '~/components/items/PosterCardSkeleton.vue'
import StatsOverviewSkeleton from '~/components/dashboard/StatsOverviewSkeleton.vue'
import SystemStatusSkeleton from '~/components/dashboard/SystemStatusSkeleton.vue'
import SyncHistoryOverviewSkeleton from '~/components/dashboard/SyncHistoryOverviewSkeleton.vue'
import SkeletonLoader from '~/components/ui/SkeletonLoader.vue'

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
const recentItems = ref<any[]>([])
const recentItemsLoading = ref(false)
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

// Fetch recent items (6 most recently synced)
const fetchRecentItems = async () => {
  recentItemsLoading.value = true
  try {
    const api = useApiService()
    const response: any = await api.getEnrichedItems(1, 6)
    
    if (response && response.items && Array.isArray(response.items)) {
      recentItems.value = response.items
    } else {
      recentItems.value = []
    }
  } catch (error) {
    console.error('Error fetching recent items:', error)
    recentItems.value = []
  } finally {
    recentItemsLoading.value = false
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
      fetchRecentItems().catch(err => {
        console.warn('Recent items fetch failed (will retry):', err)
        // Don't throw - items might not exist yet
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
      fetchRecentItems(),
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
  
  // Fetch sync status on mount
  syncStore.fetchLiveSyncStatus()
  
  // Auto-refresh every 30 seconds via polling (or 5 seconds when syncing)
  // Note: fetchRecentItems() excluded from polling to avoid distracting animations
  // Recent items only update after manual refresh or when a sync completes
  if (process.client) {
    let pollingInterval: NodeJS.Timeout | null = null
    
    const startPolling = () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
      
      const poll = async () => {
        await Promise.all([
          statsStore.fetchStats(),
          systemStore.checkHealth(),
          fetchSyncHistoryStats(),
          syncStore.fetchLiveSyncStatus(), // Include sync status
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
    
    // Prefetch items page data in background for instant navigation
    // Wait 2 seconds after dashboard loads, then prefetch
    setTimeout(() => {
      const itemsCache = useItemsCache()
      console.log('🚀 Dashboard: Prefetching items page for instant navigation...')
      itemsCache.prefetchPages([1, 2], 50)
    }, 2000)
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>

