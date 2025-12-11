<template>
  <ClientOnly fallback-tag="div" fallback="Loading lists...">
    <div class="space-y-4 sm:space-y-6 px-2 sm:px-0">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Lists
        </h1>
        <p class="text-muted-foreground mt-1.5 sm:mt-2 text-sm sm:text-base">
          Manage your watchlists from IMDb, Trakt, Letterboxd, AniList, TMDB, Simkl, and more
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2 sm:gap-3">
        <!-- View Mode Toggle -->
        <div class="flex items-center gap-1 p-1 rounded-lg bg-black/20 border border-purple-500/20">
          <button
            type="button"
            :class="[
              'p-1.5 rounded transition-all',
              viewMode === 'grid' 
                ? 'bg-purple-500/20 text-purple-300' 
                : 'text-muted-foreground hover:text-foreground'
            ]"
            @click="viewMode = 'grid'"
            title="Grid View"
          >
            <component :is="GridIcon" :size="16" />
          </button>
          <button
            type="button"
            :class="[
              'p-1.5 rounded transition-all',
              viewMode === 'list' 
                ? 'bg-purple-500/20 text-purple-300' 
                : 'text-muted-foreground hover:text-foreground'
            ]"
            @click="viewMode = 'list'"
            title="List View"
          >
            <component :is="ListIcon" :size="16" />
          </button>
        </div>

        <Button
          variant="ghost"
          :icon="UploadIcon"
          @click="showImportModal = true"
          class="touch-manipulation text-xs sm:text-sm"
          size="sm"
        >
          <span class="hidden sm:inline">Import</span>
          <span class="sm:hidden">Import</span>
        </Button>

        <Button
          v-if="listsStore.filteredLists.length > 0"
          variant="ghost"
          :icon="DownloadIcon"
          @click="handleExportLists"
          class="touch-manipulation text-xs sm:text-sm"
          size="sm"
        >
          <span class="hidden sm:inline">Export</span>
          <span class="sm:hidden">Export</span>
        </Button>

        <Button
          variant="ghost"
          :icon="selectionMode ? XIcon : CheckSquareIcon"
          @click="toggleSelectionMode"
          class="touch-manipulation text-xs sm:text-sm"
          size="sm"
        >
          {{ selectionMode ? 'Cancel' : 'Select' }}
        </Button>

        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="listsStore.loading"
          @click="handleRefresh"
          class="touch-manipulation text-xs sm:text-sm"
          size="sm"
        >
          Refresh
        </Button>

        <Button
          variant="primary"
          :icon="PlusIcon"
          @click="showAddModal = true"
          class="touch-manipulation text-xs sm:text-sm flex-1 sm:flex-initial"
          size="sm"
        >
          Add List
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <ListFilters />

    <!-- Loading State with Skeletons -->
    <div v-if="listsStore.loading && listsStore.lists.length === 0" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ListCardSkeleton v-for="i in 6" :key="`skeleton-${i}`" />
      </div>
    </div>

    <!-- Lists Content -->
    <template v-else>
      <!-- Stats Bar - Wrapped in ClientOnly to avoid SSR hydration issues -->
      <ClientOnly>
        <div v-if="listsStore.lists.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6">
          <Card variant="hover" class="group/stat cursor-default">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-xs sm:text-sm text-muted-foreground mb-1">Total Lists</p>
                <p class="text-2xl sm:text-3xl font-bold text-foreground tabular-nums">
                  <AnimatedCounter :value="listsStore.totalLists" />
                </p>
              </div>
              <div class="p-3 sm:p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/stat:from-purple-500/30 group-hover/stat:to-purple-600/30 transition-all duration-300">
                <component :is="ListIcon" :size="24" class="sm:w-7 sm:h-7 text-purple-400 group-hover/stat:scale-110 transition-transform duration-300" />
              </div>
            </div>
          </Card>

          <Card variant="hover" class="group/stat cursor-default">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-xs sm:text-sm text-muted-foreground mb-1">Total Items</p>
                <p class="text-2xl sm:text-3xl font-bold text-foreground tabular-nums">
                  <AnimatedCounter :value="listsStore.totalItems" />
                </p>
              </div>
              <div class="p-3 sm:p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/stat:from-purple-500/30 group-hover/stat:to-purple-600/30 transition-all duration-300">
                <component :is="LayersIcon" :size="24" class="sm:w-7 sm:h-7 text-purple-400 group-hover/stat:scale-110 transition-transform duration-300" />
              </div>
            </div>
          </Card>

          <Card variant="hover" class="group/stat cursor-default sm:col-span-2 lg:col-span-1">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-xs sm:text-sm text-muted-foreground mb-1">Active Filters</p>
                <p class="text-2xl sm:text-3xl font-bold text-foreground tabular-nums">
                  {{ listsStore.hasActiveFilters ? listsStore.activeFilterCount || 1 : 0 }}
                </p>
              </div>
              <div :class="[
                'p-3 sm:p-4 rounded-xl transition-all duration-300',
                listsStore.hasActiveFilters 
                  ? 'bg-gradient-to-br from-green-500/20 to-emerald-600/20 group-hover/stat:from-green-500/30 group-hover/stat:to-emerald-600/30'
                  : 'bg-gradient-to-br from-gray-500/20 to-gray-600/20 group-hover/stat:from-gray-500/30 group-hover/stat:to-gray-600/30'
              ]">
                <component :is="FilterIcon" :size="24" class="sm:w-7 sm:h-7 transition-transform duration-300 group-hover/stat:scale-110" :class="listsStore.hasActiveFilters ? 'text-green-400' : 'text-gray-400'" />
              </div>
            </div>
          </Card>
        </div>
      </ClientOnly>

      <!-- Lists Grid View -->
      <ListsGrid
        v-if="listsStore.filteredLists.length > 0 && viewMode === 'grid'"
        :lists="listsStore.filteredLists"
        :selectable="selectionMode"
        :selected-lists="selectedLists"
        @sync-list="handleSyncList"
        @delete-list="handleDeleteList"
        @toggle-select="toggleListSelection"
        @open-details="openListDetails"
      />

      <!-- Lists List View -->
      <div v-else-if="listsStore.filteredLists.length > 0 && viewMode === 'list'" class="space-y-3">
        <ListCard
          v-for="list in listsStore.filteredLists"
          :key="`${list.list_type}-${list.list_id}`"
          :list="list"
          :selectable="selectionMode"
          :is-selected="isListSelected(list)"
          class="list-view-card"
          @sync="handleSyncList(list.list_type, list.list_id)"
          @delete="handleDeleteList(list.list_type, list.list_id)"
          @toggle-select="toggleListSelection(list)"
          @open-details="openListDetails"
        />
      </div>

      <!-- Empty State -->
      <EmptyState
        v-else-if="listsStore.filteredLists.length === 0 && !listsStore.loading"
        :icon="listsStore.hasActiveFilters ? SearchIcon : ListIcon"
        :title="listsStore.hasActiveFilters ? 'No lists found' : 'No lists yet'"
        :description="listsStore.hasActiveFilters ? 'Try adjusting your filters' : 'Add your first list to get started'"
        :action-label="listsStore.hasActiveFilters ? 'Clear Filters' : 'Add List'"
        :action-icon="listsStore.hasActiveFilters ? XIcon : PlusIcon"
        @action="listsStore.hasActiveFilters ? listsStore.clearFilters() : showAddModal = true"
      />
    </template>

    <!-- Add List Modal -->
    <AddListModal
      v-model="showAddModal"
      @list-added="handleListAdded"
    />

    <!-- Import Lists Modal -->
    <ImportListsModal
      v-model="showImportModal"
      @lists-imported="handleListsImported"
    />

    <!-- List Details Modal -->
    <ListDetailsModal
      v-model="showDetailsModal"
      :list="selectedList"
      @sync="handleSyncList"
      @delete="handleDeleteList"
      @view-items="handleViewItems"
    />

    <!-- Delete Confirmation Modal -->
    <DeleteListModal
      v-model="showDeleteModal"
      :list="deleteTarget ? listsStore.lists.find(l => l.list_type === deleteTarget.type && l.list_id === deleteTarget.id) : null"
      @confirm="handleDeleteConfirm"
      @cancel="showDeleteModal = false"
    />

    <!-- Bulk Actions -->
    <BulkActions
      v-if="selectionMode"
      :selected-count="selectedLists.size"
      @bulk-sync="handleBulkSync"
      @bulk-delete="handleBulkDelete"
      @deselect-all="deselectAll"
    />

    <!-- Sync Progress Modal -->
    <SyncProgress
      :is-visible="showSyncProgress"
      :status="syncStatus"
      :current-item="syncCurrentItem"
      :items-processed="syncItemsProcessed"
      :total-items="syncTotalItems"
      :status-message="syncStatusMessage"
      :errors="syncErrors"
      @cancel="handleCancelSync"
      @close="closeSyncProgress"
    />
  </div>
  </ClientOnly>
