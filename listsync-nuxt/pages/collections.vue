<template>
  <div class="space-y-4 sm:space-y-6 px-2 sm:px-4 lg:px-0 pb-24 lg:pb-8 relative">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Collections
        </h1>
        <p class="text-muted-foreground mt-1.5 sm:mt-2 text-xs sm:text-sm">
          Browse popular movie collections and sync them to Overseerr
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          v-if="!selectionMode"
          variant="secondary"
          :icon="CheckSquareIcon"
          @click="selectionMode = true"
          class="touch-manipulation"
          size="sm"
        >
          <span class="hidden sm:inline">Select</span>
          <span class="sm:hidden">Select</span>
        </Button>
        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="collectionsStore.loading"
          @click="refreshData"
          class="w-full sm:w-auto touch-manipulation"
          size="sm"
        >
          <span class="hidden sm:inline">Refresh</span>
          <span class="sm:hidden">Refresh</span>
        </Button>
      </div>
    </div>

    <!-- Random Picks Section -->
    <Card 
      v-if="!isInitialLoading" 
      variant="default" 
      class="glass-card border border-purple-500/30"
    >
      <div class="flex items-center justify-between mb-3 sm:mb-4">
        <div class="flex items-center gap-2 sm:gap-3">
          <div class="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30">
            <component :is="ShuffleIcon" :size="16" class="sm:w-5 sm:h-5 text-purple-400" />
          </div>
          <div>
            <h2 class="text-base sm:text-lg md:text-xl font-bold text-foreground titillium-web-bold">
              Feeling Lucky?
            </h2>
            <p class="text-[10px] sm:text-xs text-muted-foreground">Random picks</p>
          </div>
        </div>
        <Button
          variant="secondary"
          :icon="ShuffleIcon"
          :loading="isLoadingRandomPicks"
          @click="reshuffleRandomPicks"
          class="touch-manipulation"
          size="sm"
        >
          <span class="hidden sm:inline">{{ isLoadingRandomPicks ? 'Spinning...' : 'Respin' }}</span>
          <span class="sm:hidden">{{ isLoadingRandomPicks ? '...' : 'Spin' }}</span>
        </Button>
      </div>

      <div v-if="isLoadingRandomPicks" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
        <div v-for="i in 5" :key="`random-loading-${i}`" class="h-20 sm:h-24 rounded-lg bg-purple-900/20 animate-pulse"></div>
      </div>
      <div v-else-if="randomPicks.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
        <button
          v-for="collection in randomPicks"
          :key="collection.franchise"
          @click="openCollectionDetails(collection)"
          class="group relative p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/10 to-purple-500/5 border border-purple-500/30 hover:border-purple-400/50 hover:from-purple-600/20 hover:to-purple-500/10 transition-all duration-300 text-left touch-manipulation"
        >
          <!-- Synced indicator -->
          <div v-if="isCollectionSynced(collection.franchise)" class="absolute top-2 right-2">
            <CheckCircleIcon :size="12" class="sm:w-[14px] sm:h-[14px] text-green-400" />
          </div>
          
          <h3 class="text-xs sm:text-sm font-semibold text-foreground mb-1.5 sm:mb-2 line-clamp-2 group-hover:text-purple-400 transition-colors pr-6">
            {{ collection.franchise }}
          </h3>
          <div class="flex items-center gap-2 sm:gap-3 text-[10px] sm:text-xs text-muted-foreground">
            <div class="flex items-center gap-1">
              <FilmIcon :size="10" class="sm:w-3 sm:h-3 text-purple-400" />
              <span>{{ collection.totalMovies || 0 }} movies</span>
            </div>
            <div class="flex items-center gap-1">
              <UsersIcon :size="10" class="sm:w-3 sm:h-3 text-blue-400" />
              <span>{{ formatNumber(collection.totalVotes || 0) }} votes</span>
            </div>
          </div>
        </button>
      </div>
      <div v-else class="text-center py-6">
        <p class="text-xs sm:text-sm text-muted-foreground mb-2">No random collections available</p>
        <Button
          variant="secondary"
          size="sm"
          @click="reshuffleRandomPicks"
          class="touch-manipulation"
        >
          Try Again
        </Button>
      </div>
    </Card>

    <!-- Random Picks Skeleton -->
    <Card 
      v-else-if="isInitialLoading" 
      variant="default" 
      class="glass-card border border-purple-500/30"
    >
      <div class="flex items-center justify-between mb-3 sm:mb-4">
        <div class="flex items-center gap-2 sm:gap-3">
          <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-purple-900/30 animate-pulse"></div>
          <div>
            <div class="h-5 sm:h-6 w-32 sm:w-40 bg-purple-900/30 rounded animate-pulse mb-1.5"></div>
            <div class="h-3 w-20 sm:w-24 bg-purple-900/20 rounded animate-pulse"></div>
          </div>
        </div>
        <div class="w-16 sm:w-20 h-8 bg-purple-900/30 rounded-lg animate-pulse"></div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
        <div v-for="i in 5" :key="`random-skeleton-${i}`" class="h-20 sm:h-24 rounded-lg bg-purple-900/20 animate-pulse"></div>
      </div>
    </Card>

    <!-- Hero Carousel: Top 20 Popular Collections -->
    <CollectionCarousel
      v-if="collectionsStore.popularCollections.length > 0"
      :collections="collectionsStore.popularCollections"
      :synced-collections="new Set(Object.keys(syncedCollectionsInfo))"
      :syncing-collections="syncingCollections"
      @sync="handleSyncCollection"
      @open-details="openCollectionDetails"
    />

    <!-- Loading State for Popular Collections -->
    <div v-else-if="isInitialLoading && collectionsStore.popularCollections.length === 0" class="space-y-4">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-purple-900/30 animate-pulse"></div>
        <div class="flex-1">
          <div class="h-5 sm:h-6 w-40 sm:w-48 bg-purple-900/30 rounded animate-pulse mb-2"></div>
          <div class="h-3 w-24 sm:w-32 bg-purple-900/20 rounded animate-pulse"></div>
        </div>
      </div>
      <div class="flex gap-3 sm:gap-4 overflow-hidden">
        <div v-for="i in 6" :key="`carousel-skeleton-${i}`" class="w-[200px] sm:w-[240px] md:w-[260px] h-[320px] sm:h-[380px] rounded-xl bg-purple-900/20 animate-pulse flex-shrink-0"></div>
      </div>
    </div>

    <!-- Library Section: All Collections -->
    <div class="space-y-3 sm:space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <LayersIcon :size="20" class="text-purple-400" />
          </div>
          <div>
            <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold">
              All Collections
            </h2>
            <p class="text-xs text-muted-foreground">
              {{ collectionsStore.total ? formatNumber(collectionsStore.total) : 'Browse all' }} available collections
            </p>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- View Toggle -->
          <ViewToggle v-model="viewMode" />
          
          <!-- Selection Mode Buttons -->
          <template v-if="selectionMode">
            <Button
              variant="ghost"
              size="sm"
              @click="selectAll"
              class="touch-manipulation"
            >
              Select All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              @click="selectionMode = false; selectedCollections.clear()"
              class="touch-manipulation"
            >
              Cancel
            </Button>
          </template>
        </div>
      </div>

      <!-- Search and Sort -->
      <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input
            v-model="searchQuery"
            placeholder="Search collections..."
            :icon="SearchIcon"
            @input="handleSearch"
          />
          <Select
            v-model="sortBy"
            :options="sortOptions"
            @update:model-value="handleSortChange"
          />
        </div>
      </Card>

      <!-- Loading State (Initial) -->
      <div v-if="collectionsStore.loading && collectionsStore.collections.length === 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">
        <PosterCardSkeleton v-for="i in 50" :key="`library-skeleton-${i}`" />
      </div>

      <!-- Collections Content -->
      <template v-else>
        <!-- Grid View -->
        <div v-if="viewMode === 'grid' && collectionsStore.collections.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">
          <CollectionCard
            v-for="collection in collectionsStore.collections"
            :key="collection.franchise"
            :collection="collection"
            :is-syncing="isSyncingCollection(collection.franchise)"
            :selectable="selectionMode"
            :is-selected="selectedCollections.has(collection.franchise)"
            :is-synced="isCollectionSynced(collection.franchise)"
            :last-synced="getLastSynced(collection.franchise)"
            @sync="handleSyncCollection"
            @toggle-select="toggleCollectionSelection(collection.franchise)"
            @open-details="openCollectionDetails(collection)"
          />
        </div>

        <!-- List View -->
        <div v-else-if="viewMode === 'list' && collectionsStore.collections.length > 0" class="space-y-2">
          <CollectionListItem
            v-for="collection in collectionsStore.collections"
            :key="collection.franchise"
            :collection="collection"
            :is-syncing="isSyncingCollection(collection.franchise)"
            :is-synced="isCollectionSynced(collection.franchise)"
            :selectable="selectionMode"
            :is-selected="selectedCollections.has(collection.franchise)"
            @sync="handleSyncCollection"
            @toggle-select="toggleCollectionSelection(collection.franchise)"
            @open-details="openCollectionDetails(collection)"
            @click="openCollectionDetails(collection)"
          />
        </div>

        <!-- Infinite Scroll Trigger -->
        <div
          v-if="collectionsStore.collections.length > 0 && (hasMorePages || isLoadingMore)"
          ref="infiniteScrollTrigger"
          class="h-20 flex items-center justify-center py-8"
        >
          <div v-if="isLoadingMore" class="flex items-center gap-2 text-sm text-muted-foreground">
            <LoaderIcon :size="16" class="animate-spin" />
            <span>Loading more collections...</span>
          </div>
          <div v-else-if="!hasMorePages && collectionsStore.collections.length > 0" class="text-xs text-muted-foreground text-center py-4">
            No more collections to load
          </div>
        </div>

        <!-- Empty State -->
        <Card v-if="collectionsStore.collections.length === 0" variant="default" class="glass-card">
          <div class="text-center py-8 sm:py-12 px-4">
            <p class="text-sm sm:text-base text-muted-foreground">No collections found</p>
          </div>
        </Card>
      </template>
    </div>

    <!-- Scroll to Top Button -->
    <Transition name="fade">
      <button
        v-if="showScrollTop"
        @click="scrollToTop"
        class="fixed bottom-20 right-4 sm:right-6 z-30 p-3 rounded-full bg-purple-600/90 hover:bg-purple-500/90 backdrop-blur-sm border border-purple-500/50 shadow-lg transition-all duration-300 hover:scale-110 touch-manipulation"
        aria-label="Scroll to top"
      >
        <ArrowUpIcon :size="20" class="text-white" />
      </button>
    </Transition>

    <!-- Bulk Actions -->
    <BulkActions
      v-if="selectionMode"
      ref="bulkActionsRef"
      :selected-count="selectedCollections.size"
      @bulk-sync="handleBulkSync"
      @deselect-all="deselectAll"
    />

    <!-- Collection Details Modal -->
    <CollectionDetailsModal
      v-model="showCollectionDetails"
      :collection="selectedCollection"
    />
  </div>
