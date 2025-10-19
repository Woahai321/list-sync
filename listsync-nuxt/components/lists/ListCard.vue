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
      <div :class="[
        'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium shadow-lg transition-all duration-300',
        getSourceColor(list.list_type).bgColor,
        getSourceColor(list.list_type).borderColor,
        'border'
      ]">
        <component :is="getSourceIcon(list.list_type)" :size="14" :class="getSourceColor(list.list_type).color" />
        <span :class="getSourceColor(list.list_type).color">{{ formatListSource(list.list_type) }}</span>
      </div>
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
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  BookOpen as BookOpenIcon,
  Globe as GlobeIcon,
  Zap as ZapIcon,
  Heart as HeartIcon,
  Calendar as CalendarIcon,
  Monitor as MonitorIcon,
} from 'lucide-vue-next'
import type { List } from '~/types'
import { extractUrlSegment } from '~/utils/urlHelpers'

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

// Source definitions with colors and icons (matching AddListModal)
const sources = [
  { 
    label: 'IMDb', 
    value: 'imdb', 
    icon: StarIcon, 
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/40',
    description: 'Internet Movie Database'
  },
  { 
    label: 'Trakt', 
    value: 'trakt', 
    icon: TrendingUpIcon, 
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/40',
    description: 'Track your movies & TV'
  },
  { 
    label: 'Trakt Special', 
    value: 'trakt_special', 
    icon: ZapIcon, 
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/40',
    description: 'Curated Trakt lists'
  },
  { 
    label: 'Letterboxd', 
    value: 'letterboxd', 
    icon: BookOpenIcon, 
    color: 'text-pink-400',
    bgColor: 'bg-pink-500/20',
    borderColor: 'border-pink-500/40',
    description: 'Social film discovery'
  },
  { 
    label: 'MDBList', 
    value: 'mdblist', 
    icon: DatabaseIcon, 
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/40',
    description: 'Movie database lists'
  },
  { 
    label: 'Steven Lu', 
    value: 'stevenlu', 
    icon: HeartIcon, 
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500/40',
    description: 'Curated movie collection'
  },
  { 
    label: 'TMDB', 
    value: 'tmdb', 
    icon: GlobeIcon, 
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
    borderColor: 'border-cyan-500/40',
    description: 'The Movie Database'
  },
  { 
    label: 'Simkl', 
    value: 'simkl', 
    icon: MonitorIcon, 
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/40',
    description: 'Track movies & shows'
  },
  { 
    label: 'TVDB', 
    value: 'tvdb', 
    icon: CalendarIcon, 
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/20',
    borderColor: 'border-indigo-500/40',
    description: 'TV series database'
  },
]

// Get source icon
const getSourceIcon = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.icon || DatabaseIcon
}

// Get source color info
const getSourceColor = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return {
    color: sourceData?.color || 'text-gray-400',
    bgColor: sourceData?.bgColor || 'bg-gray-500/20',
    borderColor: sourceData?.borderColor || 'border-gray-500/40'
  }
}

// Format list source for display
const formatListSource = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.label || source
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
    return imdbCharts[props.list.list_id.toLowerCase()] || (props.list.display_name || extractUrlSegment(props.list.list_id))
  }
  
  // For Steven Lu, show clean name
  if (source === 'stevenlu') {
    return "Steven Lu's Movie Collection"
  }
  
  // Extract meaningful name from URL based on source
  const listId = props.list.list_id
  
  if (source === 'trakt' && listId.includes('/lists/')) {
    // Extract list name from Trakt URL: /users/{user}/lists/{name}
    const match = listId.match(/\/lists\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  if (source === 'letterboxd' && listId.includes('/list/')) {
    // Extract list name from Letterboxd URL: /{user}/list/{name}/
    const match = listId.match(/\/list\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  if (source === 'mdblist' && listId.includes('/lists/')) {
    // Extract list name from MDBList URL: /lists/{user}/{name}
    const match = listId.match(/\/lists\/[^\/]+\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  if (source === 'tmdb' && listId.includes('/list/')) {
    // Extract list name from TMDB URL: /list/{id-name}
    const match = listId.match(/\/list\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  if (source === 'simkl' && listId.includes('/list/')) {
    // Extract list name from Simkl URL: /{id}/list/{id}/{name}
    const match = listId.match(/\/list\/[^\/]+\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  if (source === 'tvdb' && listId.includes('/lists/')) {
    // Extract list name from TVDB URL: /lists/{idorname}
    const match = listId.match(/\/lists\/([^\/]+)\/?$/)
    if (match) {
      return match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }
  
  // Use display_name if it doesn't look like a URL and is meaningful
  if (props.list.display_name && !props.list.display_name.includes('://')) {
    return props.list.display_name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  
  // Fallback to clean ID extraction
  const cleanId = extractUrlSegment(listId)
  return cleanId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
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
  
  // Show URL if available, otherwise show clean ID
  const url = props.list.url || props.list.list_url
  if (url) {
    return url
  }
  
  // Fallback to clean ID
  return `ID: ${extractUrlSegment(props.list.list_id)}`
}


const getFullListName = () => {
  return `${getDisplayTitle()} (${extractUrlSegment(props.list.list_id)})`
}
</script>

