<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Lists
        </h1>
        <p class="text-muted-foreground mt-1">
          Manage your watchlists from IMDb, Trakt, Letterboxd, AniList, TMDB, Simkl, and more
        </p>
      </div>

      <div class="flex items-center gap-3">
        <Button
          variant="ghost"
          :icon="selectionMode ? XIcon : CheckSquareIcon"
          @click="toggleSelectionMode"
        >
          {{ selectionMode ? 'Cancel' : 'Select' }}
        </Button>

        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="listsStore.loading"
          @click="handleRefresh"
        >
          Refresh
        </Button>

        <Button
          variant="primary"
          :icon="PlusIcon"
          @click="showAddModal = true"
        >
          Add List
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <ListFilters />

    <!-- Loading State -->
    <div v-if="listsStore.loading && listsStore.lists.length === 0" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading lists..." />
    </div>

    <!-- Lists Grid -->
    <template v-else>
      <!-- Stats Bar -->
      <div v-if="listsStore.lists.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="hover" class="group/stat cursor-default">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm text-muted-foreground mb-1">Total Lists</p>
              <p class="text-3xl font-bold text-foreground tabular-nums">
                <AnimatedCounter :value="listsStore.totalLists" />
              </p>
            </div>
            <div class="p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/stat:from-purple-500/30 group-hover/stat:to-purple-600/30 transition-all duration-300">
              <component :is="ListIcon" :size="28" class="text-purple-400 group-hover/stat:scale-110 transition-transform duration-300" />
            </div>
          </div>
        </Card>

        <Card variant="hover" class="group/stat cursor-default">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm text-muted-foreground mb-1">Total Items</p>
              <p class="text-3xl font-bold text-foreground tabular-nums">
                <AnimatedCounter :value="listsStore.totalItems" />
              </p>
            </div>
            <div class="p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-600/20 group-hover/stat:from-blue-500/30 group-hover/stat:to-cyan-600/30 transition-all duration-300">
              <component :is="LayersIcon" :size="28" class="text-blue-400 group-hover/stat:scale-110 transition-transform duration-300" />
            </div>
          </div>
        </Card>

        <Card variant="hover" class="group/stat cursor-default">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <p class="text-sm text-muted-foreground mb-1">Active Filters</p>
              <p class="text-3xl font-bold text-foreground tabular-nums">
                {{ listsStore.hasActiveFilters ? listsStore.activeFilterCount || 1 : 0 }}
              </p>
            </div>
            <div :class="[
              'p-4 rounded-xl transition-all duration-300',
              listsStore.hasActiveFilters 
                ? 'bg-gradient-to-br from-green-500/20 to-emerald-600/20 group-hover/stat:from-green-500/30 group-hover/stat:to-emerald-600/30'
                : 'bg-gradient-to-br from-gray-500/20 to-gray-600/20 group-hover/stat:from-gray-500/30 group-hover/stat:to-gray-600/30'
            ]">
              <component :is="FilterIcon" :size="28" :class="[
                'transition-transform duration-300 group-hover/stat:scale-110',
                listsStore.hasActiveFilters ? 'text-green-400' : 'text-gray-400'
              ]" />
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
} from 'lucide-vue-next'
import type { List } from '~/types'

const listsStore = useListsStore()
const { showSuccess, showError } = useToast()

// Real-time features
const { isConnected: sseConnected, lastEvent } = useSyncMonitor()

// Set page title
useHead({
  title: 'Manage Lists - ListSync',
})

// State
const showAddModal = ref(false)
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

// Watch for SSE events (real-time updates)
watch(lastEvent, (event) => {
  if (!event) return

  // Refresh lists when sync events occur
  if (event.type === 'status' || event.type === 'progress') {
    // Update last synced times and sync progress
    if (event.data.list_id) {
      // Find and update specific list
      const list = listsStore.lists.find(
        l => l.list_id === event.data.list_id && l.list_type === event.data.list_type
      )
      if (list && event.data.last_synced) {
        list.last_synced = event.data.last_synced
      }
    }
    
    // Refresh all lists if sync completed
    if (event.type === 'status' && event.data.status === 'completed') {
      listsStore.fetchLists()
    }
  }
})

// Fetch lists on mount
onMounted(async () => {
  if (process.client) {
    try {
      await listsStore.fetchLists()
      
      // Check if URL has ?action=add to auto-open add modal
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.get('action') === 'add') {
        showAddModal.value = true
        // Clean URL without triggering navigation
        window.history.replaceState({}, '', '/lists')
      }
    } catch (error) {
      console.error('Error loading lists:', error)
    }
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
  showSuccess('List added successfully')
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

