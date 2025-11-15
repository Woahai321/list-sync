<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Recent Activity
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          Latest sync activities and media processing
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        @click="navigateTo('/')"
      >
        ← Back to Dashboard
      </Button>
    </div>

    <!-- Stats Summary -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="p-3">
          <div class="flex items-center gap-2.5">
            <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
              <CheckCircle2Icon class="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground leading-none">{{ successCount }}</p>
              <p class="text-[10px] text-muted-foreground font-medium">Successful</p>
            </div>
          </div>
        </div>
      </Card>

      <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="p-3">
          <div class="flex items-center gap-2.5">
            <div class="p-2 rounded-lg bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28">
              <XCircleIcon class="w-4 h-4 text-purple-300" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground leading-none">{{ failedCount }}</p>
              <p class="text-[10px] text-muted-foreground font-medium">Failed</p>
            </div>
          </div>
        </div>
      </Card>

      <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="p-3">
          <div class="flex items-center gap-2.5">
            <div class="p-2 rounded-lg bg-gradient-to-br from-purple-400/20 to-purple-300/10 border border-purple-300/30">
              <AlertCircleIcon class="w-4 h-4 text-purple-200" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground leading-none">{{ notFoundCount }}</p>
              <p class="text-[10px] text-muted-foreground font-medium">Not Found</p>
            </div>
          </div>
        </div>
      </Card>

      <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="p-3">
          <div class="flex items-center gap-2.5">
            <div class="p-2 rounded-lg bg-gradient-to-br from-purple-300/20 to-purple-200/10 border border-purple-200/30">
              <ActivityIcon class="w-4 h-4 text-purple-100" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground leading-none">{{ activities.length }}</p>
              <p class="text-[10px] text-muted-foreground font-medium">Total Items</p>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="p-3">
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="filter in filters"
            :key="filter.value"
            :class="[
              'px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-all',
              selectedFilter === filter.value
                ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30'
                : 'bg-purple-500/5 text-purple-400/70 border border-purple-500/10 hover:bg-purple-500/10 hover:text-purple-300 hover:border-purple-500/20'
            ]"
            @click="selectedFilter = filter.value"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>
    </Card>

    <!-- Activity List -->
    <Card class="border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="divide-y divide-purple-500/10">
        <!-- Loading State -->
        <div v-if="loading" class="p-8 text-center">
          <div class="inline-flex items-center gap-2 text-muted-foreground">
            <div class="animate-spin rounded-full h-5 w-5 border-2 border-purple-500 border-t-transparent" />
            <span>Loading activities...</span>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredActivities.length === 0" class="p-8 text-center">
          <ActivityIcon class="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" />
          <p class="text-muted-foreground">No activities found</p>
        </div>

        <!-- Activity Items -->
        <div
          v-for="(activity, index) in filteredActivities"
          :key="index"
          class="p-4 hover:bg-white/5 transition-colors"
        >
          <div class="flex items-center gap-4">
            <!-- Status Icon -->
            <div :class="['p-2 rounded-lg', getStatusBg(activity.status)]">
              <component :is="getStatusIcon(activity.status)" :class="['w-5 h-5', getStatusColor(activity.status)]" />
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <p class="font-medium text-foreground truncate">{{ activity.title }}</p>
                <Badge v-if="activity.media_type" variant="secondary" class="text-xs">
                  {{ activity.media_type }}
                </Badge>
              </div>
              <p class="text-xs text-muted-foreground">
                {{ getActionText(activity.status) }}
              </p>
            </div>

            <!-- Time -->
            <div class="text-right">
              <TimeAgo :timestamp="activity.timestamp" class="text-xs text-muted-foreground" />
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="filteredActivities.length > 0" class="p-4 border-t border-border">
        <div class="flex items-center justify-between">
          <p class="text-sm text-muted-foreground">
            Showing {{ filteredActivities.length }} of {{ activities.length }} activities
          </p>
          <Button
            v-if="activities.length > filteredActivities.length"
            variant="secondary"
            size="sm"
            @click="loadMore"
          >
            Load More
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  CheckCircle2 as CheckCircle2Icon,
  XCircle as XCircleIcon,
  AlertCircle as AlertCircleIcon,
  Activity as ActivityIcon,
  Film as FilmIcon,
  Tv as TvIcon,
} from 'lucide-vue-next'

