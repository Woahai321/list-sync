<template>
  <div class="space-y-8 pb-24 lg:pb-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold">
          All Synced Items
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          Browse and manage your entire synced media library
        </p>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="text-sm text-muted-foreground">View:</span>
          <Button
            :variant="viewMode === 'pagination' ? 'primary' : 'secondary'"
            size="sm"
            @click="viewMode = 'pagination'"
          >
            Pages
          </Button>
          <Button
            :variant="viewMode === 'infinite' ? 'primary' : 'secondary'"
            size="sm"
            @click="viewMode = 'infinite'"
          >
            Infinite Scroll
          </Button>
        </div>
        
        <Button
          variant="secondary"
          :icon="DownloadIcon"
          @click="exportToCSV"
        >
          Export CSV
        </Button>
        
        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="isRefreshing"
          @click="refreshData"
        >
          Refresh
        </Button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card variant="default" class="glass-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground mb-1">Total Items</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ formatNumber(totalItems) }}
            </p>
          </div>
          <DatabaseIcon :size="24" class="text-purple-400" />
        </div>
      </Card>

      <Card variant="default" class="glass-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground mb-1">Movies</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ formatNumber(stats.movies) }}
            </p>
          </div>
          <FilmIcon :size="24" class="text-blue-400" />
        </div>
      </Card>

      <Card variant="default" class="glass-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground mb-1">TV Shows</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ formatNumber(stats.shows) }}
            </p>
          </div>
          <TvIcon :size="24" class="text-green-400" />
        </div>
      </Card>

      <Card variant="default" class="glass-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground mb-1">Requested</p>
            <p class="text-3xl font-bold text-foreground tabular-nums">
              {{ formatNumber(stats.requested) }}
            </p>
          </div>
          <SendIcon :size="24" class="text-amber-400" />
        </div>
      </Card>
    </div>

    <!-- Search and Filters -->
    <Card variant="default" class="glass-card">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Search -->
          <div class="md:col-span-2">
            <Input
              v-model="searchQuery"
              placeholder="Search by title, IMDb ID..."
              :icon="SearchIcon"
            />
          </div>

          <!-- Media Type Filter -->
          <div>
            <Select
              v-model="filters.mediaType"
              :options="mediaTypeOptions"
            />
          </div>

          <!-- Status Filter -->
          <div>
            <Select
              v-model="filters.status"
              :options="statusOptions"
            />
          </div>
        </div>

        <!-- Active Filters -->
        <div v-if="hasActiveFilters" class="flex items-center gap-2 flex-wrap">
          <span class="text-sm text-muted-foreground">Active filters:</span>
          <Badge
            v-if="filters.mediaType !== 'all'"
            variant="primary"
            class="cursor-pointer"
            @click="filters.mediaType = 'all'"
          >
            {{ mediaTypeOptions.find(o => o.value === filters.mediaType)?.label }}
            <XIcon :size="12" class="ml-1" />
          </Badge>
          <Badge
            v-if="filters.status !== 'all'"
            variant="accent"
            class="cursor-pointer"
            @click="filters.status = 'all'"
          >
            {{ statusOptions.find(o => o.value === filters.status)?.label }}
            <XIcon :size="12" class="ml-1" />
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            @click="clearFilters"
          >
            Clear all
          </Button>
        </div>
      </div>
    </Card>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <div class="text-center">
        <LoadingSpinner size="lg" text="Loading items..." />
        <p class="text-sm text-muted-foreground mt-2">
          Fetching page {{ currentPage }} of {{ totalPages || '...' }}...
        </p>
      </div>
    </div>

    <!-- Items Table -->
    <Card v-else-if="items.length > 0" variant="default" class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border/50">
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Title</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Type</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Year</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Status</th>
              <th class="text-right p-4 text-sm font-semibold text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedItems"
              :key="item.id"
              class="border-b border-border/30 hover:bg-white/5 transition-colors"
            >
              <td class="p-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-18 bg-muted/20 rounded flex items-center justify-center flex-shrink-0">
                    <FilmIcon v-if="item.media_type === 'movie'" :size="20" class="text-muted-foreground" />
                    <TvIcon v-else :size="20" class="text-muted-foreground" />
                  </div>
                  <div class="min-w-0">
                    <p class="font-semibold text-foreground truncate">{{ item.title }}</p>
                    <p v-if="item.list_name" class="text-xs text-muted-foreground truncate">
                      From: {{ item.list_name }}
                    </p>
                  </div>
                </div>
              </td>
              <td class="p-4">
                <Badge :variant="item.media_type === 'movie' ? 'primary' : 'accent'" size="sm">
                  {{ item.media_type }}
                </Badge>
              </td>
              <td class="p-4 text-sm text-muted-foreground">
                {{ item.year || 'N/A' }}
              </td>
              <td class="p-4">
                <Badge :variant="getStatusVariant(item.status)" size="sm">
                  {{ formatStatus(item.status) }}
                </Badge>
              </td>
              <td class="p-4">
                <div class="flex items-center justify-end gap-2">
                  <Button
                    v-if="item.overseerr_url"
                    variant="primary"
                    size="sm"
                    @click="openOverseerr(item.overseerr_url)"
                  >
                    <ExternalLinkIcon :size="16" class="mr-1" />
                    View in Overseerr
                  </Button>
                  <span v-else class="text-xs text-muted-foreground">Not in Overseerr</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="viewMode === 'pagination' && totalPages > 1" class="flex items-center justify-between p-4 border-t border-border/50">
        <p class="text-sm text-muted-foreground">
          Showing {{ (currentPage - 1) * perPage + 1 }} to {{ Math.min(currentPage * perPage, totalItems) }} of {{ totalItems }} items
        </p>

        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            :disabled="currentPage === 1 || isLoading"
            :loading="isLoading && currentPage > 1"
            @click="loadPreviousPage"
          >
            Previous
          </Button>
          
          <span class="text-sm text-muted-foreground px-3">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            :disabled="!hasMorePages || isLoading"
            :loading="isLoading && hasMorePages"
            @click="loadNextPage"
          >
            Next
          </Button>
        </div>
      </div>

      <!-- Infinite Scroll Load More -->
      <div v-if="viewMode === 'infinite' && hasMorePages" class="flex items-center justify-center p-4 border-t border-border/50">
        <Button
          variant="ghost"
          :loading="isLoading"
          @click="loadNextPage"
        >
          Load More Items
        </Button>
      </div>

      <!-- Infinite Scroll Info -->
      <div v-if="viewMode === 'infinite'" class="flex items-center justify-center p-4 border-t border-border/50">
        <p class="text-sm text-muted-foreground">
          Showing {{ items.length }} of {{ totalItems }} items
        </p>
      </div>
    </Card>

    <!-- Empty State -->
    <Card v-else variant="default" class="glass-card">
      <div class="text-center py-12">
        <DatabaseIcon :size="48" class="mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-semibold mb-2">No Items Found</h3>
        <p class="text-sm text-muted-foreground mb-6">
          {{ searchQuery || hasActiveFilters ? 'Try adjusting your search or filters' : 'No items have been synced yet. Add lists and trigger a sync to populate your library.' }}
        </p>
        <div class="flex items-center justify-center gap-3">
          <Button
            v-if="searchQuery || hasActiveFilters"
            variant="primary"
            @click="clearFilters"
          >
            Clear Filters
          </Button>
          <Button
            v-else
            variant="primary"
            @click="$router.push('/lists?action=add')"
          >
            Add Your First List
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Download as DownloadIcon,
  Database as DatabaseIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  Send as SendIcon,
  Search as SearchIcon,
  X as XIcon,
  ExternalLink as ExternalLinkIcon,
} from 'lucide-vue-next'