</template>

<script setup lang="ts">
// Disable SSR for this page to avoid hydration issues with complex reactive computations
definePageMeta({
  ssr: false
})

import {
  RefreshCw as RefreshIcon,
  Plus as PlusIcon,
  List as ListIcon,
  Layers as LayersIcon,
  Filter as FilterIcon,
  Search as SearchIcon,
  X as XIcon,
  CheckSquare as CheckSquareIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Grid3x3 as GridIcon,
} from 'lucide-vue-next'
import type { List } from '~/types'

// Initialize stores directly - SSR is disabled for this page so this is safe
// This matches the pattern used in index.vue, collections.vue, and other working pages
const listsStore = useListsStore()
const syncStore = useSyncStore()
const { showSuccess, showError } = useToast()

// Router and route (declare early to avoid TDZ issues)
const route = useRoute()
const router = useRouter()

// Set page title
useHead({
  title: 'Manage Lists - ListSync',
})

// State
const showAddModal = ref(false)
const showImportModal = ref(false)
const selectionMode = ref(false)
const selectedLists = ref<Set<string>>(new Set())

// View mode with SSR-safe initialization (no localStorage access during SSR)
const viewMode = ref<'grid' | 'list'>('grid')

// Sync Progress State
const showSyncProgress = ref(false)
const syncStatus = ref('idle')
const syncCurrentItem = ref<string | null>(null)
const syncItemsProcessed = ref(0)
const syncTotalItems = ref(0)
const syncStatusMessage = ref('')
const syncErrors = ref<string[]>([])