interface Activity {
  title: string
  status: string
  timestamp: string
  media_type: string
}

const loading = ref(true)
const activities = ref<Activity[]>([])
const selectedFilter = ref<string>('all')

const filters = [
  { label: 'All', value: 'all' },
  { label: 'Success', value: 'success' },
  { label: 'Failed', value: 'failed' },
  { label: 'Not Found', value: 'not_found' },
  { label: 'Movies', value: 'movie' },
  { label: 'TV Shows', value: 'tv' },
]

// Fetch activities with pagination to get more than 20 items
const fetchActivities = async () => {
  loading.value = true
  try {
    const api = useApiService()
    let allActivities: any[] = []
    let currentPage = 1
    const pageSize = 20 // API max limit
    let hasMorePages = true
    
    // Fetch multiple pages to get more activities
    while (hasMorePages && currentPage <= 5) { // Max 5 pages = 100 activities
      const response = await api.getRecentActivity(pageSize, currentPage)
      
      let pageActivities: any[] = []
      if (response && Array.isArray(response.items)) {
        pageActivities = response.items
      } else if (response && Array.isArray(response)) {
        pageActivities = response
      }
      
      if (pageActivities.length === 0) {
        hasMorePages = false
      } else {
        allActivities = allActivities.concat(pageActivities)
        currentPage++
      }
    }
    
    activities.value = allActivities.map((activity: any) => ({
      title: activity.title || activity.media_title || 'Unknown',
      status: activity.status || 'unknown',
      timestamp: activity.timestamp || activity.synced_at || new Date().toISOString(),
      media_type: activity.media_type || 'movie',
    }))
    
    console.log(`Loaded ${activities.value.length} recent activities (${currentPage - 1} pages)`)
  } catch (error) {
    console.error('Error fetching activities:', error)
  } finally {
    loading.value = false
  }
}

// Computed
const filteredActivities = computed(() => {
  if (selectedFilter.value === 'all') {
    return activities.value
  }
  
  if (['movie', 'tv'].includes(selectedFilter.value)) {
    return activities.value.filter(a => a.media_type === selectedFilter.value)
  }
  
  return activities.value.filter(a => a.status === selectedFilter.value)
})

const successCount = computed(() => {
  const successStatuses = ['requested', 'already_available', 'already_requested', 'skipped', 'success']
  return activities.value.filter(a => successStatuses.includes(a.status.toLowerCase())).length
})

const failedCount = computed(() => {
  const failedStatuses = ['failed', 'error']
  return activities.value.filter(a => failedStatuses.includes(a.status.toLowerCase())).length
})

const notFoundCount = computed(() => 
  activities.value.filter(a => a.status.toLowerCase() === 'not_found').length
)

// Helper functions
const getStatusIcon = (status: string) => {
  const icons: Record<string, any> = {
    success: CheckCircle2Icon,
    failed: XCircleIcon,
    not_found: AlertCircleIcon,
    error: XCircleIcon,
  }
  return icons[status] || ActivityIcon
}

const getStatusColor = (status: string) => {
  return 'text-purple-400'
}

const getStatusBg = (status: string) => {
  const backgrounds: Record<string, string> = {
    success: 'bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30',
    failed: 'bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28',
    not_found: 'bg-gradient-to-br from-purple-400/20 to-purple-300/10 border border-purple-300/30',
    error: 'bg-gradient-to-br from-purple-300/20 to-purple-200/10 border border-purple-200/30',
  }
  return backgrounds[status] || 'bg-purple-600/10 border border-purple-500/20'
}

const getActionText = (status: string) => {
  const texts: Record<string, string> = {
    success: 'Skipped (already available)',
    failed: 'Failed to process',
    not_found: 'Not found in database',
    error: 'Error during processing',
  }
  return texts[status] || 'Processed'
}

const loadMore = () => {
  // Implement load more functionality if needed
  console.log('Load more clicked')
}

// Lifecycle
onMounted(() => {
  fetchActivities()
})

// Auto-refresh every 30 seconds
useSmartPolling(fetchActivities, 30000)
</script>

