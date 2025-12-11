<template>
  <div
    class="poster-card group relative transition-all duration-300 ease-out animate-fade-in"
    :class="{ 
      'animate-pulse': isLoading,
      'simple-mode': simple
    }"
    role="button"
    :aria-label="`View ${item.title} in Overseerr`"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <!-- Poster Image Container -->
    <div ref="imageRef" class="poster-container relative w-full rounded-xl overflow-hidden shadow-xl">
      <!-- Aspect ratio keeper (2:3 for movie posters) -->
      <div class="aspect-[2/3] relative bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900">
        <!-- Blur Placeholder (shown while loading) -->
        <div 
          v-if="actualSrc && !imageLoaded && !imageError"
          class="absolute inset-0 bg-gradient-to-br from-purple-900/40 to-gray-900/60 animate-pulse"
        >
          <div class="absolute inset-0 backdrop-blur-xl bg-purple-500/5"></div>
        </div>
        
        <!-- Poster Image -->
        <img
          v-if="actualSrc && !imageError"
          :src="actualSrc"
          :alt="`${item.title} poster`"
          class="absolute inset-0 w-full h-full object-cover transition-all duration-500 ease-out"
          :class="{ 
            'opacity-0 scale-105': !imageLoaded,
            'opacity-100 scale-100': imageLoaded
          }"
          @load="handleLoad"
          @error="handleError"
        />
        
        <!-- Fallback Placeholder (no poster URL or error) -->
        <div
          v-if="!actualSrc || imageError"
          class="absolute inset-0 w-full h-full bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900 flex items-center justify-center"
        >
          <FilmIcon v-if="item.media_type === 'movie'" :size="48" class="text-purple-500/30" />
          <TvIcon v-else :size="48" class="text-purple-500/30" />
        </div>

        <!-- Status Icon Badge (Top Right) -->
        <div
          class="absolute top-2 right-2 w-6 h-6 rounded-md backdrop-blur-md shadow-md flex items-center justify-center"
          :class="getStatusIconClass(item.status)"
          :title="getStatusLabel(item.status)"
        >
          <component :is="getStatusIcon(item.status)" :size="12" class="drop-shadow-md" />
        </div>

        <!-- Media Type Badge (Top Left) -->
        <div class="absolute top-2 left-2 w-6 h-6 rounded-md bg-purple-600/80 backdrop-blur-md shadow-md flex items-center justify-center">
          <FilmIcon v-if="item.media_type === 'movie'" :size="12" class="text-white" />
          <TvIcon v-else :size="12" class="text-white" />
        </div>

        <!-- Simple Mode: Just poster, no overlays -->
        <template v-if="simple">
          <!-- Subtle gradient at bottom for status badge visibility -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent pointer-events-none" />
        </template>

        <!-- Full Mode: Title, Year, List Tags, and Hover Overlay -->
        <template v-else>
          <!-- Always Visible: Gradient Overlay for Title -->
          <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent pointer-events-none" />

          <!-- Always Visible: Title and Year -->
          <div class="absolute inset-x-0 bottom-0 p-3 pointer-events-none">
            <h3 class="text-white font-bold text-sm leading-tight line-clamp-2 drop-shadow-lg mb-0.5">
              {{ item.title }}
            </h3>
            <p class="text-purple-300 text-xs font-medium">
              {{ item.year || 'N/A' }}
            </p>
          </div>

          <!-- Hover Overlay: Metadata and Button -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/95 via-purple-950/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4 pointer-events-none group-hover:pointer-events-auto">
            <!-- Title and Year (duplicate for hover state) -->
            <h3 class="text-white font-bold text-base leading-tight mb-0.5">
              {{ item.title }}
            </h3>
            <p class="text-purple-300 text-sm font-medium mb-2">
              {{ item.year || 'N/A' }}
            </p>

            <!-- Overview -->
            <p v-if="item.overview" class="text-white/90 text-xs leading-relaxed line-clamp-2 mb-2">
              {{ item.overview }}
            </p>

            <!-- List Source Tags (In Hover Overlay - Only visible on hover) -->
            <div v-if="item.list_sources && item.list_sources.length > 0" class="flex flex-wrap gap-1.5 mb-3">
              <button
                v-for="(source, index) in item.list_sources.slice(0, 3)"
                :key="`${source.list_type}-${source.list_id}`"
                @click.stop="handleListTagClick(source)"
                class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold bg-purple-500/90 hover:bg-purple-400/95 text-white border border-purple-400/60 hover:border-purple-300/80 backdrop-blur-md shadow-sm transition-all cursor-pointer"
                :title="`View ${source.display_name || getListLabel(source)} list`"
              >
                <component :is="ListIcon" :size="10" />
                <span class="truncate max-w-[80px]">{{ getListLabel(source) }}</span>
              </button>
              <span
                v-if="item.list_sources.length > 3"
                class="inline-flex items-center px-2 py-1 rounded-md text-[10px] font-semibold bg-purple-500/70 text-white border border-purple-400/50 backdrop-blur-md shadow-sm"
                :title="item.list_sources.slice(3).map(s => s.display_name || s.list_id).join(', ')"
              >
                +{{ item.list_sources.length - 3 }}
              </span>
            </div>

            <!-- View in Overseerr Button (Slimmer) -->
            <button
              v-if="item.overseerr_url"
              class="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-medium text-xs py-1.5 px-2 rounded-md flex items-center justify-center gap-1.5 transition-all duration-200 shadow-sm"
              @click.stop="handleClick"
            >
              <ExternalLinkIcon :size="12" />
              <span>View in Overseerr</span>
            </button>
            <div
              v-else
              class="w-full bg-gray-700/60 text-gray-400 font-medium text-xs py-1.5 px-2 rounded-md text-center"
            >
              Not available
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Hover Effect: Purple Glow (Subtle) - Only in full mode -->
    <div v-if="!simple" class="absolute -inset-0.5 bg-gradient-to-r from-purple-600/40 via-purple-500/40 to-purple-600/40 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-md" />
  </div>
