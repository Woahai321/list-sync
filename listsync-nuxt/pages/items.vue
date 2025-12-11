<template>
  <div class="space-y-8 pb-24 lg:pb-8 relative">
    <!-- Scroll to Top Button -->
    <Transition name="fade">
      <button
        v-if="showScrollTop"
        @click="scrollToTop"
        class="fixed bottom-24 right-6 z-50 w-12 h-12 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white rounded-full shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 flex items-center justify-center group"
        aria-label="Scroll to top"
      >
        <ChevronUpIcon :size="24" class="group-hover:-translate-y-0.5 transition-transform" />
      </button>
    </Transition>

    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          All Synced Items
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          Browse and manage your entire synced media library
        </p>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="text-sm text-muted-foreground">Layout:</span>
          <Button
            :variant="displayMode === 'grid' ? 'primary' : 'secondary'"
            size="sm"
            @click="displayMode = 'grid'"
          >
            <LayoutGridIcon :size="16" />
          </Button>
          <Button
            :variant="displayMode === 'table' ? 'primary' : 'secondary'"
            size="sm"
            @click="displayMode = 'table'"
          >
            <TableIcon :size="16" />
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
    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <Card variant="default" class="glass-card group border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 cursor-default">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] text-muted-foreground mb-1 font-medium">Total Items</p>
            <div v-if="isLoadingStats" class="flex items-center h-8">
              <LoadingSpinner size="sm" color="primary" />
            </div>
            <p v-else class="text-2xl font-bold text-foreground tabular-nums leading-none group-hover:scale-105 transition-transform">
              {{ formatNumber(totalItems) }}
            </p>
          </div>
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30 group-hover:border-purple-400/50 transition-colors">
            <DatabaseIcon :size="14" class="text-purple-400 group-hover:scale-110 transition-transform" />
          </div>
        </div>
      </Card>

      <Card variant="default" class="glass-card group border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 cursor-default">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] text-muted-foreground mb-1 font-medium">Movies</p>
            <div v-if="isLoadingStats" class="flex items-center h-8">
              <LoadingSpinner size="sm" color="primary" />
            </div>
            <p v-else class="text-2xl font-bold text-foreground tabular-nums leading-none group-hover:scale-105 transition-transform">
              {{ formatNumber(stats.movies) }}
            </p>
          </div>
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28 group-hover:border-purple-300/45 transition-colors">
            <FilmIcon :size="14" class="text-purple-300 group-hover:scale-110 transition-transform" />
          </div>
        </div>
      </Card>

      <Card variant="default" class="glass-card group border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 cursor-default">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] text-muted-foreground mb-1 font-medium">TV Shows</p>
            <div v-if="isLoadingStats" class="flex items-center h-8">
              <LoadingSpinner size="sm" color="primary" />
            </div>
            <p v-else class="text-2xl font-bold text-foreground tabular-nums leading-none group-hover:scale-105 transition-transform">
              {{ formatNumber(stats.shows) }}
            </p>
          </div>
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-400/20 to-purple-300/10 border border-purple-300/30 group-hover:border-purple-200/45 transition-colors">
            <TvIcon :size="14" class="text-purple-200 group-hover:scale-110 transition-transform" />
          </div>
        </div>
      </Card>

      <Card variant="default" class="glass-card group border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 cursor-default">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] text-muted-foreground mb-1 font-medium">Requested</p>
            <div v-if="isLoadingStats" class="flex items-center h-8">
              <LoadingSpinner size="sm" color="primary" />
            </div>
            <p v-else class="text-2xl font-bold text-foreground tabular-nums leading-none group-hover:scale-105 transition-transform">
              {{ formatNumber(stats.requested) }}
            </p>
          </div>
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-300/20 to-purple-200/10 border border-purple-200/30 group-hover:border-purple-100/45 transition-colors">
            <SendIcon :size="14" class="text-purple-100 group-hover:scale-110 transition-transform" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Search and Filters -->
    <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="space-y-3">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
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

          <!-- List Filter -->
          <div>
            <Select
              v-model="filters.listSource"
              :options="listSourceOptions"
              placeholder="All Lists"
            />
          </div>
        </div>

        <!-- Active Filters -->
        <Transition name="slide-down">
          <div v-if="hasActiveFilters" class="flex items-center gap-2 flex-wrap p-2 bg-purple-600/10 rounded-lg border border-purple-500/20">
            <span class="text-[10px] font-bold text-purple-400 uppercase tracking-wide">Active filters:</span>
            <Badge
              v-if="filters.mediaType !== 'all'"
              variant="primary"
              class="cursor-pointer hover:scale-105 transition-transform text-[10px]"
              @click="filters.mediaType = 'all'"
            >
              {{ mediaTypeOptions.find(o => o.value === filters.mediaType)?.label }}
              <XIcon :size="10" class="ml-1" />
            </Badge>
            <Badge
              v-if="filters.status !== 'all'"
              variant="accent"
              class="cursor-pointer hover:scale-105 transition-transform text-[10px]"
              @click="filters.status = 'all'"
            >
              {{ statusOptions.find(o => o.value === filters.status)?.label }}
              <XIcon :size="10" class="ml-1" />
            </Badge>
            <Badge
              v-if="filters.listSource !== 'all'"
              variant="default"
              class="cursor-pointer hover:scale-105 transition-transform text-[10px]"
              @click="filters.listSource = 'all'"
            >
              {{ listSourceOptions.find(o => o.value === filters.listSource)?.label }}
              <XIcon :size="10" class="ml-1" />
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              @click="clearFilters"
              class="ml-auto hover:bg-purple-500/10 hover:text-purple-400 transition-colors text-[10px]"
            >
              Clear all
            </Button>
          </div>
        </Transition>
      </div>
    </Card>

    <!-- Loading State for Table View -->
    <div v-if="isLoading && displayMode === 'table'" class="flex items-center justify-center py-20">
      <div class="text-center">
        <LoadingSpinner size="lg" text="Loading items..." />
        <p class="text-sm text-muted-foreground mt-2">
          Fetching page {{ currentPage }} of {{ totalPages || '...' }}...
        </p>
      </div>
    </div>

    <!-- Loading State for Grid View (Skeletons) -->
    <div v-if="isLoading && displayMode === 'grid'" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">
      <PosterCardSkeleton v-for="i in perPage" :key="`skeleton-${i}`" />
    </div>

    <!-- Grid View (Posters) -->
    <div v-if="!isLoading && filteredItems.length > 0 && displayMode === 'grid'">
      <!-- Grid Container -->
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">
        <PosterCard
          v-for="item in filteredItems"
          :key="item.id"
          :item="item"
        />
      </div>

      <!-- Loading more indicator -->
      <div
        v-if="isLoadingMore"
        class="flex items-center justify-center py-12 mt-8"
      >
        <div class="text-center">
          <LoadingSpinner size="md" />
          <p class="text-sm text-muted-foreground mt-2">
            Loading more items...
          </p>
        </div>
      </div>

      <!-- Infinite scroll trigger (invisible element) -->
      <div
        ref="infiniteScrollTrigger"
        class="h-4 w-full mt-8"
      />

      <!-- End of results message -->
      <div
        v-if="!hasMorePages && filteredItems.length > 0"
        class="text-center py-8 mt-8"
      >
        <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20">
          <CheckCircle2Icon :size="16" class="text-purple-400" />
          <p class="text-sm text-purple-400 font-medium">
            <template v-if="hasActiveFilters || searchQuery">
              That's all! {{ formatNumber(filteredItems.length) }} items match your filters
            </template>
            <template v-else>
              That's all! {{ formatNumber(totalItems) }} items loaded
            </template>
          </p>
        </div>
      </div>
    </div>

    <!-- Table View (Legacy) -->
    <Card v-else-if="!isLoading && items.length > 0 && displayMode === 'table'" variant="default" class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border/50">
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Title</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Type</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Year</th>
              <th class="text-left p-4 text-sm font-semibold text-muted-foreground">Lists</th>
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
                <div v-if="item.list_sources && item.list_sources.length > 0" class="flex flex-wrap gap-1 max-w-[200px]">
                  <Badge
                    v-for="(source, index) in item.list_sources.slice(0, 2)"
                    :key="`${source.list_type}-${source.list_id}`"
                    variant="default"
                    size="sm"
                    :title="source.display_name || `${source.list_type}: ${source.list_id}`"
                    class="text-[10px]"
                  >
                    {{ source.display_name || formatListType(source.list_type) }}
                  </Badge>
                  <Badge
                    v-if="item.list_sources.length > 2"
                    variant="default"
                    size="sm"
                    :title="item.list_sources.slice(2).map((s: any) => s.display_name || s.list_id).join(', ')"
                    class="text-[10px]"
                  >
                    +{{ item.list_sources.length - 2 }}
                  </Badge>
                </div>
                <span v-else class="text-xs text-muted-foreground">—</span>
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

      <!-- Pagination (Table View Only) -->
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

      <!-- Infinite Scroll Load More (Table View Only) -->
      <div v-if="viewMode === 'infinite' && hasMorePages" class="flex items-center justify-center p-4 border-t border-border/50">
        <Button
          variant="ghost"
          :loading="isLoading"
          @click="loadNextPage"
        >
          Load More Items
        </Button>
      </div>

      <!-- Infinite Scroll Info (Table View Only) -->
      <div v-if="viewMode === 'infinite'" class="flex items-center justify-center p-4 border-t border-border/50">
        <p class="text-sm text-muted-foreground">
          Showing {{ filteredItems.length }} of {{ totalItems }} items
          <span v-if="hasActiveFilters || searchQuery" class="text-purple-400">(filtered)</span>
        </p>
      </div>
    </Card>


    <!-- Empty State -->
    <Card v-if="!isLoading && filteredItems.length === 0" variant="default" class="glass-card border-2 border-dashed border-purple-500/20">
      <div class="text-center py-16">
        <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center">
          <DatabaseIcon :size="48" class="text-purple-400" />
        </div>
        <h3 class="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          {{ searchQuery || hasActiveFilters ? 'No Matching Items' : 'No Items Found' }}
        </h3>
        <p class="text-base text-muted-foreground mb-8 max-w-md mx-auto">
          <template v-if="searchQuery || hasActiveFilters">
            No items match your current filters.
            <span v-if="totalItems > 0" class="block mt-2 text-purple-400">
              {{ formatNumber(totalItems) }} total items available
            </span>
            <span v-if="filters.listSource !== 'all'" class="block mt-3 text-sm text-amber-400/80">
              💡 Tip: If filtering by list shows no results, items may need to be re-synced to populate list relationships. Go to the Lists page and sync your lists.
            </span>
          </template>
          <template v-else>
            Your library is waiting to be filled! Add your first list and trigger a sync to get started.
          </template>
        </p>
        <div class="flex items-center justify-center gap-3">
          <Button
            v-if="searchQuery || hasActiveFilters"
            variant="primary"
            @click="clearFilters"
            class="bg-gradient-to-r from-purple-600 to-purple-500"
          >
            Clear All Filters
          </Button>
          <Button
            v-else
            variant="primary"
            @click="$router.push('/lists?action=add')"
            class="bg-gradient-to-r from-purple-600 to-purple-500"
          >
            <span class="mr-2">✨</span>
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
  LayoutGrid as LayoutGridIcon,
  Table as TableIcon,
  ChevronUp as ChevronUpIcon,
  CheckCircle2 as CheckCircle2Icon,
} from 'lucide-vue-next'
import PosterCard from '~/components/items/PosterCard.vue'
import PosterCardSkeleton from '~/components/items/PosterCardSkeleton.vue'