</template>

<script setup lang="ts">
import { onActivated, watch } from 'vue'
import {
  RefreshCw as RefreshIcon,
  Search as SearchIcon,
  CheckSquare as CheckSquareIcon,
  Layers as LayersIcon,
  Film as FilmIcon,
  Star as StarIcon,
  CheckCircle2 as CheckCircleIcon,
  ArrowUp as ArrowUpIcon,
  Loader2 as LoaderIcon,
  Shuffle as ShuffleIcon,
  Users as UsersIcon,
} from 'lucide-vue-next'
import CollectionCard from '~/components/collections/CollectionCard.vue'
import CollectionCarousel from '~/components/collections/CollectionCarousel.vue'
import CollectionListItem from '~/components/collections/CollectionListItem.vue'
import CollectionDetailsModal from '~/components/collections/CollectionDetailsModal.vue'
import ViewToggle from '~/components/collections/ViewToggle.vue'
import PosterCardSkeleton from '~/components/items/PosterCardSkeleton.vue'
import BulkActions from '~/components/collections/BulkActions.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'
import Select from '~/components/ui/Select.vue'
import LoadingSpinner from '~/components/ui/LoadingSpinner.vue'
import type { Collection } from '~/types'

// Set page title
useHead({
  title: 'Collections - ListSync',
})