</template>

<script setup lang="ts">
import { 
  Film as FilmIcon, 
  Tv as TvIcon, 
  ExternalLink as ExternalLinkIcon,
  CheckCircle2 as CheckIcon,
  Clock as ClockIcon,
  XCircle as XIcon,
  AlertCircle as AlertIcon,
  MinusCircle as SkipIcon,
  List as ListIcon
} from 'lucide-vue-next'
import type { EnrichedMediaItem } from '~/types'
import { constructListUrl } from '~/utils/urlHelpers'

interface Props {
  item: EnrichedMediaItem
  isLoading?: boolean
  simple?: boolean // Simple mode: no hover overlay, just poster
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  simple: false
})

const { showError } = useToast()

// Use smart lazy loading composable
const { imageRef, actualSrc, imageLoaded, imageError, handleLoad, handleError } = useLazyImage(
  computed(() => props.item.poster_url)
)

// Get status icon component
const getStatusIcon = (status: string) => {
  const icons: Record<string, any> = {
    'already_available': CheckIcon,
    'requested': ClockIcon,
    'already_requested': ClockIcon,
    'not_found': XIcon,
    'error': AlertIcon,
    'skipped': SkipIcon,
  }
  return icons[status] || AlertIcon
}

// Get status icon styling with unique colors for each status
const getStatusIconClass = (status: string) => {
  const classes: Record<string, string> = {
    'already_available': 'bg-green-500/90 text-white',      // Green for available
    'requested': 'bg-amber-500/90 text-white',              // Amber for requested
    'already_requested': 'bg-blue-500/90 text-white',       // Blue for already requested
    'not_found': 'bg-red-500/90 text-white',                // Red for not found
    'error': 'bg-red-600/90 text-white',                    // Dark red for errors
    'skipped': 'bg-gray-500/90 text-white',                 // Gray for skipped
  }
  return classes[status] || 'bg-gray-500/90 text-white'
}

// Get human-readable status label
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'already_available': 'Available',
    'requested': 'Requested',
    'already_requested': 'Already Requested',
    'not_found': 'Not Found',
    'error': 'Error',
    'skipped': 'Skipped',
  }
  return labels[status] || status
}

// Get list label for display
const getListLabel = (source: { list_type: string; list_id: string; display_name?: string }) => {
  // Use display_name if available, otherwise format the list_type
  if (source.display_name) {
    return source.display_name
  }
  
  // Format list_type for display
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
  
  return typeLabels[source.list_type] || source.list_type
}

// Handle card click
const handleClick = () => {
  if (props.item.overseerr_url) {
    window.open(props.item.overseerr_url, '_blank', 'noopener,noreferrer')
  } else {
    showError('Cannot open Overseerr', 'This item is not available in Overseerr')
  }
}

// Handle list tag click - open the source URL of the list
const listsStore = useListsStore()
const handleListTagClick = (source: { list_type: string; list_id: string; display_name?: string }) => {
  // First, try to get the URL from the lists store
  const list = listsStore.lists.find(
    l => l.list_type === source.list_type && l.list_id === source.list_id
  )
  
  let url: string | null = null
  
  if (list) {
    // Use the stored URL if available
    url = list.list_url || list.url || null
  }
  
  // If no URL found in store, construct it from list_type and list_id
  if (!url) {
    url = constructListUrl(source.list_type, source.list_id)
  }
  
  // Open the URL in a new tab (skip collections as they don't have URLs)
  if (url && !url.startsWith('collection:')) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}
</script>

<style scoped>
.poster-card:not(.simple-mode) {
  /* Smooth hover lift effect - only in full mode */
}

.poster-card:not(.simple-mode):hover {
  transform: translateY(-0.5rem);
}

.poster-card.simple-mode {
  /* Simple mode: subtle hover effect only */
}

.poster-card.simple-mode:hover {
  transform: scale(1.02);
}

/* Fade in animation for posters */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}

/* Skeleton loader animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Stagger animation delay for grid items */
.poster-card:nth-child(1) { animation-delay: 0ms; }
.poster-card:nth-child(2) { animation-delay: 50ms; }
.poster-card:nth-child(3) { animation-delay: 100ms; }
.poster-card:nth-child(4) { animation-delay: 150ms; }
.poster-card:nth-child(5) { animation-delay: 200ms; }
.poster-card:nth-child(6) { animation-delay: 250ms; }
.poster-card:nth-child(7) { animation-delay: 300ms; }
.poster-card:nth-child(8) { animation-delay: 350ms; }
.poster-card:nth-child(9) { animation-delay: 400ms; }
.poster-card:nth-child(10) { animation-delay: 450ms; }
</style>

