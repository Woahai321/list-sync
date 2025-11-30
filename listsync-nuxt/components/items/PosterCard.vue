<template>
  <div
    class="poster-card group relative transition-all duration-300 ease-out animate-fade-in"
    :class="{ 'animate-pulse': isLoading }"
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
        <div class="absolute inset-0 bg-gradient-to-t from-black/95 via-purple-950/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
          <!-- Title and Year (duplicate for hover state) -->
          <h3 class="text-white font-bold text-base leading-tight mb-0.5">
            {{ item.title }}
          </h3>
          <p class="text-purple-300 text-sm font-medium mb-1.5">
            {{ item.year || 'N/A' }}
          </p>

          <!-- Overview -->
          <p v-if="item.overview" class="text-white/90 text-xs leading-relaxed line-clamp-2 mb-3">
            {{ item.overview }}
          </p>

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
      </div>
    </div>

    <!-- Hover Effect: Purple Glow (Subtle) -->
    <div class="absolute -inset-0.5 bg-gradient-to-r from-purple-600/40 via-purple-500/40 to-purple-600/40 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-md" />
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
  MinusCircle as SkipIcon
} from 'lucide-vue-next'
import type { EnrichedMediaItem } from '~/types'

interface Props {
  item: EnrichedMediaItem
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false
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

// Handle card click
const handleClick = () => {
  if (props.item.overseerr_url) {
    window.open(props.item.overseerr_url, '_blank', 'noopener,noreferrer')
  } else {
    showError('Cannot open Overseerr', 'This item is not available in Overseerr')
  }
}
</script>

<style scoped>
.poster-card {
  /* Smooth hover lift effect */
  @apply hover:-translate-y-2;
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