const collectionsStore = useCollectionsStore()
const { showSuccess, showError } = useToast()
const api = useApiService()
const router = useRouter()

// State
const searchQuery = ref('')
const sortBy = ref('total_votes') // Default to total votes for quality content first
const viewMode = ref<'grid' | 'list'>('grid') // Default to grid view
const syncingCollections = ref<Set<string>>(new Set())
const selectionMode = ref(false)
const selectedCollections = ref<Set<string>>(new Set())
const syncedCollectionsInfo = ref<Record<string, { last_synced: string | null, item_count: number }>>({})
const showScrollTop = ref(false)
const isLoadingMore = ref(false)
const hasMorePages = ref(true)
const infiniteScrollTrigger = ref<HTMLElement | null>(null)
const bulkActionsRef = ref<InstanceType<typeof BulkActions> | null>(null)
const isLoadingStats = ref(true)
const showCollectionDetails = ref(false)
const selectedCollection = ref<Collection | null>(null)
const randomPicks = ref<Collection[]>([])
const isLoadingRandomPicks = ref(false)
const isInitialLoading = ref(true)
// Cache for preloaded random collections (ready for instant display)
const preloadedRandomPicks = ref<Collection[]>([])
const isPreloadingRandomPicks = ref(false)

// Helper function to load posters for collections
const loadPostersForCollections = async (collections: Collection[]) => {
  const api = useApiService()
  
  // Load posters for the collections (use cache if available, but don't wait)
  const collectionsWithPosters = collections.map((collection) => {
    // Check cache first - use immediately if available
    const cachedPoster = collectionsStore.posterCache.get(collection.franchise)
    return {
      ...collection,
      poster_url: cachedPoster !== undefined ? cachedPoster : null
    }
  })
  
  // Load missing posters in background using batch endpoint (much faster)
  const uncachedCollections = collections.filter(
    collection => !collectionsStore.posterCache.has(collection.franchise)
  )
  
  if (uncachedCollections.length > 0) {
    // Use batch endpoint for faster loading
    api.getCollectionPostersBatch(uncachedCollections.map(c => c.franchise))
      .then((batchResponse) => {
        if (batchResponse && batchResponse.posters) {
          // Update cache for each poster
          batchResponse.posters.forEach((posterData) => {
            const posterUrl = posterData.poster_url || null
            const franchise = posterData.franchise
            collectionsStore.posterCache.set(franchise, posterUrl)
            
            // Update the collection in the provided array if it exists
            const index = collectionsWithPosters.findIndex(c => c.franchise === franchise)
            if (index !== -1) {
              collectionsWithPosters[index] = {
                ...collectionsWithPosters[index],
                poster_url: posterUrl
              }
            }
          })
        }
      })
      .catch(err => {
        console.warn('Error loading batch collection posters:', err)
        // Silently fail - posters will load on demand
      })
  }
  
  return collectionsWithPosters
}