// Delete Confirmation State
const showDeleteModal = ref(false)
const deleteTarget = ref<{ type: string; id: string } | null>(null)

// List Details State
const showDetailsModal = ref(false)
const selectedList = ref<List | null>(null)

// Auto-refresh polling timeout
let refreshTimeout: ReturnType<typeof setTimeout> | null = null
let visibilityRefreshTimeout: ReturnType<typeof setTimeout> | null = null
let autoRefreshStarted = false
const runtimeWatchStops: Array<() => void> = []
let hasRegisteredRuntimeWatchers = false

// Guard to prevent duplicate modal opens
let isOpeningModal = false

// Event listener references for cleanup consolidation
let globalErrorHandler: ((event: ErrorEvent) => void) | null = null
let globalRejectionHandler: ((event: PromiseRejectionEvent) => void) | null = null
let visibilityChangeHandler: (() => void) | null = null
let storageEventHandler: ((e: StorageEvent) => void) | null = null
let focusEventHandler: (() => void) | null = null

// Track initialization state - MUST be declared before onUnmounted that references it
let isInitialized = false

// Lightweight diagnostics (client-only)
const logDiag = (...args: any[]) => {
  if (process.client) {
    console.debug('[Lists][diag]', ...args)
  }
}

// Setup automatic refresh polling
const setupAutoRefresh = () => {
  if (!process.client) return
  
  // Prevent duplicate polling loops
  if (autoRefreshStarted && refreshTimeout) {
    return
  }
  autoRefreshStarted = true
  
  // Clear existing timeout
  if (refreshTimeout) {
    clearTimeout(refreshTimeout)
    refreshTimeout = null
  }
  
  // Poll more frequently when sync is active, less frequently when idle
  const getPollInterval = () => {
    try {
      if (syncStore.isSyncing) {
        return 3000 // 3 seconds when syncing (more responsive)
      }
      // Check if sync just completed (within last 60 seconds)
      if (syncStore.lastFetched) {
        const timeSinceLastSync = Date.now() - syncStore.lastFetched.getTime()
        if (timeSinceLastSync < 60000) {
          return 5000 // 5 seconds for 60 seconds after sync completes
        }
      }
    } catch (error) {
      console.warn('[Lists] Error accessing syncStore in getPollInterval:', error)
    }
    return 15000 // 15 seconds when idle (more frequent than before)
  }
  
  const poll = async () => {
    try {
      // Always refresh sync status to detect changes
      await syncStore.fetchLiveSyncStatus()
      
      // Refresh lists if data is stale or sync is active
      try {
        if (listsStore.isStale || syncStore.isSyncing) {
          listsStore.fetchLists(true)
        }
      } catch (error) {
        console.error('[Lists] Error checking store state in poll:', error)
      }
    } catch (error) {
      console.error('[Lists] Error in auto-refresh poll:', error)
    } finally {
      // Schedule next poll with dynamic interval
      const interval = getPollInterval()
      refreshTimeout = setTimeout(poll, interval)
    }
  }
  
  // Start polling
  poll()
}

