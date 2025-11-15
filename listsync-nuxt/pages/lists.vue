<template>
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

    <!-- Loading State -->
    <div v-if="listsStore.loading && listsStore.lists.length === 0" class="flex items-center justify-center py-12 sm:py-20 px-4">
      <LoadingSpinner size="lg" text="Loading lists..." />
    </div>

    <!-- Lists Grid -->
    <template v-else>
      <!-- Stats Bar -->
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

      <!-- Lists Grid -->
      <ListsGrid
        v-if="listsStore.filteredLists.length > 0"
        :lists="listsStore.filteredLists"
        :selectable="selectionMode"
        :selected-lists="selectedLists"
        @sync-list="handleSyncList"
        @delete-list="handleDeleteList"
        @toggle-select="toggleListSelection"
      />

      <!-- Empty State -->
      <EmptyState
        v-else-if="!listsStore.loading"
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
</template>

<script setup lang="ts">
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
} from 'lucide-vue-next'
import type { List } from '~/types'

const listsStore = useListsStore()
const { showSuccess, showError } = useToast()

// Real-time features - use sync store instead of SSE (polling-based)
const syncStore = useSyncStore()

// Set page title
useHead({
  title: 'Manage Lists - ListSync',
})

// State
const showAddModal = ref(false)
const showImportModal = ref(false)
const selectionMode = ref(false)
const selectedLists = ref<Set<string>>(new Set())

// Sync Progress State
const showSyncProgress = ref(false)
const syncStatus = ref('idle')
const syncCurrentItem = ref<string | null>(null)
const syncItemsProcessed = ref(0)
const syncTotalItems = ref(0)
const syncStatusMessage = ref('')
const syncErrors = ref<string[]>([])

// Watch for sync status changes (polling-based updates)
watch(() => syncStore.isSyncing, (isSyncing, wasSyncing) => {
  // Refresh lists when sync completes (was running, now stopped)
  if (wasSyncing && !isSyncing) {
    // Sync just completed - refresh lists to get updated last_synced times
    listsStore.fetchLists()
  }
}, { immediate: false })

// Fetch lists on mount and check for action query param
const route = useRoute()
const router = useRouter()

// Guard to prevent duplicate modal opens
let isOpeningModal = false

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

// Watch route query changes (for navigation from other pages AND initial load)
watch(() => route.query.action, async (action, oldAction) => {
  if (action === 'add' && process.client) {
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
}, { immediate: true })

// Also watch the full route to catch direct navigation (but only if query watcher didn't fire)
// This is a fallback for edge cases
watch(() => route.fullPath, async (fullPath, oldFullPath) => {
  if (process.client && fullPath.includes('action=add')) {
    // Only proceed if query watcher didn't already handle it
    // Skip if modal is already opening or open
    if ((!oldFullPath || (oldFullPath && !oldFullPath.includes('action=add'))) && 
        !isOpeningModal && !showAddModal.value && route.query.action === 'add') {
      console.log('[Lists] Opening add modal from route change (fallback):', fullPath)
      // Small delay to ensure component is ready on initial load
      if (!oldFullPath) {
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 300))
      }
      await openAddModal()
    }
  }
}, { immediate: true })

onMounted(async () => {
  if (process.client) {
    try {
      await listsStore.fetchLists()
      
      // Wait for component to be fully rendered
      await nextTick()
      
      // Check multiple sources for the "open add modal" flag
      // This is a fallback in case watchers don't fire
      const shouldOpenModal = 
        route.query.action === 'add' || 
        sessionStorage.getItem('listsync_open_add_modal') === 'true'
      
      if (shouldOpenModal && !showAddModal.value) {
        console.log('[Lists] Opening add modal from onMounted check')
        // Use retry-enabled function to open modal
        await openAddModal()
      }
    } catch (error) {
      console.error('Error loading lists:', error)
    }
  }
})

// Also watch for sessionStorage flag (fallback for edge cases)
if (process.client) {
  // Listen for storage events (when tab changes, etc.)
  window.addEventListener('storage', (e) => {
    if (e.key === 'listsync_open_add_modal' && e.newValue === 'true') {
      openAddModal()
    }
  })
  
  // Check sessionStorage on focus (in case user switched tabs)
  window.addEventListener('focus', () => {
    if (sessionStorage.getItem('listsync_open_add_modal') === 'true') {
      openAddModal()
    }
  })
}

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
  // Show confirmation
  if (!confirm('Are you sure you want to delete this list?')) return

  try {
    await listsStore.deleteList(listType, listId)
    showSuccess('List deleted')
  } catch (error: any) {
    showError('Delete Failed', error.message)
  }
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

// Watch for modal close to clean URL
watch(() => showAddModal.value, (isOpen, previousValue) => {
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
</script>