// Hardcoded 5 medium/voted collections for instant display (no API call needed)
const DEFAULT_RANDOM_PICKS: Collection[] = [
  {
    franchise: "John Wick Collection",
    popularityScore: 6.6128,
    averageRating: 7.5,
    totalMovies: 4,
    totalVotes: 52762,
    poster_url: null // Will be loaded in background
  },
  {
    franchise: "Mission: Impossible Collection",
    popularityScore: 6.6074,
    averageRating: 7.05,
    totalMovies: 8,
    totalVotes: 59731,
    poster_url: null
  },
  {
    franchise: "The Matrix Collection",
    popularityScore: 6.3894,
    averageRating: 7.11,
    totalMovies: 4,
    totalVotes: 55138,
    poster_url: null
  },
  {
    franchise: "Indiana Jones Collection",
    popularityScore: 6.4864,
    averageRating: 7.12,
    totalMovies: 5,
    totalVotes: 46256,
    poster_url: null
  },
  {
    franchise: "The Bourne Collection",
    popularityScore: 6.3941,
    averageRating: 6.97,
    totalMovies: 5,
    totalVotes: 37579,
    poster_url: null
  }
]

// Silently preload random collections in background (called on page mount and after "Respin")
const preloadRandomPicks = async () => {
  if (isPreloadingRandomPicks.value) return // Already preloading
  
  isPreloadingRandomPicks.value = true
  
  try {
    // Fetch from API for variety (for next "Respin")
    const api = useApiService()
    const response = await api.getRandomCollections(5)
    
    if (response && response.collections && Array.isArray(response.collections)) {
      const validCollections = response.collections.filter(c => c && c.franchise)
      
      if (validCollections.length > 0) {
        // Load posters in background (non-blocking)
        const collectionsWithPosters = await loadPostersForCollections(validCollections)
        preloadedRandomPicks.value = collectionsWithPosters
        console.log('✅ Preloaded 5 random collections for next "Respin"')
      }
    }
  } catch (error) {
    console.warn('Failed to preload random collections (non-critical):', error)
    // Silently fail - will use hardcoded on next reshuffle if needed
  } finally {
    isPreloadingRandomPicks.value = false
  }
}

