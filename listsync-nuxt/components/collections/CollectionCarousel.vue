<template>
  <div class="collection-carousel-container">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30">
          <TrendingUpIcon :size="20" class="text-purple-400" />
        </div>
        <div>
          <h2 class="text-xl sm:text-2xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
            Most Popular Collections
          </h2>
          <p class="text-xs text-muted-foreground">Top {{ collections.length }} by community votes</p>
        </div>
      </div>
      
      <!-- Navigation Arrows (Desktop) -->
      <div class="hidden md:flex items-center gap-2">
        <button
          @click="scrollLeft"
          :disabled="!canScrollLeft"
          class="p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          aria-label="Scroll left"
        >
          <ChevronLeftIcon :size="20" class="text-purple-400" />
        </button>
        <button
          @click="scrollRight"
          :disabled="!canScrollRight"
          class="p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          aria-label="Scroll right"
        >
          <ChevronRightIcon :size="20" class="text-purple-400" />
        </button>
      </div>
    </div>

    <!-- Carousel -->
    <div class="carousel-wrapper relative group">
      <!-- Left Fade Gradient -->
      <div 
        v-if="canScrollLeft"
        class="hidden md:block absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none"
      ></div>
      
      <!-- Right Fade Gradient -->
      <div 
        v-if="canScrollRight"
        class="hidden md:block absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none"
      ></div>

      <!-- Scrollable Container - Added padding to prevent cutoff -->
      <div
        ref="scrollContainer"
        class="carousel-scroll flex gap-4 overflow-x-auto scroll-smooth py-4 snap-x snap-mandatory hide-scrollbar"
        @scroll="updateScrollState"
      >
        <!-- Collection Cards -->
        <div
          v-for="(collection, index) in collections"
          :key="collection.franchise"
          class="carousel-item flex-shrink-0 snap-start"
        >
          <div
            class="featured-collection-card group relative transition-all duration-300 ease-out cursor-pointer"
            :class="getRankClass(index)"
            @click="$emit('open-details', collection)"
          >
            <!-- Rank Badge -->
            <div class="absolute top-2 left-2 z-20 rank-badge" :class="getRankBadgeClass(index)">
              <span class="text-sm font-bold">#{{ index + 1 }}</span>
            </div>

            <!-- Synced Badge -->
            <div v-if="isSynced(collection.franchise)" class="absolute top-2 right-2 z-20">
              <div class="px-2 py-1 rounded-md bg-green-500/90 backdrop-blur-sm border border-green-400/30 flex items-center gap-1">
                <CheckIcon :size="10" class="text-white" />
                <span class="text-[10px] font-semibold text-white">Synced</span>
              </div>
            </div>

            <!-- Poster Container -->
            <div class="poster-container relative w-[240px] sm:w-[260px] rounded-xl overflow-hidden">
              <div class="aspect-[2/3] relative bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900">
                <!-- Blur Placeholder -->
                <div 
                  v-if="collection.poster_url && !isImageLoaded(collection.franchise)"
                  class="absolute inset-0 bg-gradient-to-br from-purple-900/40 to-gray-900/60 animate-pulse"
                >
                  <div class="absolute inset-0 backdrop-blur-xl bg-purple-500/5"></div>
                </div>
                
                <!-- Poster Image -->
                <img
                  v-if="collection.poster_url"
                  :src="collection.poster_url"
                  :alt="`${collection.franchise} poster`"
                  class="absolute inset-0 w-full h-full object-cover transition-all duration-500"
                  :class="{ 
                    'opacity-0 scale-105': !isImageLoaded(collection.franchise),
                    'opacity-100 scale-100': isImageLoaded(collection.franchise)
                  }"
                  @load="markImageLoaded(collection.franchise)"
                  @error="handleImageError(collection.franchise)"
                />
                
                <!-- Fallback -->
                <div
                  v-if="!collection.poster_url || hasImageError(collection.franchise)"
                  class="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900 flex items-center justify-center"
                >
                  <FilmIcon :size="64" class="text-purple-500/30" />
                </div>

                <!-- Gradient Overlay -->
                <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-70"></div>

                <!-- Info Overlay -->
                <div class="absolute inset-x-0 bottom-0 p-4">
                  <h3 class="text-white font-bold text-base sm:text-lg leading-tight line-clamp-2 drop-shadow-lg mb-2">
                    {{ collection.franchise }}
                  </h3>
                  
                  <div class="flex items-center gap-3 text-sm mb-3">
                    <div class="flex items-center gap-1">
                      <StarIcon :size="14" class="text-yellow-400 fill-yellow-400" />
                      <span class="text-white font-semibold">{{ formatRating(collection.averageRating) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <FilmIcon :size="14" class="text-purple-300" />
                      <span class="text-purple-200 font-medium">{{ collection.totalMovies }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <UsersIcon :size="14" class="text-blue-300" />
                      <span class="text-blue-200 font-medium text-xs">{{ formatVotes(collection.totalVotes) }}</span>
                    </div>
                  </div>

                  <!-- Action Button -->
                  <button
                    @click.stop="$emit('sync', collection.franchise)"
                    :disabled="isSyncing(collection.franchise)"
                    class="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-medium text-sm py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCwIcon v-if="isSyncing(collection.franchise)" :size="14" class="animate-spin" />
                    <template v-else>
                      <PlayIcon :size="14" />
                      <span>{{ isSynced(collection.franchise) ? 'Re-sync' : 'Sync Collection' }}</span>
                    </template>
                  </button>
                </div>
              </div>
            </div>

            <!-- Featured Glow -->
            <div class="featured-glow" :class="getGlowClass(index)"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Scroll Indicators -->
    <div class="flex md:hidden justify-center gap-1.5 mt-3">
      <div
        v-for="(_, index) in Math.min(collections.length, 10)"
        :key="index"
        class="h-1.5 rounded-full transition-all duration-300"
        :class="getCurrentPageIndex() === index ? 'w-6 bg-purple-500' : 'w-1.5 bg-purple-500/30'"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  TrendingUp as TrendingUpIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Film as FilmIcon,
  Star as StarIcon,
  Users as UsersIcon,
  RefreshCw as RefreshCwIcon,
  Play as PlayIcon,
  CheckCircle2 as CheckIcon,
} from 'lucide-vue-next'
import type { Collection } from '~/types'

interface Props {
  collections: Collection[]
  syncedCollections?: Set<string>
  syncingCollections?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  syncedCollections: () => new Set(),
  syncingCollections: () => new Set()
})

const emit = defineEmits<{
  sync: [franchise: string]
  'open-details': [collection: Collection]
}>()

// Scroll state
const scrollContainer = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(true)

// Image loading state
const loadedImages = ref<Set<string>>(new Set())
const errorImages = ref<Set<string>>(new Set())

// Check if collection is synced
const isSynced = (franchise: string) => props.syncedCollections?.has(franchise)

// Check if collection is syncing
const isSyncing = (franchise: string) => props.syncingCollections?.has(franchise)

// Image loading helpers
const isImageLoaded = (franchise: string) => loadedImages.value.has(franchise)
const hasImageError = (franchise: string) => errorImages.value.has(franchise)
const markImageLoaded = (franchise: string) => loadedImages.value.add(franchise)
const handleImageError = (franchise: string) => errorImages.value.add(franchise)

// Format rating
const formatRating = (rating: number) => rating.toFixed(1)

// Format votes
const formatVotes = (votes: number) => {
  if (votes >= 1000) {
    return `${(votes / 1000).toFixed(1)}K`
  }
  return votes.toString()
}

// Get rank-based classes - now just purple variants
const getRankClass = (index: number) => {
  // All cards get consistent purple styling
  return ''
}

const getRankBadgeClass = (index: number) => {
  // All badges use purple gradient
  return 'bg-gradient-to-br from-purple-600 to-purple-700 text-white'
}

const getGlowClass = (index: number) => {
  // All glows use purple
  return 'glow-purple'
}

// Scroll functions
const scrollLeft = () => {
  if (scrollContainer.value) {
    const cardWidth = 280 + 16 // card width + gap
    scrollContainer.value.scrollBy({ left: -cardWidth * 3, behavior: 'smooth' })
  }
}

const scrollRight = () => {
  if (scrollContainer.value) {
    const cardWidth = 280 + 16
    scrollContainer.value.scrollBy({ left: cardWidth * 3, behavior: 'smooth' })
  }
}

const updateScrollState = () => {
  if (scrollContainer.value) {
    const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
    canScrollLeft.value = scrollLeft > 0
    canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 10
  }
}

const getCurrentPageIndex = () => {
  if (!scrollContainer.value) return 0
  const cardWidth = 280 + 16
  const scrollLeft = scrollContainer.value.scrollLeft
  return Math.round(scrollLeft / cardWidth)
}

// Initialize scroll state
onMounted(() => {
  updateScrollState()
  if (scrollContainer.value) {
    scrollContainer.value.addEventListener('scroll', updateScrollState)
  }
})

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', updateScrollState)
  }
})
</script>

<style scoped>
.carousel-wrapper {
  position: relative;
}

.carousel-scroll {
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.carousel-scroll::-webkit-scrollbar {
  display: none;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.carousel-item {
  scroll-snap-align: start;
}

.featured-collection-card {
  position: relative;
  transition: all 0.3s ease-out;
}

.featured-collection-card:hover {
  /* No transform - just opacity and shadow changes to prevent cutoff */
}

.rank-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.featured-glow {
  position: absolute;
  inset: -2px;
  border-radius: 1rem;
  opacity: 0;
  filter: blur(12px);
  transition: opacity 0.3s;
  pointer-events: none;
  z-index: -1;
}

.featured-collection-card:hover .featured-glow {
  opacity: 0.4;
}

.glow-purple {
  background: linear-gradient(45deg, #a855f7, #ec4899);
}

/* Removed gold/silver/bronze - all use purple */
.poster-container {
  box-shadow: 0 4px 16px rgba(168, 85, 247, 0.2);
  transition: box-shadow 0.3s ease-out;
}

.featured-collection-card:hover .poster-container {
  box-shadow: 0 8px 28px rgba(168, 85, 247, 0.4);
}
</style>

