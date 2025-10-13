<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Sync History
        </h1>
        <p class="text-muted-foreground mt-1">
          View detailed history of all sync operations and their results
        </p>
      </div>

      <div class="flex items-center gap-3">
        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="isRefreshing"
          @click="handleRefresh"
        >
          Refresh
        </Button>
      </div>
    </div>

    <!-- Quick Stats -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card variant="hover" class="group/stat cursor-default">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <p class="text-sm text-muted-foreground mb-1">Total Syncs (7d)</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              <AnimatedCounter :value="stats.recent_stats.last_7d" />
            </p>
          </div>
          <div class="p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/stat:from-purple-500/30 group-hover/stat:to-purple-600/30 transition-all duration-300">
            <component :is="HistoryIcon" :size="28" class="text-purple-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
        </div>
      </Card>

      <Card variant="hover" class="group/stat cursor-default">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <p class="text-sm text-muted-foreground mb-1">Items Processed</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              <AnimatedCounter :value="stats.total_items_processed" />
            </p>
          </div>
          <div class="p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-600/20 group-hover/stat:from-blue-500/30 group-hover/stat:to-cyan-600/30 transition-all duration-300">
            <component :is="LayersIcon" :size="28" class="text-blue-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
        </div>
      </Card>

      <Card variant="hover" class="group/stat cursor-default">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <p class="text-sm text-muted-foreground mb-1">Success Rate</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ stats.success_rate.toFixed(1) }}<span class="text-xl">%</span>
            </p>
          </div>
          <div class="p-4 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-600/20 group-hover/stat:from-green-500/30 group-hover/stat:to-emerald-600/30 transition-all duration-300">
            <component :is="CheckCircleIcon" :size="28" class="text-green-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
        </div>
      </Card>

      <Card variant="hover" class="group/stat cursor-default">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <p class="text-sm text-muted-foreground mb-1">Avg Per Item</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ formatDuration(stats.avg_duration_seconds) }}
            </p>
          </div>
          <div class="p-4 rounded-xl bg-gradient-to-br from-orange-500/20 to-amber-600/20 group-hover/stat:from-orange-500/30 group-hover/stat:to-amber-600/30 transition-all duration-300">
            <component :is="ClockIcon" :size="28" class="text-orange-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <Card>
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Type Filter -->
          <div>
            <label class="block text-sm font-medium text-muted-foreground mb-2">
              Sync Type
            </label>
            <select
              v-model="filters.type"
              class="w-full px-4 py-2 rounded-lg bg-black/30 border border-purple-500/20 text-foreground focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all"
              @change="applyFilters"
            >
              <option value="">All Types</option>
              <option value="full">Full Sync</option>
              <option value="single">Single List</option>
            </select>
          </div>

          <!-- Date Range -->
          <div>
            <label class="block text-sm font-medium text-muted-foreground mb-2">
              Time Period
            </label>
            <select
              v-model="filters.period"
              class="w-full px-4 py-2 rounded-lg bg-black/30 border border-purple-500/20 text-foreground focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all"
              @change="applyFilters"
            >
              <option value="all">All Time</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>

          <!-- Clear Filters -->
          <div class="flex items-end">
            <Button
              v-if="hasActiveFilters"
              variant="ghost"
              :icon="XIcon"
              class="w-full"
              @click="clearFilters"
            >
              Clear Filters
            </Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- Loading State -->
    <div v-if="isLoading && sessions.length === 0" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading sync history..." />
    </div>

    <!-- Sessions List -->
    <template v-else>
      <div v-if="sessions.length > 0" class="space-y-4">
        <SyncSessionCard
          v-for="session in sessions"
          :key="session.id"
          :session="session"
        />
      </div>

      <!-- Empty State -->
      <EmptyState
        v-else
        :icon="HistoryIcon"
        title="No sync history found"
        :description="hasActiveFilters ? 'Try adjusting your filters' : 'No sync sessions have been recorded yet'"
        :action-label="hasActiveFilters ? 'Clear Filters' : undefined"
        @action="clearFilters"
      />

      <!-- Pagination -->
      <div v-if="totalSessions > sessions.length" class="flex justify-center">
        <Button
          variant="secondary"
          :loading="isLoadingMore"
          @click="loadMore"
        >
          Load More
        </Button>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  History as HistoryIcon,
  Layers as LayersIcon,
  CheckCircle2 as CheckCircleIcon,
  Clock as ClockIcon,
  X as XIcon,
} from 'lucide-vue-next'
import type { SyncHistorySession, SyncHistoryStats } from '~/types'

// Set page title
useHead({
  title: 'Sync History - ListSync',
})

// State
const isLoading = ref(true)
const isRefreshing = ref(false)
const isLoadingMore = ref(false)
const sessions = ref<SyncHistorySession[]>([])
const stats = ref<SyncHistoryStats | null>(null)
const totalSessions = ref(0)
const currentOffset = ref(0)
const limit = 20

// Filters
const filters = ref({
  type: '' as '' | 'full' | 'single',
  period: 'all' as string,
})

const hasActiveFilters = computed(() => {
  return filters.value.type !== '' || filters.value.period !== 'all'
})

// API
const { showSuccess, showError } = useToast()
const api = useApiService()

// Load data
const loadSyncHistory = async (append: boolean = false) => {
  try {
    if (!append) {
      isLoading.value = true
      currentOffset.value = 0
    } else {
      isLoadingMore.value = true
    }

    // Calculate date range from period
    let startDate: string | undefined
    const now = new Date()
    
    if (filters.value.period === '24h') {
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      startDate = yesterday.toISOString()
    } else if (filters.value.period === '7d') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      startDate = weekAgo.toISOString()
    } else if (filters.value.period === '30d') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      startDate = monthAgo.toISOString()
    }

    const response = await api.getSyncHistory(
      limit,
      currentOffset.value,
      filters.value.type || undefined,
      startDate
    )

    if (append) {
      sessions.value = [...sessions.value, ...response.sessions]
    } else {
      sessions.value = response.sessions
    }

    totalSessions.value = response.total
    currentOffset.value += response.sessions.length
  } catch (error: any) {
    console.error('Error loading sync history:', error)
    showError('Failed to load sync history', error.message)
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
  }
}

const loadStats = async () => {
  try {
    stats.value = await api.getSyncHistoryStats()
  } catch (error: any) {
    console.error('Error loading sync history stats:', error)
  }
}

// Handlers
const handleRefresh = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      loadSyncHistory(),
      loadStats(),
    ])
    showSuccess('Sync history refreshed')
  } catch (error: any) {
    showError('Failed to refresh', error.message)
  } finally {
    isRefreshing.value = false
  }
}

const loadMore = async () => {
  await loadSyncHistory(true)
}

const applyFilters = () => {
  loadSyncHistory()
}

const clearFilters = () => {
  filters.value.type = ''
  filters.value.period = 'all'
  loadSyncHistory()
}


// Utilities
const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

// Initialize
onMounted(async () => {
  await Promise.all([
    loadSyncHistory(),
    loadStats(),
  ])
})
</script>