// Force refresh when navigating to this page
onBeforeMount(async () => {
  if (process.client) {
    console.log('[Lists] Component mounting, preparing to fetch fresh data')
  }
})

// Function to open add modal with retry logic
const openAddModal = async (retryCount = 0) => {
  if (!process.client) return
  
  // Prevent duplicate calls
  if (isOpeningModal && retryCount === 0) {
    console.log('[Lists] Modal already opening, skipping duplicate call')
    return
  }
  
  if (retryCount === 0) {
    isOpeningModal = true
  }
  
  const maxRetries = 3
  const retryDelay = 150
  
  try {
    // Open modal first
    showAddModal.value = true
    
    // Wait for modal component to be mounted and rendered
    await nextTick()
    
    // Give additional time for modal to fully render
    // More time on retries to account for component mounting delays
    const waitTime = retryCount > 0 ? retryDelay * 2 : 100
    await new Promise(resolve => setTimeout(resolve, waitTime))
    
    // Verify modal is actually visible in the DOM
    // This ensures the modal component has fully rendered
    await nextTick()
    
    // Check if modal component is actually in the DOM (more reliable than checking ref)
    // Look for common modal selectors - check multiple times to be sure
    await new Promise(resolve => setTimeout(resolve, 100))
    const modalExists = 
      document.querySelector('[data-modal]') !== null || 
      document.querySelector('.modal') !== null ||
      document.querySelector('[role="dialog"]') !== null ||
      document.querySelector('.modal-overlay') !== null ||
      showAddModal.value === true
    
    // If modal didn't render and we haven't exceeded retries, try again
    if (retryCount < maxRetries && !modalExists) {
      console.log(`[Lists] Retrying modal open (attempt ${retryCount + 1}/${maxRetries})`)
      // Reset and retry
      showAddModal.value = false
      await nextTick()
      setTimeout(() => openAddModal(retryCount + 1), retryDelay)
      return
    }
    
    // Don't automatically clean URL - let it stay in the URL bar while modal is open
    // URL will be cleaned when user closes the modal manually
    
    // Clear sessionStorage flag (only on successful open, not retries)
    if (process.client && retryCount === 0 && modalExists) {
      sessionStorage.removeItem('listsync_open_add_modal')
    }
    
    // Reset guard after successful open (only if modal exists)
    if (modalExists && retryCount === 0) {
      isOpeningModal = false
    } else if (retryCount >= maxRetries) {
      // Reset guard after max retries even if modal didn't open
      isOpeningModal = false
    }
  } catch (error) {
    console.error('[Lists] Error opening add modal:', error)
    // Retry on error if we haven't exceeded max retries
    const maxRetries = 3
    const retryDelay = 150
    if (retryCount < maxRetries) {
      showAddModal.value = false
      await nextTick()
      setTimeout(() => openAddModal(retryCount + 1), retryDelay)
    } else {
      // Reset guard after max retries
      isOpeningModal = false
    }
  }
}

// Consolidated cleanup on unmount - handles all event listeners and timeouts
onUnmounted(() => {
  // Clear timeouts
  if (refreshTimeout) {
    clearTimeout(refreshTimeout)
    refreshTimeout = null
  }
  if (visibilityRefreshTimeout) {
    clearTimeout(visibilityRefreshTimeout)
    visibilityRefreshTimeout = null
  }
  
  // Stop all watchers
  runtimeWatchStops.forEach((stop) => {
    try {
      stop()
    } catch (error) {
      logDiag('Error stopping watcher', error)
    }
  })
  runtimeWatchStops.length = 0
  hasRegisteredRuntimeWatchers = false
  autoRefreshStarted = false
  
  // Clean up global error handlers
  if (process.client) {
    if (globalErrorHandler) {
      window.removeEventListener('error', globalErrorHandler)
      globalErrorHandler = null
    }
    if (globalRejectionHandler) {
      window.removeEventListener('unhandledrejection', globalRejectionHandler)
      globalRejectionHandler = null
    }
    
    // Clean up visibility change handler
    if (visibilityChangeHandler && document) {
      document.removeEventListener('visibilitychange', visibilityChangeHandler)
      visibilityChangeHandler = null
    }
    
    // Clean up storage and focus handlers
    if (storageEventHandler) {
      window.removeEventListener('storage', storageEventHandler)
      storageEventHandler = null
    }
    if (focusEventHandler) {
      window.removeEventListener('focus', focusEventHandler)
      focusEventHandler = null
    }
  }
  
  // Reset initialization state
  isInitialized = false
})

