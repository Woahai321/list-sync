<template>
  <div class="space-y-6">
    <!-- Filters -->
    <Card class="glass-card">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Date Range Filter -->
        <div>
          <label class="block text-sm font-medium mb-2">
            Date Range
          </label>
          <Select
            v-model="filters.dateRange"
            :options="dateRangeOptions"
            @update:model-value="applyFilters"
          />
        </div>

        <!-- Category Filter -->
        <div>
          <label class="block text-sm font-medium mb-2">
            Category
          </label>
          <Select
            v-model="filters.mediaType"
            :options="mediaTypeOptions"
            @update:model-value="applyFilters"
          />
        </div>

        <!-- Log Level Filter -->
        <div>
          <label class="block text-sm font-medium mb-2">
            Log Level
          </label>
          <Select
            v-model="filters.status"
            :options="statusOptions"
            @update:model-value="applyFilters"
          />
        </div>
      </div>
    </Card>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading activities..." />
    </div>

    <!-- Activity List -->
    <template v-else-if="activities.length > 0">
      <div class="space-y-3">
        <Card
          v-for="activity in activities"
          :key="activity.id"
          class="glass-card hover:border-primary/30 transition-colors"
        >
          <div class="flex items-start gap-4">
            <!-- Icon -->
            <div
              class="p-3 rounded-lg flex-shrink-0"
              :class="getActivityColorClass(activity.action)"
            >
              <component
                :is="getActivityIcon(activity.action)"
                class="w-5 h-5"
              />
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <h4 class="font-semibold text-foreground mb-1 truncate">
                    {{ activity.title }}
                  </h4>
                  <p class="text-sm text-muted-foreground mb-2">
                    {{ activity.description }}
                  </p>
                  <div class="flex flex-wrap items-center gap-2">
                    <Badge :variant="getMediaTypeBadge(activity.media_type)">
                      {{ activity.media_type }}
                    </Badge>
                    <Badge :variant="getStatusBadge(activity.status)">
                      {{ activity.status }}
                    </Badge>
                    <span class="text-xs text-muted-foreground flex items-center gap-1">
                      <ClockIcon class="w-3 h-3" />
                      {{ formatRelativeTime(activity.timestamp) }}
                    </span>
                  </div>
                </div>

                <!-- Action Button -->
                <Button
                  v-if="activity.status === 'failed'"
                  variant="ghost"
                  size="sm"
                  @click="retryActivity(activity)"
                >
                  <RefreshIcon class="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Pagination -->
      <Pagination
        :current-page="currentPage"
        :total-items="totalItems"
        :per-page="perPage"
        @update:current-page="currentPage = $event; fetchActivities()"
        @update:per-page="perPage = $event; fetchActivities()"
      />
    </template>

    <!-- Empty State -->
    <EmptyState
      v-else
      :icon="ActivityIcon"
      title="No logs found"
      description="No backend application logs match your filters"
      action-label="Clear Filters"
      @action="clearFilters"
    />
  </div>
</template>

<script setup lang="ts">
import {
  Activity as ActivityIcon,
  Clock as ClockIcon,
  RefreshCw as RefreshIcon,
  Plus as PlusIcon,
  Trash as TrashIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Edit as EditIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow } from 'date-fns'

interface Activity {
  id: string
  title: string
  description: string
  action: string
  media_type: string
  status: string
  timestamp: string
}

// State
const loading = ref(true)
const activities = ref<Activity[]>([])
const currentPage = ref(1)
const perPage = ref(20) // API max limit is 20
const totalItems = ref(0)

// Filters
const filters = ref({
  dateRange: 'all',
  mediaType: 'all',
  status: 'all',
})

// Filter options
const dateRangeOptions = [
  { label: 'All Time', value: 'all' },
  { label: 'Last Hour', value: '1h' },
  { label: 'Last 24 Hours', value: '24h' },
  { label: 'Last 7 Days', value: '7d' },
  { label: 'Last 30 Days', value: '30d' },
]

const mediaTypeOptions = [
  { label: 'All Categories', value: 'all' },
  { label: 'Web Scraping', value: 'web_scraping' },
  { label: 'API Calls', value: 'api_calls' },
  { label: 'Database Operations', value: 'database' },
  { label: 'Sync Operations', value: 'sync' },
  { label: 'Item Processing', value: 'item_processing' },
]

const statusOptions = [
  { label: 'All Levels', value: 'all' },
  { label: 'Info', value: 'INFO' },
  { label: 'Debug', value: 'DEBUG' },
  { label: 'Warning', value: 'WARNING' },
  { label: 'Error', value: 'ERROR' },
]

