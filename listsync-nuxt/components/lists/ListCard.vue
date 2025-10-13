<template>
  <Card 
    variant="hover" 
    class="relative overflow-hidden group/card" 
    :class="{ 
      'ring-2 ring-purple-500 shadow-xl shadow-purple-500/30': isSelected,
      'hover:shadow-xl hover:shadow-purple-500/20': !isSelected 
    }"
  >
    <!-- Subtle gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-accent/5 opacity-0 group-hover/card:opacity-100 transition-opacity duration-300" />
    
    <!-- Selection Checkbox -->
    <div v-if="selectable" class="absolute top-4 left-4 z-10">
      <input
        type="checkbox"
        :checked="isSelected"
        class="w-6 h-6 rounded-lg border-2 border-purple-500/40 bg-black/40 text-purple-500 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-black cursor-pointer transition-all hover:scale-110"
        @change="$emit('toggle-select')"
      />
    </div>

    <!-- Source Badge -->
    <div class="absolute top-4 right-4 z-10">
      <Badge :variant="getSourceBadgeVariant(list.list_type)" size="md" class="shadow-lg">
        <component :is="getSourceIcon(list.list_type)" :size="14" />
        {{ formatListSource(list.list_type) }}
      </Badge>
    </div>

    <!-- Content -->
    <div class="space-y-4 relative">
      <!-- Header -->
      <div class="pr-20">
        <Tooltip :content="getFullListName()">
          <h3 class="text-lg font-bold text-foreground line-clamp-2 titillium-web-bold group-hover/card:text-purple-300 transition-colors leading-tight">
            {{ getDisplayTitle() }}
          </h3>
        </Tooltip>
        <p class="text-xs text-muted-foreground mt-2 opacity-70">
          {{ getListSubtitle() }}
        </p>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex items-center gap-3 group/stat">
          <div class="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/stat:from-purple-500/30 group-hover/stat:to-purple-600/30 transition-all duration-300">
            <component :is="LayersIcon" :size="18" class="text-purple-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
          <div>
            <p class="text-xs text-muted-foreground mb-0.5">Items</p>
            <p class="text-base font-bold text-foreground tabular-nums">
              {{ formatNumber(list.item_count) }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3 group/stat">
          <div class="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-600/20 group-hover/stat:from-blue-500/30 group-hover/stat:to-cyan-600/30 transition-all duration-300">
            <component :is="ClockIcon" :size="18" class="text-blue-400 group-hover/stat:scale-110 transition-transform duration-300" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs text-muted-foreground mb-0.5">Last Synced</p>
            <Tooltip v-if="list.last_synced" :content="formatDate(list.last_synced, 'PPpp')">
              <p class="text-base font-bold text-foreground truncate tabular-nums">
                <TimeAgo :timestamp="list.last_synced" />
              </p>
            </Tooltip>
            <p v-else class="text-base font-bold text-muted-foreground">
              Never
            </p>
          </div>
        </div>
      </div>

      <!-- Quick Actions Bar -->
      <div class="flex items-center gap-2">
        <button
          v-if="list.url || list.list_url"
          type="button"
          class="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-black/30 hover:bg-purple-500/20 border border-purple-500/10 hover:border-purple-500/30 transition-all group/url"
          @click="openUrl"
        >
          <component :is="ExternalLinkIcon" :size="14" class="text-muted-foreground group-hover/url:text-purple-400 transition-colors" />
          <span class="text-xs font-medium text-muted-foreground group-hover/url:text-purple-400 transition-colors">View Source</span>
        </button>
        
        <button
          v-if="list.url || list.list_url"
          type="button"
          class="p-2 rounded-lg bg-black/30 hover:bg-purple-500/20 border border-purple-500/10 hover:border-purple-500/30 transition-all group/copy"
          :title="'Copy URL'"
          @click="copyUrl"
        >
          <component :is="CopyIcon" :size="14" class="text-muted-foreground group-hover/copy:text-purple-400 transition-colors" />
        </button>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-3 border-t border-purple-500/10">
        <Button
          variant="primary"
          size="sm"
          :icon="RefreshCwIcon"
          :loading="isSyncing"
          class="flex-1"
          @click="handleSync"
        >
          Sync Now
        </Button>

        <Button
          variant="ghost"
          size="sm"
          :icon="TrashIcon"
          @click="handleDelete"
        >
          Delete
        </Button>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Layers as LayersIcon,
  Clock as ClockIcon,
  RefreshCw as RefreshCwIcon,
  ExternalLink as ExternalLinkIcon,
  Trash2 as TrashIcon,
  Link as LinkIcon,
  Copy as CopyIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  Database as DatabaseIcon,
} from 'lucide-vue-next'
import type { List } from '~/types'