// Reshuffle random picks - use cached data first for instant display, then fetch new ones
const reshuffleRandomPicks = async () => {
  isLoadingRandomPicks.value = true
  
  // If we have preloaded picks, use them instantly (no loading state)
  if (preloadedRandomPicks.value.length > 0) {
    randomPicks.value = [...preloadedRandomPicks.value]
    isLoadingRandomPicks.value = false
    
    // Clear the cache so next time we fetch fresh
    const usedPicks = preloadedRandomPicks.value
    preloadedRandomPicks.value = []
    
    // Immediately start preloading new ones in background for next time
    preloadRandomPicks()
    
    // Also refresh posters in background if needed
    loadPostersForCollections(randomPicks.value)
    
    return
  }
  
  // No cache available - fetch now (this should rarely happen)
  randomPicks.value = [] // Clear previous picks
  
  try {
    const api = useApiService()
    const response = await api.getRandomCollections(5)
    
    if (response && response.collections && Array.isArray(response.collections)) {
      // Ensure each collection has required fields
      const validCollections = response.collections.filter(c => c && c.franchise)
      
      if (validCollections.length === 0) {
        randomPicks.value = []
        isLoadingRandomPicks.value = false
        return
      }
      
      // Load posters and set immediately
      const collectionsWithPosters = await loadPostersForCollections(validCollections)
      randomPicks.value = collectionsWithPosters
      
      // Preload next batch in background
      preloadRandomPicks()
    } else {
      console.error('❌ Invalid response from getRandomCollections:', response)
      randomPicks.value = []
    }
  } catch (error: any) {
    console.error('❌ Error fetching random collections:', error)
    randomPicks.value = []
  } finally {
    isLoadingRandomPicks.value = false
  }
}

// Stats
const stats = computed(() => {
  if (isLoadingStats.value) {
    return {
      totalCollections: 0,
      totalMovies: 0,
      averageRating: 0,
      syncedCount: 0
    }
  }
  
  const allCollections = [
    ...collectionsStore.popularCollections,
    ...collectionsStore.collections
  ]
  
  // Remove duplicates by franchise name
  const uniqueCollections = Array.from(
    new Map(allCollections.map(c => [c.franchise, c])).values()
  )
  
  const totalCollections = collectionsStore.total || uniqueCollections.length
  const totalMovies = uniqueCollections.reduce((sum, c) => sum + (c.totalMovies || 0), 0)
  const averageRating = uniqueCollections.length > 0
    ? uniqueCollections.reduce((sum, c) => sum + (c.averageRating || 0), 0) / uniqueCollections.length
    : 0
  const syncedCount = Object.keys(syncedCollectionsInfo.value).length
  
  return {
    totalCollections,
    totalMovies,
    averageRating,
    syncedCount
  }
})

// Sort options
const sortOptions = [
  { label: 'Total Votes', value: 'total_votes' },
  { label: 'Popularity', value: 'popularity' },
  { label: 'Rating', value: 'rating' },
  { label: 'Movie Count', value: 'movie_count' },
  { label: 'Name', value: 'name' },
]

// Check if a collection is currently syncing
const isSyncingCollection = (franchise: string) => {
  return syncingCollections.value.has(franchise)
}

// Check if collection is synced
const isCollectionSynced = (franchise: string) => {
  return franchise in syncedCollectionsInfo.value
}

// Get last synced timestamp
const getLastSynced = (franchise: string): string | null => {
  return syncedCollectionsInfo.value[franchise]?.last_synced || null
}

// Toggle collection selection
const toggleCollectionSelection = (franchise: string) => {
  if (selectedCollections.value.has(franchise)) {
    selectedCollections.value.delete(franchise)
  } else {
    selectedCollections.value.add(franchise)
  }
}