// Register runtime-only watchers after client init
const registerRuntimeWatchers = () => {
  if (!process.client || hasRegisteredRuntimeWatchers) return

  hasRegisteredRuntimeWatchers = true

  // Persist view mode changes
  const stopViewModeWatch = watch(viewMode, (newMode) => {
    try {
      localStorage.setItem('listsViewMode', newMode)
    } catch (error) {
      console.warn('[Lists] Failed to persist viewMode:', error)
    }
  })
  runtimeWatchStops.push(stopViewModeWatch)

  // Watch sync status to refresh lists and adjust polling
  const stopSyncWatch = watch(() => {
    if (!isInitialized) return false
    try {
      return syncStore.isSyncing || false
    } catch (error) {
      console.warn('[Lists] Error accessing syncStore.isSyncing in watcher:', error)
      return false
    }
  }, (isSyncing, wasSyncing) => {
    if (!isInitialized) return

    if (wasSyncing && !isSyncing) {
      console.log('[Lists] Sync completed, refreshing lists data')
      setTimeout(async () => {
        try {
          await listsStore.fetchLists(true)
          console.log('[Lists] Lists data refreshed after sync completion')
        } catch (error) {
          console.error('[Lists] Error refreshing lists after sync:', error)
        }
      }, 1500)
    } else if (isSyncing && !wasSyncing) {
      console.log('[Lists] Sync started, monitoring for completion')
    }

    setupAutoRefresh()
  }, { immediate: false })
  runtimeWatchStops.push(stopSyncWatch)
}

// Route watchers will be created inside onMounted after initialization
// This prevents TDZ errors from accessing route during setup phase

