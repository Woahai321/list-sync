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
          Showing {{ filteredItems.length }} of {{ totalItems }} items
          <span v-if="hasActiveFilters || searchQuery" class="text-purple-400">(filtered)</span>
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
          Showing {{ filteredItems.length }} of {{ totalItems }} items
          <span v-if="hasActiveFilters || searchQuery" class="text-purple-400">(filtered)</span>
        </p>
      </div>
    </Card>

    <!-- Empty State -->
    <Card v-else variant="default" class="glass-card">
      <div class="text-center py-12">
        <DatabaseIcon :size="48" class="mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-semibold mb-2">
          {{ searchQuery || hasActiveFilters ? 'No Matching Items' : 'No Items Found' }}
        </h3>
        <p class="text-sm text-muted-foreground mb-6">
          <template v-if="searchQuery || hasActiveFilters">
            No items match your current filters.
            <span v-if="totalItems > 0">There are {{ formatNumber(totalItems) }} total items available.</span>
          </template>
          <template v-else>
            No items have been synced yet. Add lists and trigger a sync to populate your library.
          </template>
        </p>
        <div class="flex items-center justify-center gap-3">
          <Button
            v-if="searchQuery || hasActiveFilters"
            variant="primary"
            @click="clearFilters"
          >
            Clear All Filters
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

// Stats data (separate from paginated items)
const stats = ref({
  movies: 0,
  shows: 0,
  requested: 0,
})

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

// Use filtered items for display
const paginatedItems = computed(() => filteredItems.value)

// Stats are now fetched separately from API

const hasActiveFilters = computed(() =>
  filters.value.mediaType !== 'all' || filters.value.status !== 'all'
)

// Get filtered count for display
const filteredCount = computed(() => filteredItems.value.length)

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

// Fetch stats separately from paginated items
const fetchStats = async () => {
  try {
    // Get total count from items API metadata first
    const metadataResponse: any = await api.getItems(1, 1)
    if (metadataResponse && metadataResponse.total) {
      totalItems.value = metadataResponse.total
    }
    
    // Fetch ALL items by looping through all pages
    let allItems: any[] = []
    let currentPage = 1
    let hasMore = true
    const pageSize = 100 // Use larger page size for efficiency
    
    console.log('Fetching all items for stats calculation...')
    
    while (hasMore) {
      const response: any = await api.getItems(currentPage, pageSize)
      
      if (response && response.items && response.items.length > 0) {
        allItems = allItems.concat(response.items)
        console.log(`Fetched page ${currentPage}: ${response.items.length} items (total so far: ${allItems.length})`)
        
        // Check if there are more pages
        hasMore = currentPage < (response.total_pages || 0)
        currentPage++
        
        // Safety check to prevent infinite loops
        if (currentPage > 1000) {
          console.warn('Reached maximum page limit (1000), stopping')
          break
        }
      } else {
        hasMore = false
      }
    }
    
    console.log(`Total items fetched for stats: ${allItems.length}`)
    
    // Calculate stats from ALL items
    stats.value.movies = allItems.filter((item: any) => item.media_type === 'movie').length
    stats.value.shows = allItems.filter((item: any) => item.media_type === 'tv' || item.media_type === 'show').length
    // Only count "requested" status, NOT "already_requested" to match filter
    stats.value.requested = allItems.filter((item: any) => item.status === 'requested').length
    
    // Update total items to match what we actually got
    totalItems.value = allItems.length
    
    console.log('Stats calculated:', {
      total: totalItems.value,
      movies: stats.value.movies,
      shows: stats.value.shows,
      requested: stats.value.requested
    })
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
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
    await Promise.all([
      fetchItems(1, true),
      fetchStats() // Also refresh stats
    ])
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
  Promise.all([
    fetchItems(1, true),
    fetchStats() // Fetch stats on mount
  ])
})
</script>