// Select all visible collections
const selectAll = () => {
  const allFranchises = [
    ...collectionsStore.popularCollections.map(c => c.franchise),
    ...collectionsStore.collections.map(c => c.franchise)
  ]
  allFranchises.forEach(f => selectedCollections.value.add(f))
}

// Deselect all
const deselectAll = () => {
  selectedCollections.value.clear()
  selectionMode.value = false
}

// Open collection details modal
const openCollectionDetails = (collection: Collection) => {
  selectedCollection.value = collection
  showCollectionDetails.value = true
}

// Handle collection sync - redirect immediately, let backend catch up
const handleSyncCollection = async (franchise: string) => {
  syncingCollections.value.add(franchise)
  
  // Optimistically mark as synced immediately (will be confirmed when we refresh)
  syncedCollectionsInfo.value[franchise] = {
    last_synced: new Date().toISOString(),
    item_count: 0 // Will be updated when we refresh
  }
  
  // Fire sync request but don't wait for it - redirect immediately
  collectionsStore.syncCollection(franchise).then(() => {
    // Sync succeeded - refresh synced info to get accurate data
    fetchSyncedInfo()
  }).catch((error: any) => {
    // Sync failed - remove optimistic update
    delete syncedCollectionsInfo.value[franchise]
    console.error('Sync error:', error)
    showError('Sync failed', error.message || 'Failed to sync collection')
    syncingCollections.value.delete(franchise)
  })
  
  showSuccess('Sync Started', `Syncing ${franchise} collection...`)
  
  // Redirect immediately - don't wait for sync to complete
  if (process.client) {
    setTimeout(() => {
      try {
        router.push('/logs')
      } catch (err) {
        console.error('Navigation error:', err)
        window.location.href = '/logs'
      }
    }, 100) // Reduced delay for faster redirect
  }
}

// Handle bulk sync
const handleBulkSync = async () => {
  if (selectedCollections.value.size === 0) return
  
  const franchises = Array.from(selectedCollections.value)
  bulkActionsRef.value?.setSyncing(true)
  
  let completed = 0
  const total = franchises.length
  
  try {
    for (const franchise of franchises) {
      syncingCollections.value.add(franchise)
      try {
        await collectionsStore.syncCollection(franchise)
        completed++
        const progress = Math.round((completed / total) * 100)
        bulkActionsRef.value?.setProgress(progress, completed)
      } catch (error: any) {
        console.error(`Failed to sync ${franchise}:`, error)
      } finally {
        syncingCollections.value.delete(franchise)
      }
    }
    
    showSuccess('Bulk Sync Started', `Started sync for ${completed} of ${total} collections`)
    // Redirect to logs page after bulk sync
    if (process.client) {
      setTimeout(() => {
        try {
          router.push('/logs')
        } catch (err) {
          console.error('Navigation error:', err)
          window.location.href = '/logs'
        }
      }, 150)
    }
    selectedCollections.value.clear()
    selectionMode.value = false
  } catch (error: any) {
    showError('Bulk Sync Failed', error.message || 'Failed to sync collections')
  } finally {
    bulkActionsRef.value?.setSyncing(false)
    bulkActionsRef.value?.setProgress(0, 0)
  }
}

// Fetch synced collections info
const fetchSyncedInfo = async () => {
  try {
    const response = await api.getSyncedCollectionsInfo()
    if (response?.synced_collections) {
      syncedCollectionsInfo.value = response.synced_collections
    }
  } catch (error) {
    console.warn('Failed to fetch synced collections info:', error)
  } finally {
    isLoadingStats.value = false
    isInitialLoading.value = false
  }
}

// Handle search
const handleSearch = debounce(() => {
  loadPage(1, true)
}, 300)

// Handle sort change
const handleSortChange = () => {
  loadPage(1, true)
}

// Load page - optimized: load 20 initially for faster first render
const loadPage = (page: number, reset: boolean = false) => {
  if (reset) {
    collectionsStore.collections = []
    hasMorePages.value = true
  }
  // Use smaller limit (20) for initial load, 50 for subsequent pages
  const limit = (page === 1 && reset) ? 20 : 50
  collectionsStore.fetchAll(page, limit, searchQuery.value, sortBy.value, false).then(() => {
    hasMorePages.value = page < collectionsStore.totalPages
    // Setup infinite scroll after initial load
    if (process.client && collectionsStore.collections.length > 0) {
      nextTick(() => {
        setupInfiniteScroll()
      })
    }
  })
}