// Fetch backend application logs
const fetchActivities = async () => {
  loading.value = true
  try {
    // Call logs API with pagination and filters
    const params: any = {
      page: currentPage.value,
      limit: perPage.value,
    }
    
    // Add level filter if not 'all'
    if (filters.value.status !== 'all') {
      params.level = filters.value.status
    }
    
    // Add category filter if not 'all'
    if (filters.value.mediaType !== 'all') {
      params.category = [filters.value.mediaType]
    }
    
    const response = await $fetch(`/api/logs/entries`, { params }) as any
    
    if (!response || !response.entries) {
      activities.value = []
      totalItems.value = 0
      return
    }
    
    // Map log entries to activity format
    activities.value = response.entries.map((entry: any, index: number) => {
      // Determine action based on level and category
      let action = 'sync'
      let status = entry.level?.toLowerCase() || 'info'
      
      if (entry.level === 'ERROR') {
        action = 'failed'
        status = 'error'
      } else if (entry.level === 'WARNING') {
        action = 'warning'
        status = 'warning'
      } else if (entry.level === 'INFO') {
        if (entry.message.includes('successful') || entry.message.includes('Added')) {
          action = 'success'
          status = 'success'
        } else {
          action = 'info'
          status = 'info'
        }
      } else if (entry.level === 'DEBUG') {
        action = 'debug'
        status = 'debug'
      }
      
      // Use backend's category directly
      const category = entry.category || 'general'
      
      // Generate readable title based on category and message
      let title = 'Application Log'
      
      if (entry.media_title) {
        title = entry.media_title
      } else if (category === 'web_scraping') {
        if (entry.message.includes('IMDb')) {
          title = 'IMDb Web Scraping'
        } else if (entry.message.includes('Letterboxd')) {
          title = 'Letterboxd Web Scraping'
        } else if (entry.message.includes('MDBList')) {
          title = 'MDBList Web Scraping'
        } else {
          title = 'Web Scraping'
        }
      } else if (category === 'api_calls') {
        if (entry.message.includes('Overseerr')) {
          title = 'Overseerr API'
        } else if (entry.message.includes('TMDb') || entry.message.includes('Detailed response')) {
          title = 'TMDb API'
        } else {
          title = 'API Call'
        }
      } else if (category === 'database') {
        if (entry.message.includes('Final match')) {
          const match = entry.message.match(/Final match for '([^']+)'/)
          title = match ? `Matched: ${match[1]}` : 'Database Match'
        } else if (entry.message.includes('Searching for')) {
          const match = entry.message.match(/Searching for '([^']+)'/)
          title = match ? `Searching: ${match[1]}` : 'Database Search'
        } else {
          title = 'Database Operation'
        }
      } else if (category === 'sync') {
        if (entry.message.includes('completed')) {
          title = 'Sync Completed'
        } else if (entry.message.includes('Starting')) {
          title = 'Sync Started'
        } else {
          title = 'Sync Operation'
        }
      } else if (category === 'item_processing') {
        const match = entry.message.match(/Added (?:movie|show): ([^(]+)/)
        title = match ? match[1].trim() : 'Item Processing'
      } else {
        title = entry.category ? entry.category.replace(/_/g, ' ').toUpperCase() : 'General Log'
      }
      
      return {
        id: `${entry.id || entry.timestamp}-${index}`,
        title: title,
        description: entry.message || 'No description',
        action: action,
        media_type: entry.media_title ? 'movie' : 'log',
        status: status,
        timestamp: entry.timestamp || new Date().toISOString(),
      }
    })
    
    totalItems.value = response.pagination?.total_items || 0
  } catch (error) {
    console.error('Error fetching activities:', error)
    activities.value = []
    totalItems.value = 0
  } finally {
    loading.value = false
  }
}

// Apply filters
const applyFilters = () => {
  currentPage.value = 1
  fetchActivities()
}

// Clear filters
const clearFilters = () => {
  filters.value = {
    dateRange: 'all',
    mediaType: 'all',
    status: 'all',
  }
  applyFilters()
}

// Retry activity
const retryActivity = (activity: Activity) => {
  console.log('Retry activity:', activity)
  // Implement retry logic
}

// Helper functions
const getActivityIcon = (action: string) => {
  switch (action.toLowerCase()) {
    case 'success':
      return CheckCircleIcon
    case 'failed':
    case 'error':
      return XCircleIcon
    case 'warning':
      return ErrorIcon
    case 'info':
      return PlusIcon
    case 'debug':
      return EditIcon
    default:
      return ActivityIcon
  }
}

const getActivityColorClass = (action: string) => {
  switch (action.toLowerCase()) {
    case 'success':
      return 'bg-success/10 text-success'
    case 'failed':
    case 'error':
      return 'bg-danger/10 text-danger'
    case 'warning':
      return 'bg-yellow-500/10 text-yellow-400'
    case 'info':
      return 'bg-blue-500/10 text-blue-400'
    case 'debug':
      return 'bg-purple-500/10 text-purple-400'
    default:
      return 'bg-muted/10 text-muted-foreground'
  }
}

const getMediaTypeBadge = (type: string) => {
  return type === 'movie' ? 'primary' : 'accent'
}

const getStatusBadge = (status: string) => {
  switch (status.toLowerCase()) {
    case 'success':
      return 'success'
    case 'error':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    case 'debug':
      return 'default'
    default:
      return 'default'
  }
}

const formatRelativeTime = (timestamp: string) => {
  try {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Fetch on mount
onMounted(() => {
  fetchActivities()
})
</script>