// Set page title
useHead({
  title: 'All Items - ListSync',
})

const api = useApiService()
const { showSuccess, showError } = useToast()
const itemsCache = useItemsCache()
const listsStore = useListsStore()

// State
const isLoading = ref(true)
const isRefreshing = ref(false)
const isLoadingMore = ref(false) // For infinite scroll loading indicator
const isLoadingStats = ref(true) // Track stats loading state
const searchQuery = ref('')
const currentPage = ref(1)
const perPage = 50
const viewMode = ref<'pagination' | 'infinite'>('infinite')
const displayMode = ref<'grid' | 'table'>('grid') // Grid view by default
const isUsingCache = ref(false) // Track if we're showing cached data
const showScrollTop = ref(false) // Show scroll-to-top button
const infiniteScrollTrigger = ref<HTMLElement | null>(null) // Infinite scroll observer target

// Filters
const filters = ref({
  mediaType: 'all',
  status: 'all',
  listSource: 'all',
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

// Normalize list ID to match what's stored in item_lists table
// This matches the backend normalize_list_id function
const normalizeListId = (listType: string, listId: string): string => {
  if (!listId) return listId
  
  // If it's already not a URL, return as-is
  if (!listId.startsWith('http://') && !listId.startsWith('https://')) {
    return listId
  }
  
  const listTypeLower = listType.toLowerCase()
  
  // MDBList URLs: https://mdblist.com/lists/username/listname
  // Extract: username/listname
  if (listTypeLower === 'mdblist') {
    const match = listId.match(/mdblist\.com\/lists\/([^/?]+)/)
    if (match) {
      return match[1]
    }
  }
  
  // Trakt URLs
  else if (listTypeLower === 'trakt' || listTypeLower === 'trakt_special') {
    // https://trakt.tv/users/username/lists/list-slug
    // https://trakt.tv/lists/123
    let match = listId.match(/trakt\.tv\/(?:users\/[^/]+\/)?lists\/([^/?]+)/)
    if (match) {
      return match[1]
    }
    // For special Trakt lists like trending:movies
    match = listId.match(/trakt\.tv\/(?:movies|shows)\/([^/?]+)/)
    if (match) {
      return match[1]
    }
  }
  
  // IMDb URLs: https://www.imdb.com/list/ls123456789
  else if (listTypeLower === 'imdb') {
    const match = listId.match(/imdb\.com\/list\/([^/?]+)/)
    if (match) {
      return match[1]
    }
  }
  
  // Letterboxd URLs: https://letterboxd.com/username/list/listname/
  // NOTE: Letterboxd stores the full URL in the database, so do NOT normalize
  else if (listTypeLower === 'letterboxd') {
    // Return as-is - Letterboxd list_ids are stored as full URLs in the database
    return listId
  }
  
  // TMDB URLs: https://www.themoviedb.org/list/123
  else if (listTypeLower === 'tmdb') {
    const match = listId.match(/themoviedb\.org\/list\/([^/?]+)/)
    if (match) {
      return match[1]
    }
  }
  
  // TVDB URLs: https://www.thetvdb.com/lists/123
  else if (listTypeLower === 'tvdb') {
    const match = listId.match(/thetvdb\.com\/lists\/([^/?]+)/)
    if (match) {
      return match[1]
    }
  }
  
  // If no match, return original (shouldn't happen but fallback)
  return listId
}

// List source options - built from items and lists store
const listSourceOptions = computed(() => {
  const uniqueLists = new Map<string, string>()
  uniqueLists.set('all', 'All Lists')
  
  // First, add lists from items (most accurate - shows which lists actually have items)
  // Normalize the list_id to ensure consistency with what will be sent to backend
  items.value.forEach(item => {
    if (item.list_sources && Array.isArray(item.list_sources)) {
      item.list_sources.forEach((source: any) => {
        // Normalize the list_id to ensure dropdown values match what's sent to API
        const normalizedId = normalizeListId(source.list_type, source.list_id)
        const key = `${source.list_type}:${normalizedId}`
        if (!uniqueLists.has(key)) {
          // Use display_name if available, otherwise generate a readable label
          const label = source.display_name || generateListLabel(source.list_type, normalizedId)
          uniqueLists.set(key, label)
        }
      })
    }
  })
  
  // Also add lists from lists store as fallback (ensures all configured lists are available)
  // These might have URLs, so we need to normalize them
  if (listsStore.lists && listsStore.lists.length > 0) {
    listsStore.lists.forEach((list: any) => {
      // Normalize the list_id to match what's in item_lists table
      const normalizedId = normalizeListId(list.list_type, list.list_id)
      const key = `${list.list_type}:${normalizedId}`
      if (!uniqueLists.has(key)) {
        // Use display_name if available, otherwise generate a readable label
        const label = list.display_name || generateListLabel(list.list_type, normalizedId)
        uniqueLists.set(key, label)
      }
    })
  }
  
  const options = Array.from(uniqueLists.entries()).map(([value, label]) => ({
    label,
    value
  }))
  
  // Sort options: "All Lists" first, then alphabetically
  return options.sort((a, b) => {
    if (a.value === 'all') return -1
    if (b.value === 'all') return 1
    return a.label.localeCompare(b.label)
  })
})

// Format list type for display
const formatListType = (listType: string): string => {
  const typeLabels: Record<string, string> = {
    'imdb': 'IMDb',
    'trakt': 'Trakt',
    'trakt_special': 'Trakt',
    'letterboxd': 'Letterboxd',
    'mdblist': 'MDBList',
    'stevenlu': 'Steven Lu',
    'tmdb': 'TMDB',
    'tvdb': 'TVDB',
    'anilist': 'AniList',
    'collections': 'Collection'
  }
  return typeLabels[listType] || listType
}

// Generate a readable label for a list source when display_name is not available
const generateListLabel = (listType: string, listId: string): string => {
  // For trakt_special, parse the list_id to extract meaningful name
  if (listType === 'trakt_special') {
    // Format: "trending:movies" -> "Trakt Trending Movies"
    // Format: "popular:tv" -> "Trakt Popular TV"
    const parts = listId.split(':')
    if (parts.length >= 2) {
      const category = parts[0].charAt(0).toUpperCase() + parts[0].slice(1) // Capitalize
      const mediaType = parts[1] === 'movies' ? 'Movies' : parts[1] === 'tv' ? 'TV Shows' : parts[1]
      return `Trakt ${category} ${mediaType}`
    }
    return `Trakt ${listId}`
  }
  
  // For stevenlu, check if it's the original or a preset
  if (listType === 'stevenlu') {
    if (listId === 'stevenlu') {
      return "Steven Lu's Original Collection"
    }
    // Parse preset names like "movies-metacritic-min70.json" -> "Steven Lu Metacritic Min 70"
    const cleanId = listId.replace(/^movies-/, '').replace(/\.json$/, '')
    const formatted = cleanId
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
    return `Steven Lu ${formatted}`
  }
  
  // For collections, extract the collection name
  if (listType === 'collections') {
    // Remove "collection:" prefix if present
    const collectionName = listId.replace(/^collection:/, '')
    return `Collection: ${collectionName}`
  }
  
  // For letterboxd, extract username from URL
  if (listType === 'letterboxd') {
    const usernameMatch = listId.match(/letterboxd\.com\/([^\/]+)/)
    if (usernameMatch) {
      return `Letterboxd - ${usernameMatch[1]}`
    }
  }
  
  // For other types, show provider + truncated ID
  const providerName = formatListType(listType)
  // Truncate long IDs (like URLs) to last part
  const shortId = listId.includes('/') ? listId.split('/').pop() || listId : listId
  const maxLength = 30
  const displayId = shortId.length > maxLength ? shortId.substring(0, maxLength) + '...' : shortId
  
  return `${providerName}: ${displayId}`
}

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

  // List source filter is now handled server-side for both grid and table views
  // No client-side filtering needed for list sources anymore

  return filtered
})

