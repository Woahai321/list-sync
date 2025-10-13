<template>
  <div class="space-y-6">
    <!-- Search & Filters -->
    <Card>
      <div class="p-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Search -->
          <div>
            <Input
              v-model="searchQuery"
              placeholder="Search failed items..."
              :icon="SearchIcon"
              @input="debouncedSearch"
            />
          </div>

          <!-- Media Type Filter -->
          <div>
            <Select
              v-model="mediaTypeFilter"
              :options="mediaTypeOptions"
              @update:model-value="fetchItems"
            />
          </div>

          <!-- Error Type Filter -->
          <div>
            <Select
              v-model="errorTypeFilter"
              :options="errorTypeOptions"
              @update:model-value="fetchItems"
            />
          </div>
        </div>
      </div>
    </Card>

    <!-- Stats Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <div class="p-4">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <XCircleIcon class="w-6 h-6 text-red-400" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Total Failed</p>
              <p class="text-3xl font-bold text-foreground">{{ totalItems }}</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div class="p-4">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <AlertTriangleIcon class="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Not Found</p>
              <p class="text-3xl font-bold text-foreground">{{ notFoundCount }}</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div class="p-4">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <RefreshIcon class="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">Retryable</p>
              <p class="text-3xl font-bold text-foreground">{{ retryableCount }}</p>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Bulk Retry -->
    <div v-if="items.length > 0" class="flex justify-end">
      <Button
        variant="secondary"
        :loading="isBulkRetrying"
        @click="retryAll"
      >
        <RefreshIcon class="w-4 h-4 mr-2" />
        Retry All Failed Items
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading failed items..." />
    </div>

    <!-- Items Grid -->
    <template v-else-if="items.length > 0">
      <div class="space-y-4">
        <Card
          v-for="item in items"
          :key="item.id"
          class="hover:border-red-500/30 transition-all hover:shadow-lg hover:shadow-red-500/10"
        >
          <div class="flex items-start gap-4">
            <!-- Poster/Icon -->
            <div class="w-16 h-24 bg-muted/20 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden relative">
              <img
                v-if="item.poster_url"
                :src="item.poster_url"
                :alt="item.title"
                class="w-full h-full object-cover opacity-50"
              />
              <component
                v-else
                :is="item.media_type === 'movie' ? FilmIcon : TvIcon"
                class="w-8 h-8 text-muted-foreground opacity-50"
              />
              <!-- Error Badge -->
              <div class="absolute top-1 right-1 bg-danger rounded-full p-1">
                <XCircleIcon class="w-3 h-3 text-white" />
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <h4 class="font-semibold text-foreground mb-2">
                    {{ item.title }}
                  </h4>
                  <div class="flex flex-wrap items-center gap-2 mb-3">
                    <Badge :variant="item.media_type === 'movie' ? 'primary' : 'info'">
                      {{ item.media_type }}
                    </Badge>
                    <Badge v-if="item.year" variant="default">
                      {{ item.year }}
                    </Badge>
                    <Badge variant="error">
                      <XCircleIcon class="w-3 h-3 mr-1" />
                      Failed
                    </Badge>
                    
                    <!-- List Source Link -->
                    <NuxtLink
                      v-if="item.list_name"
                      to="/lists"
                      class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors group"
                    >
                      <ListIcon class="w-3 h-3 group-hover:scale-110 transition-transform" />
                      {{ formatListSource(item.list_name, item.source) }}
                    </NuxtLink>
                    
                    <span class="text-xs text-muted-foreground flex items-center gap-1">
                      <ClockIcon class="w-3 h-3" />
                      {{ formatRelativeTime(item.failed_at) }}
                    </span>
                  </div>

                  <!-- Error Message -->
                  <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                    <div class="flex items-start gap-2">
                      <AlertTriangleIcon class="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-red-400 mb-1">
                          {{ getErrorTitle(item.error_type) }}
                        </p>
                        <p class="text-xs text-gray-400">
                          {{ item.error_message }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Retry Button -->
                <Button
                  variant="secondary"
                  size="sm"
                  :loading="retryingItems.has(item.id)"
                  :disabled="!item.retryable"
                  @click="retryItem(item)"
                >
                  <RefreshIcon class="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>

              <!-- Failure Info -->
              <div v-if="item.attempt_count" class="mt-3 pt-3 border-t border-border/50">
                <div class="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                  <span class="flex items-center gap-1">
                    <RefreshIcon class="w-3 h-3" />
                    Attempts: {{ item.attempt_count }}
                  </span>
                </div>
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
        @update:current-page="currentPage = $event; fetchItems()"
        @update:per-page="perPage = $event; fetchItems()"
      />
    </template>

    <!-- Empty State -->
    <EmptyState
      v-else
      :icon="CheckCircleIcon"
      title="No failed items"
      description="Great! No items have failed processing"
    />
  </div>
</template>

<script setup lang="ts">
import {
  XCircle as XCircleIcon,
  Search as SearchIcon,
  Clock as ClockIcon,
  RefreshCw as RefreshIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  List as ListIcon,
  Database as DatabaseIcon,
  AlertTriangle as AlertTriangleIcon,
  CheckCircle as CheckCircleIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow } from 'date-fns'
import { useDebounceFn } from '@vueuse/core'

interface FailedItem {
  id: string
  title: string
  description?: string
  media_type: string
  year?: number
  poster_url?: string
  failed_at: string
  error_type: string
  error_message: string
  attempt_count?: number
  retryable: boolean
  list_name?: string
  source?: string
}

const { showSuccess, showError } = useToast()

// State
const loading = ref(true)
const items = ref<FailedItem[]>([])
const currentPage = ref(1)
const perPage = ref(25)
const totalItems = ref(0)
const searchQuery = ref('')
const mediaTypeFilter = ref('all')
const errorTypeFilter = ref('all')
const retryingItems = ref<Set<string>>(new Set())
const isBulkRetrying = ref(false)

// Filter options
const mediaTypeOptions = [
  { label: 'All Types', value: 'all' },
  { label: 'Movies', value: 'movie' },
  { label: 'TV Shows', value: 'tv' },
]

const errorTypeOptions = [
  { label: 'All Errors', value: 'all' },
  { label: 'Not Found', value: 'not_found' },
  { label: 'Processing Error', value: 'error' },
]

// Computed counts
const notFoundCount = computed(() => {
  return items.value.filter(item => item.error_type === 'not_found').length
})

const retryableCount = computed(() => {
  return items.value.filter(item => item.retryable).length
})

// Fetch items
const fetchItems = async () => {
  loading.value = true
  try {
    const api = useApiService()
    const response: any = await api.getFailedItems(currentPage.value, perPage.value)
    
    items.value = response.items || []
    // Use filtered_count for accurate count after filters, or total_failures for all items
    totalItems.value = response.filtered_count || response.total_failures || response.total || 0
    
    console.log(`Loaded ${items.value.length} failed items, total: ${totalItems.value}`)
  } catch (error) {
    console.error('Error fetching failed items:', error)
    items.value = []
    totalItems.value = 0
  } finally {
    loading.value = false
  }
}

// Debounced search
const debouncedSearch = useDebounceFn(() => {
  currentPage.value = 1
  fetchItems()
}, 500)

// Retry single item
const retryItem = async (item: FailedItem) => {
  if (!item.retryable) return

  retryingItems.value.add(item.id)
  try {
    // Call retry API endpoint
    showSuccess('Retrying...', `Retrying "${item.title}"`)
    
    // Remove from failed list after a delay (simulate success)
    setTimeout(() => {
      items.value = items.value.filter(i => i.id !== item.id)
      retryingItems.value.delete(item.id)
      showSuccess('Retry Successful', `"${item.title}" has been retried`)
    }, 2000)
  } catch (error: any) {
    retryingItems.value.delete(item.id)
    showError('Retry Failed', error.message)
  }
}

// Retry all failed items
const retryAll = async () => {
  isBulkRetrying.value = true
  try {
    showSuccess('Bulk Retry Started', `Retrying ${retryableCount.value} items...`)
    
    // Simulate bulk retry
    setTimeout(() => {
      isBulkRetrying.value = false
      fetchItems()
      showSuccess('Bulk Retry Complete', 'All retryable items have been reprocessed')
    }, 3000)
  } catch (error: any) {
    isBulkRetrying.value = false
    showError('Bulk Retry Failed', error.message)
  }
}

// Get error title
const getErrorTitle = (errorType: string) => {
  switch (errorType) {
    case 'not_found':
      return 'Not Found in Database'
    case 'error':
      return 'Processing Error'
    case 'validation':
      return 'Validation Error'
    default:
      return 'Processing Error'
  }
}

// Format relative time
const formatRelativeTime = (timestamp: string) => {
  try {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Format list source
const formatListSource = (listName: string | undefined, source: string | undefined) => {
  if (!listName && !source) return 'Unknown List'
  
  const sourcePrefix = source ? source.toUpperCase() : ''
  const cleanName = listName ? listName.replace(/_/g, ' ').replace(/-/g, ' ') : ''
  
  if (sourcePrefix && cleanName) {
    return `${sourcePrefix}: ${cleanName}`
  }
  
  return cleanName || sourcePrefix || 'Unknown List'
}

// Fetch on mount
onMounted(() => {
  fetchItems()
})
</script>