// Set page title
useHead({
  title: 'All Items - ListSync',
})

const api = useApiService()
const { showSuccess, showError } = useToast()

// State
const isLoading = ref(true)
const isRefreshing = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const perPage = 50
const viewMode = ref<'pagination' | 'infinite'>('pagination')

// Filters
const filters = ref({
  mediaType: 'all',
  status: 'all',
})

// Data
const items = ref<any[]>([])
const totalItems = ref(0)
const totalPages = ref(0)
const hasMorePages = ref(false)

// Filter options
const mediaTypeOptions = [
  { label: 'All Types', value: 'all' },
  { label: 'Movies', value: 'movie' },
  { label: 'TV Shows', value: 'tv' },
]

const statusOptions = [
  { label: 'All Status', value: 'all' },
  { label: 'Available', value: 'already_available' },
  { label: 'Requested', value: 'requested' },
  { label: 'Already Requested', value: 'already_requested' },
  { label: 'Not Found', value: 'not_found' },
  { label: 'Error', value: 'error' },
  { label: 'Skipped', value: 'skipped' },
]

// Computed
const filteredItems = computed(() => {
  let filtered = items.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item =>
      item.title?.toLowerCase().includes(query) ||
      item.imdb_id?.toLowerCase().includes(query)
    )
  }

  // Media type filter
  if (filters.value.mediaType !== 'all') {
    filtered = filtered.filter(item => item.media_type === filters.value.mediaType)
  }

  // Status filter
  if (filters.value.status !== 'all') {
    filtered = filtered.filter(item => item.status === filters.value.status)
  }

  return filtered
})

// Items are already paginated from API, so we use them directly
const paginatedItems = computed(() => items.value)

const stats = computed(() => ({
  movies: items.value.filter(i => i.media_type === 'movie').length,
  shows: items.value.filter(i => i.media_type === 'tv' || i.media_type === 'show').length,
  requested: items.value.filter(i => i.status === 'requested' || i.status === 'already_requested').length,
}))