// Setup all watchers and event listeners in onMounted to avoid TDZ issues
onMounted(async () => {
  console.log('[Lists] onMounted: Starting initialization')
  
  // Attach global diagnostic hooks to capture runtime errors during init
  if (process.client) {
    globalErrorHandler = (event: ErrorEvent) => {
      console.error('[Lists] Global error captured:', event.error || event.message)
    }
    globalRejectionHandler = (event: PromiseRejectionEvent) => {
      console.error('[Lists] Unhandled rejection captured:', event.reason)
    }
    window.addEventListener('error', globalErrorHandler)
    window.addEventListener('unhandledrejection', globalRejectionHandler)
    // Cleanup is handled in the consolidated onUnmounted
  }

  if (process.client) {
    // Load view mode from localStorage (SSR-safe)
    const saved = localStorage.getItem('listsViewMode')
    if (saved === 'grid' || saved === 'list') {
      viewMode.value = saved
    }
    
    // Initialize data - stores are already initialized at module level
    console.log('[Lists] onMounted: Initializing stores...')
    
    try {
      // ALWAYS force fetch on mount to ensure fresh data when visiting the page
      console.log('[Lists] onMounted: Fetching lists...')
      await listsStore.fetchLists(true)
      console.log('[Lists] onMounted: Lists fetched successfully')
      
      // Also fetch sync status to track sync state - MUST be done before watchers access it
      console.log('[Lists] onMounted: Fetching sync status...')
      await syncStore.fetchLiveSyncStatus()
      console.log('[Lists] onMounted: Sync status fetched successfully')
      
      // Wait for component to be fully rendered
      await nextTick()
      
      // Mark as initialized - this allows watchers to start working
      console.log('[Lists] onMounted: Marking as initialized')
      isInitialized = true
    } catch (error) {
      console.error('[Lists] onMounted: Error initializing stores:', error)
      // Still mark as initialized to allow watchers to work
      isInitialized = true
    }
    
    // NOW create route watchers AFTER stores are initialized
    // This prevents TDZ errors from accessing route during setup phase
    console.log('[Lists] onMounted: Creating route watchers...')
    
    // Safety check: Ensure route and router are available
    if (!route || !router) {
      console.error('[Lists] onMounted: Route or router not available, skipping watcher creation')
    } else {
      // Watch route query changes (for navigation from other pages AND initial load)
      const stopActionWatch = watch(() => route.query.action, async (action, oldAction) => {
        if (!process.client) return
        
        if (action === 'add') {
          // Only open if it's actually changing to 'add' (not already set)
          // This prevents duplicate opens on initial load
          // Also skip if we're already opening or modal is already open
          if ((action !== oldAction || oldAction === undefined) && !isOpeningModal && !showAddModal.value) {
            console.log('[Lists] Opening add modal from route query:', action)
            // Small delay to ensure component is ready, especially after redirects
            await nextTick()
            await new Promise(resolve => setTimeout(resolve, 200))
            await openAddModal()
          }
        } else if (!action && showAddModal.value) {
          // If action is removed but modal is still open, don't close it
          // The modal will close when user clicks X or outside, and then we clean the URL
          // This prevents the modal from closing unexpectedly when URL is cleaned
          console.log('[Lists] Route query action removed but modal is still open, keeping modal open')
        }
      }, { immediate: false })
      runtimeWatchStops.push(stopActionWatch)

      // Watch for route query changes to open list details modal
      const stopDetailsWatch = watch(() => route.query, async (newQuery) => {
        if (!newQuery?.list_type || !newQuery?.list_id || !process.client) return
        
        // Wait for lists to be loaded
        if (listsStore.lists.length === 0) {
          try {
            await listsStore.fetchLists()
          } catch (error) {
            console.error('[Lists] Error fetching lists for details modal:', error)
            return
          }
        }
        
        const listType = newQuery.list_type as string
        const listId = newQuery.list_id as string
        const list = listsStore.lists.find(
          l => l.list_type === listType && l.list_id === listId
        )
        if (list) {
          console.log('[Lists] Opening list details modal from route query:', listType, listId)
          selectedList.value = list
          showDetailsModal.value = true
          // Clean up query params
          router.replace({ path: '/lists', query: {} })
        }
      }, { immediate: false })
      runtimeWatchStops.push(stopDetailsWatch)
      
      // Watch for modal close to clean URL
      const stopModalWatch = watch(() => showAddModal.value, (isOpen, previousValue) => {
        if (!process.client || !route || !router) return
        
        // Only clean URL when modal transitions from open (true) to closed (false)
        // This prevents cleaning URL when modal is already closed
        if (previousValue === true && isOpen === false && route.query.action === 'add') {
          // Clean URL when modal is closed (user clicked X or clicked outside)
          // Use nextTick to ensure modal state is fully updated
          nextTick(() => {
            router.replace({ path: '/lists', query: {} })
          })
        }
      })
      runtimeWatchStops.push(stopModalWatch)
    }

    // Register runtime watchers now that init is done
    registerRuntimeWatchers()

    // Setup automatic refresh polling (after stores are initialized)
    console.log('[Lists] onMounted: Setting up auto-refresh...')
    setupAutoRefresh()
    
    // Manually check initial route state since watchers use immediate: false
    // This handles the case where user navigates directly to /lists?action=add
    if (route?.query?.action === 'add' && !isOpeningModal && !showAddModal.value) {
      console.log('[Lists] onMounted: Opening add modal from initial route check')
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 200))
      await openAddModal()
    }
    
    // Check if we should open a specific list's details modal
    if (route.query.list_type && route.query.list_id) {
      const listType = route.query.list_type as string
      const listId = route.query.list_id as string
      const list = listsStore.lists.find(
        l => l.list_type === listType && l.list_id === listId
      )
      if (list) {
        console.log('[Lists] Opening list details modal from query params:', listType, listId)
        selectedList.value = list
        showDetailsModal.value = true
        // Clean up query params
        router.replace({ path: '/lists', query: {} })
      }
    }
    
    // Check sessionStorage for modal flag (fallback)
    const shouldOpenModal = sessionStorage.getItem('listsync_open_add_modal') === 'true'
    if (shouldOpenModal && !showAddModal.value && !isOpeningModal) {
      console.log('[Lists] Opening add modal from sessionStorage check')
      await nextTick()
      await openAddModal()
    }
    
    // Setup visibility change handler - store reference for cleanup
    visibilityChangeHandler = () => {
      if (!document) return
      if (document.visibilityState === 'visible') {
        console.log('[Lists] Page became visible, forcing refresh')
        // Clear any pending timeout
        if (visibilityRefreshTimeout) {
          clearTimeout(visibilityRefreshTimeout)
        }
        // Force refresh immediately when page becomes visible to show latest data
        visibilityRefreshTimeout = setTimeout(async () => {
          try {
            await Promise.all([
              listsStore.fetchLists(true),
              syncStore.fetchLiveSyncStatus()
            ])
          } catch (error) {
            console.error('[Lists] Error refreshing on visibility change:', error)
          }
        }, 300) // Shorter delay for better UX
      }
    }
    
    if (document) {
      document.addEventListener('visibilitychange', visibilityChangeHandler)
    }
    
    // Setup storage event listeners - store reference for cleanup
    storageEventHandler = (e: StorageEvent) => {
      if (e.key === 'listsync_open_add_modal' && e.newValue === 'true') {
        openAddModal()
      }
    }
    window.addEventListener('storage', storageEventHandler)
    
    // Check sessionStorage on focus (in case user switched tabs) - store reference for cleanup
    focusEventHandler = () => {
      if (sessionStorage.getItem('listsync_open_add_modal') === 'true') {
        openAddModal()
      }
    }
    window.addEventListener('focus', focusEventHandler)
    
    // Cleanup is handled in the consolidated onUnmounted
  }
})

