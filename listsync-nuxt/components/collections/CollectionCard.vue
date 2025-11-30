<template>
  <div
    class="collection-card group relative transition-all duration-300 ease-out animate-fade-in"
    :class="{ 
      'animate-pulse': isLoading,
      'ring-2 ring-purple-500 shadow-xl shadow-purple-500/30': isSelected,
      'opacity-60': isSynced
    }"
    role="button"
    :aria-label="`Collection: ${collection.franchise}`"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <!-- Selection Checkbox -->
    <div v-if="selectable" class="absolute top-2 left-2 z-20">
      <label class="relative inline-flex items-center cursor-pointer touch-manipulation group/checkbox">
        <input
          type="checkbox"
          :checked="isSelected"
          class="sr-only peer"
          @click.stop
          @change="$emit('toggle-select')"
        />
        <div
          class="w-6 h-6 rounded-lg border-2 transition-all duration-200 flex items-center justify-center backdrop-blur-sm shadow-lg"
          :class="isSelected 
            ? 'bg-gradient-to-br from-purple-500 to-purple-600 border-purple-400 shadow-purple-500/50 ring-2 ring-purple-500/30' 
            : 'bg-black/60 border-purple-500/40 group-hover/checkbox:border-purple-400 group-hover/checkbox:bg-purple-500/10'"
        >
          <CheckMarkIcon
            v-if="isSelected"
            :size="14"
            class="text-white transition-all duration-200 stroke-[3]"
            :class="isSelected ? 'scale-100 opacity-100' : 'scale-0 opacity-0'"
          />
        </div>
      </label>
    </div>

    <!-- Synced Status Badge -->
    <div v-if="isSynced" class="absolute top-2 right-2 z-20">
      <div class="px-2 py-1 rounded-md bg-green-500/90 backdrop-blur-sm border border-green-400/50 shadow-md flex items-center gap-1">
        <CheckIcon :size="12" class="text-white" />
        <span class="text-[10px] font-bold text-white">Synced</span>
      </div>
    </div>

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
          :alt="`${collection.franchise} poster`"
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
          <FilmIcon :size="48" class="text-purple-500/30" />
        </div>

        <!-- Always Visible: Gradient Overlay for Title (matching items page) -->
        <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent pointer-events-none" />

        <!-- Collection Name and Info -->
        <div class="absolute inset-x-0 bottom-0 p-3 pointer-events-none">
          <h3 class="text-white font-bold text-sm leading-tight line-clamp-2 drop-shadow-lg mb-1.5">
            {{ collection.franchise }}
          </h3>
          
          <!-- Rating and Movie Count -->
          <div class="flex items-center gap-3 text-xs">
            <!-- Average Rating -->
            <div class="flex items-center gap-1">
              <StarIcon :size="12" class="text-yellow-400 fill-yellow-400" />
              <span class="text-white font-medium">{{ formatRating(collection.averageRating) }}</span>
            </div>
            
            <!-- Movie Count -->
            <div class="flex items-center gap-1">
              <FilmIcon :size="12" class="text-purple-300" />
              <span class="text-purple-300 font-medium">{{ collection.totalMovies }} movies</span>
            </div>
          </div>
        </div>

        <!-- Hover Overlay: Sync Button -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/95 via-purple-950/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
          <!-- Collection Name (duplicate for hover state) -->
          <h3 class="text-white font-bold text-base leading-tight mb-1">
            {{ collection.franchise }}
          </h3>
          
          <!-- Rating and Movie Count (duplicate for hover) -->
          <div class="flex items-center gap-3 text-sm mb-3">
            <div class="flex items-center gap-1">
              <StarIcon :size="14" class="text-yellow-400 fill-yellow-400" />
              <span class="text-white font-medium">{{ formatRating(collection.averageRating) }}</span>
            </div>
            <div class="flex items-center gap-1">
              <FilmIcon :size="14" class="text-purple-300" />
              <span class="text-purple-300 font-medium">{{ collection.totalMovies }} movies</span>
            </div>
          </div>

          <!-- Sync Collection Button -->
          <button
            class="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-medium text-xs py-1.5 px-2 rounded-md flex items-center justify-center gap-1.5 transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isSyncing"
            @click.stop="handleSync"
          >
            <RefreshCwIcon v-if="!isSyncing" :size="12" />
            <LoaderIcon v-else :size="12" class="animate-spin" />
            <span>{{ isSyncing ? 'Syncing...' : 'Sync Collection' }}</span>
          </button>
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
  Star as StarIcon,
  RefreshCw as RefreshCwIcon,
  Loader2 as LoaderIcon,
  CheckCircle2 as CheckIcon,
  Check as CheckMarkIcon,
} from 'lucide-vue-next'
import type { Collection } from '~/types'

interface Props {
  collection: Collection
  isLoading?: boolean
  isSyncing?: boolean
  selectable?: boolean
  isSelected?: boolean
  isSynced?: boolean
  lastSynced?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isSyncing: false,
  selectable: false,
  isSelected: false,
  isSynced: false,
  lastSynced: null
})

const emit = defineEmits<{
  sync: [franchise: string]
  'toggle-select': []
  'open-details': []
}>()

const { showSuccess, showError } = useToast()

// Use smart lazy loading composable
const { imageRef, actualSrc, imageLoaded, imageError, handleLoad, handleError } = useLazyImage(
  computed(() => props.collection.poster_url)
)

// Format rating to 1 decimal place
const formatRating = (rating: number) => {
  return rating.toFixed(1)
}

// Handle card click (open details modal)
const handleClick = (event: MouseEvent | KeyboardEvent) => {
  // Don't open modal if clicking on sync button or checkbox
  const target = event.target as HTMLElement
  if (target.closest('button') || target.closest('input[type="checkbox"]')) {
    return
  }
  
  emit('open-details')
}

// Handle sync button click
const handleSync = async () => {
  if (props.isSyncing) return
  
  emit('sync', props.collection.franchise)
}
</script>

<style scoped>
.collection-card {
  /* Smooth hover lift effect */
  @apply hover:-translate-y-2;
}

/* Fade in animation for collections */
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
.collection-card:nth-child(1) { animation-delay: 0ms; }
.collection-card:nth-child(2) { animation-delay: 50ms; }
.collection-card:nth-child(3) { animation-delay: 100ms; }
.collection-card:nth-child(4) { animation-delay: 150ms; }
.collection-card:nth-child(5) { animation-delay: 200ms; }
.collection-card:nth-child(6) { animation-delay: 250ms; }
.collection-card:nth-child(7) { animation-delay: 300ms; }
.collection-card:nth-child(8) { animation-delay: 350ms; }
.collection-card:nth-child(9) { animation-delay: 400ms; }
.collection-card:nth-child(10) { animation-delay: 450ms; }
</style>