const hasActiveFilters = computed(() =>
  filters.value.mediaType !== 'all' || filters.value.status !== 'all'
)

// Format number with commas
const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Format status
const formatStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'already_available': 'Available',
    'requested': 'Requested',
    'already_requested': 'Already Requested',
    'not_found': 'Not Found',
    'error': 'Error',
    'skipped': 'Skipped',
  }
  return statusMap[status] || status?.charAt(0).toUpperCase() + status?.slice(1) || 'Unknown'
}

// Get status badge variant
const getStatusVariant = (status: string): 'success' | 'warning' | 'danger' | 'default' => {
  switch (status) {
    case 'already_available':
      return 'success'
    case 'requested':
    case 'already_requested':
      return 'warning'
    case 'error':
    case 'not_found':
      return 'danger'
    case 'skipped':
      return 'default'
    default:
      return 'default'
  }
}

// Clear filters
const clearFilters = () => {
  searchQuery.value = ''
  filters.value.mediaType = 'all'
  filters.value.status = 'all'
  currentPage.value = 1
}

// Fetch items with server-side pagination
const fetchItems = async (page: number = 1, reset: boolean = true) => {
  try {
    if (reset) {
      isLoading.value = true
    }
    
    const response: any = await api.getProcessedItems(page, perPage)
    
    if (response && response.items) {
      if (reset) {
        items.value = response.items
      } else {
        // For infinite scroll, append to existing items
        items.value = [...items.value, ...response.items]
      }
      
      totalItems.value = response.total || 0
      totalPages.value = response.total_pages || 0
      hasMorePages.value = page < totalPages.value
      
      console.log(`Loaded page ${page}: ${response.items.length} items (${response.total || 0} total)`)
    } else {
      // Fallback to getItems if processed items fails
      const fallbackResponse: any = await api.getItems(page, perPage)
      if (fallbackResponse && fallbackResponse.items) {
        if (reset) {
          items.value = fallbackResponse.items
        } else {
          items.value = [...items.value, ...fallbackResponse.items]
        }
        
        totalItems.value = fallbackResponse.total || 0
        totalPages.value = fallbackResponse.total_pages || 0
        hasMorePages.value = page < totalPages.value
        
        console.log(`Fallback: Loaded page ${page}: ${fallbackResponse.items.length} items`)
      } else {
        items.value = []
        totalItems.value = 0
        totalPages.value = 0
        hasMorePages.value = false
      }
    }
    
  } catch (error: any) {
    console.error('Error fetching items:', error)
    
    if (error.statusCode === 404 || error.response?.status === 404) {
      showError('Feature Coming Soon', 'The items endpoint is not yet available')
    } else {
      showError('Failed to load items', error.message || 'Please try again later')
    }
    
    items.value = []
    totalItems.value = 0
    totalPages.value = 0
    hasMorePages.value = false
  } finally {
    isLoading.value = false
  }
}

// Refresh data
const refreshData = async () => {
  isRefreshing.value = true
  try {
    currentPage.value = 1
    await fetchItems(1, true)
    showSuccess('Items refreshed')
  } catch (error: any) {
    showError('Refresh failed', error.message)
  } finally {
    isRefreshing.value = false
  }
}

// Load next page
const loadNextPage = async () => {
  if (hasMorePages.value && !isLoading.value) {
    currentPage.value++
    await fetchItems(currentPage.value, false)
  }
}

// Load previous page
const loadPreviousPage = async () => {
  if (currentPage.value > 1 && !isLoading.value) {
    currentPage.value--
    await fetchItems(currentPage.value, true)
  }
}

// Export to CSV
const exportToCSV = () => {
  try {
    const headers = ['Title', 'Type', 'Year', 'Status', 'IMDb ID', 'Overseerr ID', 'List Name']
    const rows = items.value.map(item => [
      item.title,
      item.media_type,
      item.year || '',
      item.status,
      item.imdb_id || '',
      item.overseerr_id || '',
      item.list_name || '',
    ])

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `listsync-items-${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    URL.revokeObjectURL(url)

    showSuccess('CSV exported', 'Downloaded to your device')
  } catch (error) {
    showError('Export failed', 'Unable to create CSV file')
  }
}

// Open Overseerr
const openOverseerr = (url: string) => {
  if (!url) {
    showError('Cannot open Overseerr', 'Overseerr URL is not available for this item')
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

// Watch filters to reset pagination
watch([searchQuery, filters], () => {
  currentPage.value = 1
  // Note: For now, we'll keep client-side filtering
  // In the future, we could implement server-side filtering
}, { deep: true })

// Watch view mode changes
watch(viewMode, (newMode) => {
  if (newMode === 'infinite') {
    // Reset to first page and reload all items for infinite scroll
    currentPage.value = 1
    fetchItems(1, true)
  }
})

// Load data on mount
onMounted(() => {
  fetchItems(1, true)
})
</script>

