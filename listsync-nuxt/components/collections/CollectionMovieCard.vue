<template>
  <div
    class="movie-card group relative transition-all duration-300 ease-out cursor-pointer animate-fade-in"
    role="button"
    :aria-label="`View ${movie.title} details`"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <!-- Poster Image Container -->
    <div ref="imageRef" class="poster-container relative w-full rounded-xl overflow-hidden shadow-xl border border-purple-500/20 group-hover:border-purple-500/40 transition-colors duration-300">
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
          :alt="`${movie.title} poster`"
          class="absolute inset-0 w-full h-full object-cover transition-all duration-500 ease-out"
          :class="{ 
            'opacity-0 scale-105': !imageLoaded,
            'opacity-100 scale-100': imageLoaded
          }"
          @load="handleLoad"
          @error="handleError"
        />
        
        <!-- Fallback Placeholder -->
        <div
          v-if="!actualSrc || imageError"
          class="absolute inset-0 w-full h-full bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900 flex items-center justify-center"
        >
          <FilmIcon :size="48" class="text-purple-500/30" />
        </div>

        <!-- Rating Badge (Top Right) -->
        <div
          v-if="movie.rating && movie.rating > 0"
          class="absolute top-2 right-2 px-2.5 py-1.5 rounded-lg bg-yellow-500/95 backdrop-blur-sm border border-yellow-400/60 shadow-lg flex items-center gap-1.5 z-10"
        >
          <StarIcon :size="12" class="text-white fill-white" />
          <span class="text-xs font-bold text-white tabular-nums">{{ formatRating(movie.rating) }}</span>
        </div>

        <!-- Runtime Badge (Top Left) -->
        <div
          v-if="movie.runtime && movie.runtime > 0"
          class="absolute top-2 left-2 px-2 py-1 rounded-lg bg-black/80 backdrop-blur-sm border border-white/20 shadow-lg flex items-center gap-1 z-10"
        >
          <ClockIcon :size="10" class="text-white/80" />
          <span class="text-[10px] font-medium text-white/90 tabular-nums">{{ formatRuntime(movie.runtime) }}</span>
        </div>

        <!-- Always Visible: Gradient Overlay for Title -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none" />

        <!-- Always Visible: Title and Year -->
        <div class="absolute inset-x-0 bottom-0 p-3 pointer-events-none">
          <h3 class="text-white font-bold text-sm leading-tight line-clamp-2 drop-shadow-lg mb-1">
            {{ movie.title }}
          </h3>
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1 px-2 py-0.5 rounded bg-purple-500/30 border border-purple-400/40">
              <CalendarIcon :size="10" class="text-purple-300" />
              <span class="text-purple-200 text-[10px] font-semibold">
                {{ formatYear(movie.releaseDate) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Hover Overlay: Simple view with title, year, and brief description -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/95 via-purple-950/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-3">
          <!-- Title -->
          <h3 class="text-white font-bold text-sm leading-tight mb-1.5 line-clamp-2">
            {{ movie.title }}
          </h3>
          
          <!-- Year -->
          <div class="flex items-center gap-1 mb-2">
            <CalendarIcon :size="12" class="text-purple-400" />
            <span class="text-purple-300 text-xs font-medium">
              {{ formatYear(movie.releaseDate) }}
            </span>
          </div>

          <!-- Overview (3 lines max) -->
          <p v-if="movie.overview" class="text-white/90 text-xs leading-relaxed line-clamp-3">
            {{ movie.overview }}
          </p>
          <p v-else class="text-white/60 text-xs italic">
            No description available
          </p>
        </div>
      </div>
    </div>

    <!-- Hover Effect: Purple Glow -->
    <div class="absolute -inset-1 bg-gradient-to-r from-purple-600/50 via-purple-500/50 to-purple-600/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-xl" />
  </div>
</template>

<script setup lang="ts">
import {
  Film as FilmIcon,
  Star as StarIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
} from 'lucide-vue-next'
import { useLazyImage } from '~/composables/useLazyImage'
import type { CollectionMovie } from '~/types'

interface Props {
  movie: CollectionMovie
}

const props = defineProps<Props>()

defineEmits<{
  click: []
}>()

const posterUrl = computed(() => {
  if (props.movie.poster_path) {
    return `https://image.tmdb.org/t/p/w500${props.movie.poster_path}`
  }
  return null
})

// Use lazy image composable
const { imageRef, actualSrc, imageLoaded, imageError, handleLoad, handleError } = useLazyImage(posterUrl)

const formatRating = (rating: number) => {
  return rating.toFixed(1)
}

const formatYear = (dateString?: string) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.getFullYear().toString()
  } catch {
    return dateString.split('-')[0] || 'N/A'
  }
}

const formatRuntime = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins}m`
}
</script>

<style scoped>
.movie-card {
  @apply hover:-translate-y-2;
}
</style>