interface Props {
  list: List
  selectable?: boolean
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectable: false,
  isSelected: false,
})

const emit = defineEmits<{
  sync: []
  delete: []
  'toggle-select': []
}>()

const { showSuccess, showError } = useToast()

// State
const isSyncing = ref(false)

// Get source icon
const getSourceIcon = (source: string) => {
  const sourceMap: Record<string, any> = {
    imdb: FilmIcon,
    trakt: TvIcon,
    trakt_special: TvIcon,
    letterboxd: FilmIcon,
    mdblist: DatabaseIcon,
    stevenlu: DatabaseIcon,
  }
  
  return sourceMap[source.toLowerCase()] || DatabaseIcon
}

// Get source badge variant
const getSourceBadgeVariant = (source: string): 'primary' | 'success' | 'info' => {
  const variantMap: Record<string, 'primary' | 'success' | 'info'> = {
    imdb: 'primary',
    trakt: 'info',
    trakt_special: 'info',
    letterboxd: 'success',
    mdblist: 'primary',
    stevenlu: 'info',
  }
  
  return variantMap[source.toLowerCase()] || 'primary'
}

// Handlers
const handleSync = async () => {
  isSyncing.value = true
  try {
    emit('sync')
    // Keep button in loading state for a moment
    await new Promise(resolve => setTimeout(resolve, 1000))
  } finally {
    isSyncing.value = false
  }
}

const handleDelete = () => {
  emit('delete')
}

const openUrl = () => {
  const url = props.list.url || props.list.list_url
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

const copyUrl = async () => {
  const url = props.list.url || props.list.list_url
  if (!url) return

  try {
    await navigator.clipboard.writeText(url)
    showSuccess('URL copied to clipboard')
  } catch (error) {
    showError('Failed to copy URL')
  }
}

// Helper functions for clean display
const getDisplayTitle = () => {
  const source = props.list.list_type?.toLowerCase()
  
  // For Trakt Special, format the title nicely
  if (source === 'trakt_special' && props.list.list_id) {
    const parts = props.list.list_id.split(':')
    if (parts.length === 2) {
      const [category, mediaType] = parts
      const catFormatted = category.charAt(0).toUpperCase() + category.slice(1)
      const mediaFormatted = mediaType === 'movies' ? 'Movies' : 'TV Shows'
      return `${catFormatted} ${mediaFormatted}`
    }
  }
  
  // For IMDb, show a clean name
  if (source === 'imdb') {
    const imdbCharts: Record<string, string> = {
      'top': 'Top 250 Movies',
      'boxoffice': 'Box Office',
      'moviemeter': 'MovieMeter (Popular Movies)',
      'tvmeter': 'TVMeter (Popular TV)',
    }
    return imdbCharts[props.list.list_id.toLowerCase()] || (props.list.display_name || props.list.list_id)
  }
  
  // For other sources, use display_name or fallback
  return props.list.display_name || props.list.list_id
}

const getListSubtitle = () => {
  const source = props.list.list_type?.toLowerCase()
  
  // For Trakt Special, show the source
  if (source === 'trakt_special') {
    return 'Trakt Special List'
  }
  
  // For IMDb charts, show "IMDb Chart"
  const imdbCharts = ['top', 'boxoffice', 'moviemeter', 'tvmeter']
  if (source === 'imdb' && imdbCharts.includes(props.list.list_id.toLowerCase())) {
    return 'IMDb Chart'
  }
  
  // For regular lists, show the list ID
  return `ID: ${props.list.list_id}`
}

const getFullListName = () => {
  return `${getDisplayTitle()} (${props.list.list_id})`
}
</script>