// Use filtered items for display
const paginatedItems = computed(() => filteredItems.value)

// Stats are now fetched separately from API

const hasActiveFilters = computed(() =>
  filters.value.mediaType !== 'all' || filters.value.status !== 'all' || filters.value.listSource !== 'all'
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
  isLoadingStats.value = true
  try {
    // Use the /api/successful endpoint which provides efficient stats with movie/tv breakdown
    const successfulResponse: any = await api.getSuccessfulItems(1, 1)
    
    if (successfulResponse) {
      // Get total count from items API
      totalItems.value = successfulResponse.total_count || 0
      
      // Get movie/tv breakdown from successful endpoint
      stats.value.movies = successfulResponse.movie_count || 0
      stats.value.shows = successfulResponse.tv_count || 0
      
      console.log('Stats from /api/successful:', {
        total: totalItems.value,
        movies: stats.value.movies,
        shows: stats.value.shows,
      })
    }
    
    // Get requested count from /api/requested endpoint
    try {
      const requestedResponse: any = await api.getRequestedItems(1, 1)
      stats.value.requested = requestedResponse.total_count || 0
      console.log('Requested items:', stats.value.requested)
    } catch (error) {
      console.warn('Could not fetch requested items count:', error)
      stats.value.requested = 0
    }
    
    console.log('Final stats:', {
      total: totalItems.value,
      movies: stats.value.movies,
      shows: stats.value.shows,
      requested: stats.value.requested
    })
  } catch (error) {
    console.error('Error fetching stats:', error)
    // Fallback to items endpoint if successful endpoint fails
    try {
      const fallbackResponse: any = await api.getItems(1, 1)
      if (fallbackResponse && fallbackResponse.total) {
        totalItems.value = fallbackResponse.total
      }
    } catch (fallbackError) {
      console.error('Fallback stats fetch also failed:', fallbackError)
    }
  } finally {
    isLoadingStats.value = false
  }
}

