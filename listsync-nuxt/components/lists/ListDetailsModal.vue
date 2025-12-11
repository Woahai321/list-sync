<template>
  <Modal
    v-model="isOpen"
    :title="list ? getDisplayName(list) : 'List Details'"
    size="xl"
    @close="handleClose"
  >
    <div v-if="list" class="space-y-6">
      <!-- List Info Section -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="default" class="bg-purple-500/5 border-purple-500/20">
          <div class="space-y-1">
            <p class="text-xs text-muted-foreground">Provider</p>
            <p class="text-sm font-semibold text-foreground">{{ formatProvider(list.list_type) }}</p>
          </div>
        </Card>
        <Card variant="default" class="bg-purple-500/5 border-purple-500/20">
          <div class="space-y-1">
            <p class="text-xs text-muted-foreground">Total Items</p>
            <p class="text-sm font-semibold text-foreground">{{ formatNumber(list.item_count) }}</p>
          </div>
        </Card>
        <Card variant="default" class="bg-purple-500/5 border-purple-500/20">
          <div class="space-y-1">
            <p class="text-xs text-muted-foreground">Last Synced</p>
            <p class="text-sm font-semibold text-foreground">
              <TimeAgo v-if="list.last_synced" :timestamp="list.last_synced" />
              <span v-else class="text-muted-foreground">Never</span>
            </p>
          </div>
        </Card>
      </div>

      <!-- Sync Status -->
      <div class="flex items-center gap-3 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
        <component 
          :is="getSyncStatusIcon()" 
          :size="20" 
          :class="[getSyncStatusColor(), { 'animate-spin': isSyncingList || syncStore.isSyncing }]" 
        />
        <div class="flex-1">
          <p class="text-sm font-semibold text-foreground">{{ getSyncStatusText() }}</p>
          <p v-if="nextSyncCountdown" class="text-xs text-muted-foreground">
            Next sync: {{ nextSyncCountdown }}
          </p>
        </div>
      </div>

      <!-- List URL -->
      <div v-if="list.url || list.list_url" class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          :icon="ExternalLinkIcon"
          @click="openUrl"
        >
          View Source
        </Button>
        <Button
          variant="ghost"
          size="sm"
          :icon="CopyIcon"
          @click="copyUrl"
        >
          Copy URL
        </Button>
      </div>

      <!-- Items Preview -->
      <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-foreground titillium-web-semibold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
                Items Preview
              </h3>
              <p class="text-xs text-muted-foreground mt-1">
                Showing {{ itemsData.items.length }} of {{ formatNumber(itemsData.total) }} items
              </p>
            </div>
            <Button
              v-if="itemsData.total > itemsData.items.length"
              variant="primary"
              size="sm"
              :icon="ExternalLinkIcon"
              @click="handleViewAllItems"
            >
              View All Items
            </Button>
          </div>

          <!-- Loading State -->
          <div v-if="loadingItems" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <PosterCardSkeleton v-for="i in 10" :key="`skeleton-${i}`" />
          </div>

          <!-- Items Grid -->
          <div v-else-if="itemsData.items.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <PosterCard
              v-for="item in itemsData.items"
              :key="item.id"
              :item="formatItemForPosterCard(item)"
              simple
            />
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-12">
            <p class="text-muted-foreground">No items found in this list</p>
          </div>
        </div>
      </Card>
    </div>

    <template #footer>
      <div class="flex items-center justify-between">
        <Button
          variant="ghost"
          :icon="TrashIcon"
          @click="handleDelete"
        >
          Delete List
        </Button>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            @click="handleClose"
          >
            Close
          </Button>
          <Button
            variant="primary"
            :icon="RefreshCwIcon"
            :loading="isSyncingList || syncStore.isSyncing"
            :disabled="syncStore.isSyncing"
            @click="handleSync"
          >
            {{ syncStore.isSyncing ? 'Syncing...' : 'Sync Now' }}
          </Button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshCwIcon,
  Trash2 as TrashIcon,
  ExternalLink as ExternalLinkIcon,
  Copy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Clock as ClockIcon,
  AlertCircle as AlertCircleIcon,
} from 'lucide-vue-next'
import type { List, EnrichedMediaItem } from '~/types'