// Selection handlers
const toggleSelectionMode = () => {
  selectionMode.value = !selectionMode.value
  if (!selectionMode.value) {
    selectedLists.value.clear()
  }
}

const toggleListSelection = (list: List) => {
  const key = `${list.list_type}-${list.list_id}`
  if (selectedLists.value.has(key)) {
    selectedLists.value.delete(key)
  } else {
    selectedLists.value.add(key)
  }
}

const isListSelected = (list: List) => {
  const key = `${list.list_type}-${list.list_id}`
  return selectedLists.value.has(key)
}

const deselectAll = () => {
  selectedLists.value.clear()
}

// Handlers
const handleRefresh = async () => {
  try {
    await listsStore.refresh()
    showSuccess('Lists refreshed')
  } catch (error: any) {
    showError('Failed to refresh', error.message)
  }
}

const handleSyncList = async (listType: string, listId: string) => {
  try {
    await listsStore.syncList(listType, listId)
    showSuccess('Sync Started', `Syncing ${listType} list`)
  } catch (error: any) {
    showError('Sync Failed', error.message)
  }
}

const handleDeleteList = async (listType: string, listId: string) => {
  // Check if user has "don't ask again" preference
  const dontAskAgain = process.client && localStorage.getItem('listsDeleteDontAsk') === 'true'
  
  if (!dontAskAgain) {
    // Show confirmation modal
    showDeleteModal.value = true
    deleteTarget.value = { type: listType, id: listId }
    return
  }

  // Direct delete if user chose "don't ask again"
  try {
    await listsStore.deleteList(listType, listId)
    showSuccess('List deleted')
  } catch (error: any) {
    showError('Delete Failed', error.message)
  }
}

const handleViewItems = (listType: string, listId: string) => {
  // Navigate to items page with list filter pre-selected
  // Format: listType:normalizedListId
  const filterValue = `${listType}:${listId}`
  router.push({
    path: '/items',
    query: { list: filterValue }
  })
}

const handleListAdded = () => {
  showAddModal.value = false
  listsStore.refresh()
  // Don't show success message if we're navigating to logs (it will be shown there)
  // Only show if we're staying on the lists page
  const currentPath = route.path
  if (currentPath === '/lists') {
    showSuccess('List added successfully')
  }
  // Clean URL when modal closes after adding a list
  // But only if we're still on the lists page (not navigating away)
  if (route.query.action === 'add' && currentPath === '/lists') {
    router.replace({ path: '/lists', query: {} })
  }
}

const handleListsImported = () => {
  showImportModal.value = false
  listsStore.refresh()
}

