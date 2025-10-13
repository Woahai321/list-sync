<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-foreground">Recent Activity</h1>
        <p class="text-sm text-muted-foreground mt-1">
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
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <div class="p-4">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-green-500/10">
              <CheckCircle2Icon class="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground">{{ successCount }}</p>
              <p class="text-xs text-muted-foreground">Successful</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div class="p-4">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-red-500/10">
              <XCircleIcon class="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground">{{ failedCount }}</p>
              <p class="text-xs text-muted-foreground">Failed</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div class="p-4">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-yellow-500/10">
              <AlertCircleIcon class="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground">{{ notFoundCount }}</p>
              <p class="text-xs text-muted-foreground">Not Found</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div class="p-4">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-purple-500/10">
              <ActivityIcon class="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p class="text-2xl font-bold text-foreground">{{ activities.length }}</p>
              <p class="text-xs text-muted-foreground">Total Items</p>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Filters -->
    <Card>
      <div class="p-4">
        <div class="flex flex-wrap items-center gap-3">
          <button
            v-for="filter in filters"
            :key="filter.value"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              selectedFilter === filter.value
                ? 'bg-purple-500 text-white'
                : 'bg-black/20 text-muted-foreground hover:bg-white/5'
            ]"
            @click="selectedFilter = filter.value"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>
    </Card>

    <!-- Activity List -->
    <Card>
      <div class="divide-y divide-border">
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
  const colors: Record<string, string> = {
    success: 'text-green-400',
    failed: 'text-red-400',
    not_found: 'text-yellow-400',
    error: 'text-red-400',
  }
  return colors[status] || 'text-muted-foreground'
}

const getStatusBg = (status: string) => {
  const backgrounds: Record<string, string> = {
    success: 'bg-green-500/10',
    failed: 'bg-red-500/10',
    not_found: 'bg-yellow-500/10',
    error: 'bg-red-500/10',
  }
  return backgrounds[status] || 'bg-purple-500/10'
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