interface Props {
  modelValue: boolean
  list: List | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'sync': [listType: string, listId: string]
  'delete': [listType: string, listId: string]
  'view-items': [listType: string, listId: string]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const { showSuccess, showError } = useToast()
const syncStore = useSyncStore()
const api = useApiService()

// State
const loadingItems = ref(false)
const itemsData = ref<{
  items: any[]
  total: number
  limit: number
  has_more: boolean
}>({
  items: [],
  total: 0,
  limit: 20,
  has_more: false
})

// No need for local isSyncing - use computed from store

// Watch for list changes to fetch items
watch(() => props.list, async (newList) => {
  if (newList && isOpen.value) {
    await fetchItems()
  }
}, { immediate: true })

watch(() => isOpen.value, async (open) => {
  if (open && props.list) {
    await fetchItems()
  }
})

// Fetch items from list
const fetchItems = async () => {
  if (!props.list) return
  
  loadingItems.value = true
  try {
    const response = await api.getListItems(props.list.list_type, props.list.list_id, 10)
    itemsData.value = response
  } catch (error: any) {
    console.error('Error fetching list items:', error)
    showError('Failed to load items', error.message)
  } finally {
    loadingItems.value = false
  }
}

// Format item for PosterCard
const formatItemForPosterCard = (item: any): EnrichedMediaItem => {
  // Construct overseerr_url if we have overseerr_id
  let overseerr_url = item.overseerr_url || null
  if (!overseerr_url && item.overseerr_id) {
    // Try to get overseerr base URL from system store
    const systemStore = useSystemStore()
    const overseerrBaseUrl = systemStore.health?.overseerr_url
    if (overseerrBaseUrl) {
      const mediaTypePath = (item.media_type || 'movie') === 'tv' ? 'tv' : 'movie'
      overseerr_url = `${overseerrBaseUrl.replace(/\/$/, '')}/${mediaTypePath}/${item.overseerr_id}`
    }
  }

  return {
    id: item.id,
    title: item.title,
    media_type: item.media_type || 'movie',
    year: item.year,
    imdb_id: item.imdb_id,
    tmdb_id: item.tmdb_id,
    overseerr_id: item.overseerr_id,
    status: item.status || 'pending',
    last_synced: item.last_synced,
    poster_url: item.poster_url || null,
    rating: null,
    overview: null,
    genres: [],
    overseerr_url: overseerr_url,
  }
}

// Sync status helpers
const isSyncingList = computed(() => {
  if (!props.list || !syncStore.isSyncing || !syncStore.liveSyncStatus) return false
  // Check if this list matches the current sync
  return syncStore.liveSyncStatus.list_type === props.list.list_type &&
         syncStore.liveSyncStatus.list_id === props.list.list_id
})

const getSyncStatusIcon = () => {
  if (isSyncingList.value || syncStore.isSyncing) return RefreshCwIcon
  if (props.list?.last_synced) return CheckCircleIcon
  return AlertCircleIcon
}

const getSyncStatusColor = () => {
  if (isSyncingList.value || syncStore.isSyncing) return 'text-purple-400'
  if (props.list?.last_synced) return 'text-green-400'
  return 'text-yellow-400'
}

const getSyncStatusText = () => {
  if (isSyncingList.value) return 'Syncing...'
  if (syncStore.isSyncing) return 'Sync in progress (other lists)'
  if (props.list?.last_synced) return 'Last synced successfully'
  return 'Never synced'
}

const nextSyncCountdown = computed(() => {
  // Get next sync from system store if available
  const systemStore = useSystemStore()
  if (systemStore.health?.next_sync) {
    const next = new Date(systemStore.health.next_sync)
    const now = new Date()
    const diff = next.getTime() - now.getTime()
    if (diff > 0) {
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      if (hours > 0) return `${hours}h ${minutes}m`
      return `${minutes}m`
    }
  }
  return null
})

// Handlers
const handleClose = () => {
  emit('update:modelValue', false)
}

const handleSync = async () => {
  if (!props.list) return
  try {
    emit('sync', props.list.list_type, props.list.list_id)
    showSuccess('Sync Started', `Syncing ${props.list.list_type} list`)
    // Refresh items after a delay
    setTimeout(() => {
      fetchItems()
    }, 2000)
  } catch (error: any) {
    showError('Sync Failed', error.message)
  }
}

const handleDelete = () => {
  if (!props.list) return
  emit('delete', props.list.list_type, props.list.list_id)
  handleClose()
}

const openUrl = () => {
  const url = props.list?.url || props.list?.list_url
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

const copyUrl = async () => {
  const url = props.list?.url || props.list?.list_url
  if (!url) return

  try {
    await navigator.clipboard.writeText(url)
    showSuccess('URL copied to clipboard')
  } catch (error) {
    showError('Failed to copy URL')
  }
}

const handleViewAllItems = () => {
  if (!props.list) return
  emit('view-items', props.list.list_type, props.list.list_id)
}

const getDisplayName = (list: List) => {
  return list.display_name || list.list_id
}

const formatProvider = (type: string) => {
  const providers: Record<string, string> = {
    imdb: 'IMDb',
    trakt: 'Trakt',
    trakt_special: 'Trakt Special',
    letterboxd: 'Letterboxd',
    mdblist: 'MDBList',
    stevenlu: 'Steven Lu',
    tmdb: 'TMDB',
    simkl: 'Simkl',
    tvdb: 'TVDB',
    anilist: 'AniList',
  }
  return providers[type.toLowerCase()] || type
}
</script>

