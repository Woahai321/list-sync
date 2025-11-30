<template>
  <div
    class="collection-list-item group relative flex items-center gap-4 p-3 rounded-lg border border-purple-500/20 hover:border-purple-400/40 bg-gradient-to-r from-background to-purple-950/5 hover:from-purple-950/10 hover:to-purple-900/10 transition-all duration-300 cursor-pointer"
    :class="{ 
      'ring-2 ring-purple-500 shadow-lg shadow-purple-500/20': isSelected,
      'opacity-70': isSynced
    }"
    @click="handleClick"
  >
    <!-- Selection Checkbox -->
    <div v-if="selectable" class="flex-shrink-0" @click.stop>
      <label class="relative inline-flex items-center cursor-pointer touch-manipulation group/checkbox">
        <input
          type="checkbox"
          :checked="isSelected"
          class="sr-only peer"
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

    <!-- Thumbnail -->
    <div class="flex-shrink-0 relative">
      <div class="w-16 h-24 rounded-lg overflow-hidden shadow-lg border border-purple-500/20">
        <!-- Blur Placeholder -->
        <div 
          v-if="collection.poster_url && !imageLoaded"
          class="absolute inset-0 bg-gradient-to-br from-purple-900/40 to-gray-900/60 animate-pulse"
        >
          <div class="absolute inset-0 backdrop-blur-sm bg-purple-500/5"></div>
        </div>
        
        <!-- Image -->
        <img
          v-if="collection.poster_url && !imageError"
          :src="collection.poster_url"
          :alt="`${collection.franchise} poster`"
          class="w-full h-full object-cover transition-opacity duration-300"
          :class="{ 'opacity-0': !imageLoaded, 'opacity-100': imageLoaded }"
          @load="imageLoaded = true"
          @error="imageError = true"
        />
        
        <!-- Fallback -->
        <div
          v-if="!collection.poster_url || imageError"
          class="w-full h-full bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900 flex items-center justify-center"
        >
          <FilmIcon :size="24" class="text-purple-500/30" />
        </div>
      </div>
      
      <!-- Synced Badge (Small) -->
      <div v-if="isSynced" class="absolute -top-1 -right-1 z-10">
        <div class="w-5 h-5 rounded-full bg-green-500 border-2 border-background flex items-center justify-center">
          <CheckIcon :size="10" class="text-white" />
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <!-- Title -->
      <h3 class="text-base font-bold text-foreground line-clamp-1 mb-1 group-hover:text-purple-400 transition-colors">
        {{ collection.franchise }}
      </h3>
      
      <!-- Metadata -->
      <div class="flex items-center gap-3 text-xs text-muted-foreground mb-1.5">
        <div class="flex items-center gap-1">
          <FilmIcon :size="12" class="text-purple-400" />
          <span class="font-medium">{{ collection.totalMovies }} {{ collection.totalMovies === 1 ? 'movie' : 'movies' }}</span>
        </div>
        <span class="text-purple-500/50">•</span>
        <div class="flex items-center gap-1">
          <UsersIcon :size="12" class="text-blue-400" />
          <span class="font-medium">{{ formatVotes(collection.totalVotes) }} votes</span>
        </div>
        <span class="text-purple-500/50">•</span>
        <div class="flex items-center gap-1">
          <StarIcon :size="12" class="text-yellow-400 fill-yellow-400" />
          <span class="font-medium">{{ formatRating(collection.averageRating) }}</span>
        </div>
      </div>
      
      <!-- Tags -->
      <div class="flex items-center gap-2 flex-wrap">
        <span v-if="isSynced" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-green-500/20 border border-green-500/30 text-green-400 text-[10px] font-semibold">
          <CheckCircleIcon :size="10" />
          Synced
        </span>
        <span v-if="isPopular" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-500/20 border border-purple-500/30 text-purple-400 text-[10px] font-semibold">
          <TrendingUpIcon :size="10" />
          Popular
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex-shrink-0 flex items-center gap-2">
      <!-- Info Button -->
      <button
        @click.stop="$emit('open-details')"
        class="p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-400 transition-all hover:scale-105"
        aria-label="View details"
      >
        <InfoIcon :size="16" />
      </button>
      
      <!-- Sync Button -->
      <button
        @click.stop="$emit('sync', collection.franchise)"
        :disabled="isSyncing"
        class="px-3 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-semibold text-sm flex items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
      >
        <RefreshCwIcon v-if="isSyncing" :size="14" class="animate-spin" />
        <PlayIcon v-else :size="14" />
        <span class="hidden sm:inline">{{ isSynced ? 'Re-sync' : 'Sync' }}</span>
      </button>
    </div>

    <!-- Hover Border Effect -->
    <div class="absolute inset-0 rounded-lg border-2 border-purple-500/0 group-hover:border-purple-500/30 transition-all pointer-events-none"></div>
  </div>
</template>

<script setup lang="ts">
import {
  Film as FilmIcon,
  Star as StarIcon,
  Users as UsersIcon,
  RefreshCw as RefreshCwIcon,
  Play as PlayIcon,
  CheckCircle2 as CheckIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  Info as InfoIcon,
  Check as CheckMarkIcon,
} from 'lucide-vue-next'
import type { Collection } from '~/types'

interface Props {
  collection: Collection
  isSyncing?: boolean
  isSynced?: boolean
  selectable?: boolean
  isSelected?: boolean
  isPopular?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSyncing: false,
  isSynced: false,
  selectable: false,
  isSelected: false,
  isPopular: false
})

const emit = defineEmits<{
  sync: [franchise: string]
  'toggle-select': []
  'open-details': []
  click: []
}>()

// Image loading state
const imageLoaded = ref(false)
const imageError = ref(false)

// Format helpers
const formatRating = (rating: number) => rating.toFixed(1)

const formatVotes = (votes: number) => {
  if (votes >= 1000) {
    return `${(votes / 1000).toFixed(1)}K`
  }
  return votes.toString()
}

// Handle card click (for details modal)
const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.collection-list-item {
  animation: fadeIn 0.3s ease-out;
}

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
</style>