// Bulk actions
const handleBulkSync = async () => {
  showSyncProgress.value = true
  syncStatus.value = 'running'
  syncItemsProcessed.value = 0
  syncTotalItems.value = selectedLists.value.size
  syncErrors.value = []
  syncStatusMessage.value = 'Syncing selected lists...'

  let processed = 0
  for (const key of selectedLists.value) {
    const [listType, listId] = key.split('-')
    syncCurrentItem.value = listId

    try {
      await listsStore.syncList(listType, listId)
      processed++
      syncItemsProcessed.value = processed
    } catch (error: any) {
      syncErrors.value.push(`${listId}: ${error.message}`)
    }

    // Small delay between syncs
    await new Promise(resolve => setTimeout(resolve, 300))
  }

  syncStatus.value = 'completed'
  syncStatusMessage.value = `Completed: ${processed} of ${syncTotalItems.value} lists synced`
  syncCurrentItem.value = null

  // Auto-close after a delay
  setTimeout(() => {
    if (syncErrors.value.length === 0) {
      closeSyncProgress()
    }
  }, 2000)
}

const handleBulkDelete = async () => {
  const listsToDelete: Array<{ type: string; id: string }> = []
  
  for (const key of selectedLists.value) {
    const [listType, listId] = key.split('-')
    listsToDelete.push({ type: listType, id: listId })
  }

  for (const list of listsToDelete) {
    try {
      await listsStore.deleteList(list.type, list.id)
    } catch (error) {
      console.error(`Failed to delete ${list.id}:`, error)
    }
  }

  selectedLists.value.clear()
  selectionMode.value = false
}

// Sync progress handlers
const handleCancelSync = () => {
  syncStatus.value = 'cancelled'
  syncStatusMessage.value = 'Sync cancelled by user'
  closeSyncProgress()
}

// Export lists to text file
const handleExportLists = () => {
  if (!process.client) return
  
  try {
    const lists = listsStore.filteredLists
    if (lists.length === 0) {
      showError('No lists to export', 'There are no lists to export')
      return
    }

    // Build text content
    let content = 'ListSync - Lists Export\n'
    content += '='.repeat(50) + '\n'
    content += `Exported: ${new Date().toLocaleString()}\n`
    content += `Total Lists: ${lists.length}\n`
    content += '='.repeat(50) + '\n\n'

    // Group by list type
    const groupedByType = lists.reduce((acc, list) => {
      const type = list.list_type || 'unknown'
      if (!acc[type]) {
        acc[type] = []
      }
      acc[type].push(list)
      return acc
    }, {} as Record<string, typeof lists>)

    // Format each list
    Object.entries(groupedByType).forEach(([type, typeLists]) => {
      content += `\n${type.toUpperCase()} Lists (${typeLists.length})\n`
      content += '-'.repeat(50) + '\n'
      
      typeLists.forEach((list, index) => {
        content += `\n${index + 1}. ${list.display_name || list.list_id}\n`
        content += `   Type: ${list.list_type}\n`
        content += `   ID: ${list.list_id}\n`
        
        const url = list.url || list.list_url
        if (url) {
          content += `   URL: ${url}\n`
        } else {
          content += `   URL: N/A\n`
        }
        
        if (list.item_count !== undefined) {
          content += `   Items: ${list.item_count}\n`
        }
        
        if (list.last_synced) {
          const lastSynced = new Date(list.last_synced)
          content += `   Last Synced: ${lastSynced.toLocaleString()}\n`
        }
      })
    })

    // Create and download file
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `listsync-lists-export-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    showSuccess('Export Successful', `Exported ${lists.length} list(s) to text file`)
  } catch (error: any) {
    console.error('Export error:', error)
    showError('Export Failed', error.message || 'Failed to export lists')
  }
}

const closeSyncProgress = () => {
  showSyncProgress.value = false
  // Reset after animation
  setTimeout(() => {
    syncStatus.value = 'idle'
    syncCurrentItem.value = null
    syncItemsProcessed.value = 0
    syncTotalItems.value = 0
    syncStatusMessage.value = ''
    syncErrors.value = []
  }, 300)
}

// Handle delete confirmation
const handleDeleteConfirm = async (dontAskAgain: boolean) => {
  if (!deleteTarget.value) return

  if (dontAskAgain && process.client) {
    localStorage.setItem('listsDeleteDontAsk', 'true')
  }

  try {
    await listsStore.deleteList(deleteTarget.value.type, deleteTarget.value.id)
    showSuccess('List deleted')
    showDeleteModal.value = false
    deleteTarget.value = null
  } catch (error: any) {
    showError('Delete Failed', error.message)
  }
}

// Open list details
const openListDetails = (list: List) => {
  selectedList.value = list
  showDetailsModal.value = true
}
</script>