// Load next page (for infinite scroll) - optimized like items page
const loadNextPage = async () => {
  if (isLoadingMore.value || !hasMorePages.value || collectionsStore.loading) return
  
  isLoadingMore.value = true
  const nextPage = collectionsStore.currentPage + 1
  
  try {
    // Use append=true to add to existing collections
    await collectionsStore.fetchAll(nextPage, 50, searchQuery.value, sortBy.value, true)
    hasMorePages.value = nextPage < collectionsStore.totalPages
  } catch (error) {
    console.error('Error loading next page:', error)
    showError('Failed to load more', 'Could not load additional collections')
  } finally {
    isLoadingMore.value = false
    // Re-setup infinite scroll after loading more
    nextTick(() => {
      setupInfiniteScroll()
    })
  }
}

// Refresh data
const refreshData = async () => {
  isLoadingStats.value = true
  isInitialLoading.value = true
  await Promise.all([
    collectionsStore.fetchPopular(),
    loadPage(1, true),
    fetchSyncedInfo()
  ])
  isInitialLoading.value = false
}

// Scroll to top
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// Handle scroll event
const handleScroll = () => {
  showScrollTop.value = window.scrollY > 400
}

// Setup infinite scroll
let infiniteScrollObserver: IntersectionObserver | null = null

const setupInfiniteScroll = () => {
  if (!process.client || !infiniteScrollTrigger.value) return
  
  if (infiniteScrollObserver) {
    infiniteScrollObserver.disconnect()
  }
  
  infiniteScrollObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry.isIntersecting && hasMorePages.value && !isLoadingMore.value && !collectionsStore.loading) {
        console.log('🔄 Infinite scroll triggered, loading next page...')
        loadNextPage()
      }
    },
    {
      root: null,
      rootMargin: '200px',
      threshold: 0.1
    }
  )
  
  infiniteScrollObserver.observe(infiniteScrollTrigger.value)
}

// Format number
const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Format rating
const formatRating = (rating: number) => {
  return rating ? rating.toFixed(1) : 'N/A'
}

// Debounce helper
function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout | null = null
  return function executedFunction(...args: any[]) {
    const later = () => {
      timeout = null
      func(...args)
    }
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Prefetch collections data before page opens - DISABLED to prevent slow initial load
// Collections load fast enough without prefetching
if (process.client) {
  // Prefetching disabled - page loads instantly without it
}

// Load initial data - optimized for instant display
onMounted(async () => {
  isLoadingStats.value = true
  
  // Load popular collections and first page in parallel
  // Popular collections show immediately, posters load in background
  await Promise.all([
    collectionsStore.fetchPopular(), // Shows cards instantly, posters load progressively
    loadPage(1, true), // Shows first 20 collections
    fetchSyncedInfo() // Load synced info
  ])
  
  // Mark initial loading as complete - page is now interactive
  isInitialLoading.value = false
  
  // Show hardcoded collections immediately (instant display, no API call)
  randomPicks.value = [...DEFAULT_RANDOM_PICKS]
  
  // Load posters in background (non-blocking)
  loadPostersForCollections(randomPicks.value).then((collectionsWithPosters) => {
    randomPicks.value = collectionsWithPosters
  })
  
  // Preload next batch for "Respin" (will use API for variety)
  preloadRandomPicks()
  
  if (process.client) {
    window.addEventListener('scroll', handleScroll)
    
    // Setup infinite scroll after initial data load
    nextTick(() => {
      if (infiniteScrollTrigger.value) {
        setupInfiniteScroll()
      }
    })
    
    // NO automatic prefetching - let user scroll naturally
    // Removed the page 2 prefetch that was causing "bounce"
  }
})

// Refresh synced info when page becomes active again (user returns from logs)
onActivated(() => {
  // Refresh synced info to get latest status
  fetchSyncedInfo()
})

// Cleanup
onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('scroll', handleScroll)
    if (infiniteScrollObserver) {
      infiniteScrollObserver.disconnect()
    }
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