// Fetch items with server-side pagination and smart caching
const fetchItems = async (page: number = 1, reset: boolean = true, forceRefresh: boolean = false) => {
  try {
    if (reset) {
      isLoading.value = true
      isUsingCache.value = false
    }
    
    let response: any
    
    // Use enriched API with smart caching for grid view, regular API for table view
    if (displayMode.value === 'grid') {
      // Build query params including list filter if active
      const queryParams: any = {}
      if (filters.value.listSource !== 'all') {
        // Normalize the filter value to ensure it matches what's in the database
        // Split only on FIRST colon to preserve list IDs that contain colons (like "trending:movies")
        const colonIndex = filters.value.listSource.indexOf(':')
        const listType = filters.value.listSource.substring(0, colonIndex)
        const listId = filters.value.listSource.substring(colonIndex + 1)
        const normalizedId = normalizeListId(listType, listId)
        queryParams.list_source = `${listType}:${normalizedId}`
        console.log(`🔍 GRID Filter: Original="${filters.value.listSource}", Split=(${listType}, ${listId}), Normalized="${queryParams.list_source}"`)
      } else {
        console.log(`🔍 GRID: No list filter active (filters.value.listSource = "${filters.value.listSource}")`)
      }
      console.log(`📡 Calling itemsCache.fetchEnrichedItems with:`, { page, perPage, forceRefresh, queryParams })
      // Use smart cache - returns immediately if cached, fetches fresh in background if stale
      // Note: Cache key includes filter to avoid cache collisions
      response = await itemsCache.fetchEnrichedItems(page, perPage, forceRefresh, queryParams)
      
      // Check if we got cached data
      const cacheStats = itemsCache.getCacheStats()
      if (cacheStats.fresh > 0 || cacheStats.stale > 0) {
        isUsingCache.value = true
      }
    } else {
      // Table view - no caching (less critical, users don't switch as often)
      // Build query params including list filter if active
      const queryParams: any = {}
      if (filters.value.listSource !== 'all') {
        // Normalize the filter value to ensure it matches what's in the database
        // Split only on FIRST colon to preserve list IDs that contain colons (like "trending:movies")
        const colonIndex = filters.value.listSource.indexOf(':')
        const listType = filters.value.listSource.substring(0, colonIndex)
        const listId = filters.value.listSource.substring(colonIndex + 1)
        const normalizedId = normalizeListId(listType, listId)
        queryParams.list_source = `${listType}:${normalizedId}`
        console.log(`🔍 Table Filter: Original="${filters.value.listSource}", Split=(${listType}, ${listId}), Normalized="${queryParams.list_source}"`)
      }
      response = await api.getProcessedItems(page, perPage, queryParams)
    }
    
    if (response && response.items) {
      if (reset) {
        // Always reset items array when resetting (including filter changes)
        items.value = response.items
      } else {
        // For infinite scroll, append to existing items
        items.value = [...items.value, ...response.items]
      }
      
      totalItems.value = response.total || response.total_count || 0
      totalPages.value = response.total_pages || 0
      hasMorePages.value = page < totalPages.value
      
      // Debug: Check if items have list_sources
      const itemsWithLists = response.items.filter((item: any) => item.list_sources && item.list_sources.length > 0)
      const activeFilter = filters.value.listSource !== 'all' ? filters.value.listSource : 'none'
      console.log(`📦 Loaded page ${page} (filter: ${activeFilter}): ${response.items.length} items (${response.total || response.total_count || 0} total), ${itemsWithLists.length} with list sources`)
      
      // Debug: Show breakdown by list type
      const listTypeBreakdown = new Map<string, number>()
      response.items.forEach((item: any) => {
        if (item.list_sources && Array.isArray(item.list_sources)) {
          item.list_sources.forEach((source: any) => {
            const key = `${source.list_type}:${source.list_id}`
            listTypeBreakdown.set(key, (listTypeBreakdown.get(key) || 0) + 1)
          })
        }
      })
      if (listTypeBreakdown.size > 0) {
        console.log('📊 List sources breakdown on this page:')
        listTypeBreakdown.forEach((count, key) => {
          console.log(`  - ${key}: ${count} items`)
        })
      }
      
      // Debug: Verify filter is working correctly
      if (filters.value.listSource !== 'all') {
        const filterMatch = response.items.filter((item: any) => {
          if (!item.list_sources || !Array.isArray(item.list_sources)) return false
          return item.list_sources.some((source: any) => 
            `${source.list_type}:${source.list_id}` === filters.value.listSource
          )
        })
        console.log(`✅ Filter verification: ${filterMatch.length}/${response.items.length} items match filter "${filters.value.listSource}"`)
        if (filterMatch.length < response.items.length) {
          console.warn(`⚠️  Some items don't match the active filter! This might indicate a backend filtering issue.`)
        }
      }
      
      // Debug: Show sample item with list sources
      if (itemsWithLists.length > 0) {
        console.log('📦 Sample item with list_sources:', {
          title: itemsWithLists[0].title,
          list_sources: itemsWithLists[0].list_sources
        })
      } else if (response.items.length > 0) {
        console.warn('⚠️ No items have list_sources! Sample item:', response.items[0])
        console.warn('💡 To fix: Re-sync your lists from the Lists page to populate list relationships. This will enable list tags on items and allow filtering by list.')
      }
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

// Refresh data (force refresh, bypass cache)
const refreshData = async () => {
  isRefreshing.value = true
  try {
    currentPage.value = 1
    // Clear cache and force fresh fetch
    itemsCache.clearCache()
    await Promise.all([
      fetchItems(1, true, true), // Force refresh
      fetchStats() // Also refresh stats
    ])
    showSuccess('Items refreshed')
  } catch (error: any) {
    showError('Refresh failed', error.message)
  } finally {
    isRefreshing.value = false
  }
}

// Load next page (for infinite scroll)
const loadNextPage = async () => {
  if (hasMorePages.value && !isLoading.value && !isLoadingMore.value) {
    isLoadingMore.value = true
    currentPage.value++
    
    try {
      await fetchItems(currentPage.value, false)
    } finally {
      isLoadingMore.value = false
    }
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

// Clear all filters
const clearFilters = () => {
  searchQuery.value = ''
  filters.value.mediaType = 'all'
  filters.value.status = 'all'
  filters.value.listSource = 'all'
}

// Watch filters to reset pagination
// Note: List source filter changes trigger a separate watch below for server-side filtering
watch([searchQuery, filters], () => {
  currentPage.value = 1
}, { deep: true })

// Watch list source filter separately to trigger server-side refetch
watch(() => filters.value.listSource, async (newValue, oldValue) => {
  console.log(`👀 List source filter watch triggered: "${oldValue}" → "${newValue}"`)
  if (newValue !== oldValue && process.client) {
    console.log(`🔄 List source filter ACTUALLY changed, refetching...`)
    currentPage.value = 1
    // Clear cache completely to avoid stale data
    itemsCache.clearCache()
    // Reset items array immediately to show loading state
    items.value = []
    // Fetch with new filter (force refresh to bypass any caching)
    await fetchItems(1, true, true)
  } else if (!process.client) {
    console.log(`⚠️ Skipping refetch - not in client context`)
  } else {
    console.log(`⚠️ Skipping refetch - values are the same`)
  }
}, { immediate: false })

// Debug: Watch listSourceOptions changes
watch(listSourceOptions, (newOptions) => {
  console.log('📊 listSourceOptions updated:', newOptions.length, 'options', newOptions)
}, { immediate: true, deep: true })

// Watch view mode changes
watch(viewMode, (newMode) => {
  if (newMode === 'infinite') {
    // Reset to first page and reload all items for infinite scroll
    currentPage.value = 1
    fetchItems(1, true)
  }
})

// Watch display mode changes (grid vs table)
watch(displayMode, (newMode) => {
  // Reload items when switching between grid and table view
  currentPage.value = 1
  fetchItems(1, true)
  
  // Setup or cleanup infinite scroll observer
  if (process.client) {
    if (newMode === 'grid') {
      nextTick(() => {
        if (infiniteScrollTrigger.value) {
          setupInfiniteScroll()
        }
      })
    } else if (infiniteScrollObserver) {
      infiniteScrollObserver.disconnect()
    }
  }
})

// Scroll to top functionality
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// Handle scroll event to show/hide scroll-to-top button
const handleScroll = () => {
  showScrollTop.value = window.scrollY > 400
}

// Track last sync status to detect when syncs complete
const syncStore = useSyncStore()
const lastSyncStatus = ref<string | null>(null)
let syncPollInterval: ReturnType<typeof setInterval> | null = null

// Watch for sync completion and refresh data
watch(() => syncStore.status, async (newStatus) => {
  // If sync just completed (was running, now idle/complete)
  if (lastSyncStatus.value === 'running' && newStatus !== 'running' && process.client) {
    console.log('🔄 Sync completed, refreshing items...')
    // Clear cache and refresh to get new items
    itemsCache.clearCache()
    await Promise.all([
      fetchItems(1, true, true), // Force refresh
      fetchStats()
    ])
  }
  lastSyncStatus.value = newStatus
}, { immediate: true })

// Load data on mount and prefetch next pages in background
onMounted(async () => {
  // Check for list filter in query parameters (from list detail page)
  if (process.client) {
    const route = useRoute()
    const listParam = route.query.list as string
    if (listParam) {
      console.log('📋 Pre-filtering to list:', listParam)
      filters.value.listSource = listParam
    }
  }
  
  // Always fetch fresh data on mount (bypass cache for initial load)
  // This ensures users see latest items when navigating to the page
  itemsCache.clearCache()
  
  await Promise.all([
    fetchItems(1, true, true), // Force refresh on mount
    fetchStats(),
    syncStore.fetchLiveSyncStatus(), // Get current sync status
    listsStore.fetchLists() // Fetch lists for filter dropdown
  ])
  
  // Prefetch next 2 pages in background for smooth pagination
  if (totalPages.value > 1 && displayMode.value === 'grid') {
    setTimeout(() => {
      const pagesToPrefetch = [2, 3].filter(p => p <= totalPages.value)
      if (pagesToPrefetch.length > 0) {
        console.log('🚀 Prefetching next pages for smoother navigation...')
        // Include current filter in prefetch to avoid cache pollution
        const queryParams: any = {}
        if (filters.value.listSource !== 'all') {
          // Normalize the filter value to ensure it matches what's in the database
          // Split only on FIRST colon to preserve list IDs that contain colons (like "trending:movies")
          const colonIndex = filters.value.listSource.indexOf(':')
          const listType = filters.value.listSource.substring(0, colonIndex)
          const listId = filters.value.listSource.substring(colonIndex + 1)
          const normalizedId = normalizeListId(listType, listId)
          queryParams.list_source = `${listType}:${normalizedId}`
        }
        itemsCache.prefetchPages(pagesToPrefetch, perPage, queryParams)
      }
    }, 1000) // Wait 1 second after initial load
  }
  
  // Setup scroll listener for scroll-to-top button
  if (process.client) {
    window.addEventListener('scroll', handleScroll)
    
    // Setup infinite scroll observer (grid view only) after DOM is fully rendered
    if (displayMode.value === 'grid') {
      nextTick(() => {
        if (infiniteScrollTrigger.value) {
          setupInfiniteScroll()
        }
      })
    }
    
    // Poll for sync status changes every 10 seconds
    // This helps detect when syncs complete even if we miss the status change
    syncPollInterval = setInterval(async () => {
      await syncStore.fetchLiveSyncStatus()
    }, 10000)
  }
})

// Setup infinite scroll observer
let infiniteScrollObserver: IntersectionObserver | null = null

const setupInfiniteScroll = () => {
  if (!process.client || !infiniteScrollTrigger.value) return
  
  // Clean up existing observer
  if (infiniteScrollObserver) {
    infiniteScrollObserver.disconnect()
  }
  
  // Create new observer
  infiniteScrollObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      // When the trigger element is visible and we have more pages, load next page
      if (entry.isIntersecting && hasMorePages.value && !isLoadingMore.value && !isLoading.value) {
        console.log('🔄 Infinite scroll triggered, loading next page...')
        loadNextPage()
      }
    },
    {
      root: null, // viewport
      rootMargin: '200px', // Start loading 200px before reaching the trigger
      threshold: 0.1
    }
  )
  
  infiniteScrollObserver.observe(infiniteScrollTrigger.value)
}

// Cleanup scroll listener, infinite scroll observer, and polling
onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('scroll', handleScroll)
    
    if (infiniteScrollObserver) {
      infiniteScrollObserver.disconnect()
    }
    
    if (syncPollInterval) {
      clearInterval(syncPollInterval)
    }
  }
})
</script>

<style scoped>
/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

