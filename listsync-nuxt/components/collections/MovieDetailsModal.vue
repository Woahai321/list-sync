<template>
  <Modal
    v-model="isOpen"
    size="lg"
    @close="handleClose"
  >
    <template #header>
      <div class="flex items-start gap-3 sm:gap-4">
        <!-- Movie Poster -->
        <div
          v-if="posterUrl"
          class="w-20 h-30 sm:w-24 sm:h-36 rounded-lg overflow-hidden flex-shrink-0 shadow-xl border border-purple-500/20"
        >
          <img
            :src="posterUrl"
            :alt="`${movie?.title} poster`"
            class="w-full h-full object-cover"
          />
        </div>
        
        <div class="flex-1 min-w-0">
          <h2 class="text-lg sm:text-xl font-bold text-foreground titillium-web-bold line-clamp-2 mb-1.5">
            {{ movie?.title }}
          </h2>
          <p v-if="movie?.original_title && movie.original_title !== movie.title" class="text-xs sm:text-sm text-muted-foreground mb-2">
            {{ movie.original_title }}
          </p>
          
          <div class="flex flex-wrap items-center gap-2 sm:gap-3 text-xs sm:text-sm">
            <!-- Rating -->
            <div v-if="movie?.rating && movie.rating > 0" class="flex items-center gap-1 px-2 py-1 rounded-md bg-yellow-500/20 border border-yellow-500/30">
              <StarIcon :size="12" class="sm:w-4 sm:h-4 text-yellow-400 fill-yellow-400" />
              <span class="font-semibold text-yellow-300">{{ formatRating(movie.rating) }}</span>
            </div>
            
            <!-- Year -->
            <div v-if="movie?.releaseDate" class="flex items-center gap-1 px-2 py-1 rounded-md bg-purple-500/20 border border-purple-500/30">
              <CalendarIcon :size="12" class="sm:w-4 sm:h-4 text-purple-400" />
              <span class="text-purple-300 font-medium">{{ formatYear(movie.releaseDate) }}</span>
            </div>
            
            <!-- Runtime -->
            <div v-if="movie?.runtime && movie.runtime > 0" class="flex items-center gap-1 px-2 py-1 rounded-md bg-purple-500/20 border border-purple-500/30">
              <ClockIcon :size="12" class="sm:w-4 sm:h-4 text-purple-400" />
              <span class="text-purple-300 font-medium">{{ formatRuntime(movie.runtime) }}</span>
            </div>
            
            <!-- Vote Count -->
            <div v-if="movie?.voteCount" class="flex items-center gap-1 px-2 py-1 rounded-md bg-blue-500/20 border border-blue-500/30">
              <UsersIcon :size="12" class="sm:w-4 sm:h-4 text-blue-400" />
              <span class="text-blue-300 font-medium text-[10px] sm:text-xs">{{ formatNumber(movie.voteCount) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="movie" class="space-y-4">
      <!-- Overview and Tagline -->
      <div class="space-y-3">
        <!-- Tagline -->
        <div v-if="movie.tagline" class="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <p class="text-xs sm:text-sm italic text-purple-300 text-center">{{ movie.tagline }}</p>
        </div>

        <!-- Overview -->
        <div v-if="movie.overview">
          <h3 class="text-sm font-semibold text-foreground mb-1.5">Overview</h3>
          <p class="text-xs sm:text-sm text-foreground/90 leading-relaxed line-clamp-4">{{ movie.overview }}</p>
        </div>
      </div>

      <!-- Genres and Quick Info Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Genres -->
        <div v-if="movie.genres && movie.genres.length > 0">
          <h3 class="text-xs sm:text-sm font-semibold text-foreground mb-2">Genres</h3>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="genre in movie.genres"
              :key="genre"
              class="px-2 py-1 rounded-md text-xs bg-purple-500/20 text-purple-200 border border-purple-500/40"
            >
              {{ genre }}
            </span>
          </div>
        </div>

        <!-- Additional Info -->
        <div class="space-y-2">
          <!-- Status -->
          <div v-if="movie.status" class="flex items-center justify-between py-1.5 border-b border-purple-500/10">
            <span class="text-xs text-muted-foreground font-medium">Status</span>
            <span class="text-xs text-foreground font-semibold">{{ movie.status }}</span>
          </div>

          <!-- Language -->
          <div v-if="movie.original_language" class="flex items-center justify-between py-1.5 border-b border-purple-500/10">
            <span class="text-xs text-muted-foreground font-medium">Language</span>
            <span class="text-xs text-foreground font-semibold">{{ movie.original_language.toUpperCase() }}</span>
          </div>

          <!-- Budget -->
          <div v-if="movie.budget && movie.budget > 0" class="flex items-center justify-between py-1.5 border-b border-purple-500/10">
            <span class="text-xs text-muted-foreground font-medium">Budget</span>
            <span class="text-xs text-foreground font-semibold">${{ formatNumber(movie.budget) }}</span>
          </div>

          <!-- Revenue -->
          <div v-if="movie.revenue && movie.revenue > 0" class="flex items-center justify-between py-1.5">
            <span class="text-xs text-muted-foreground font-medium">Revenue</span>
            <span class="text-xs text-foreground font-semibold">${{ formatNumber(movie.revenue) }}</span>
          </div>
        </div>
      </div>

      <!-- Production Countries and Languages (Compact) -->
      <div v-if="(movie.production_countries && movie.production_countries.length > 0) || (movie.spoken_languages && movie.spoken_languages.length > 0)" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Production Countries -->
        <div v-if="movie.production_countries && movie.production_countries.length > 0">
          <h3 class="text-xs sm:text-sm font-semibold text-foreground mb-2">Production</h3>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="country in movie.production_countries"
              :key="country"
              class="px-2 py-1 rounded-md text-xs bg-gray-500/20 text-gray-300 border border-gray-500/40"
            >
              {{ country }}
            </span>
          </div>
        </div>

        <!-- Spoken Languages -->
        <div v-if="movie.spoken_languages && movie.spoken_languages.length > 0">
          <h3 class="text-xs sm:text-sm font-semibold text-foreground mb-2">Languages</h3>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="lang in movie.spoken_languages"
              :key="lang"
              class="px-2 py-1 rounded-md text-xs bg-gray-500/20 text-gray-300 border border-gray-500/40"
            >
              {{ lang }}
            </span>
          </div>
        </div>
      </div>

      <!-- Overseerr Actions -->
      <div v-if="movie?.id" class="pt-3 border-t border-purple-500/10 flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3">
        <a
          v-if="overseerrUrl"
          :href="overseerrUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-medium text-xs sm:text-sm transition-all shadow-lg hover:shadow-purple-500/50 touch-manipulation"
        >
          <ExternalLinkIcon :size="14" class="sm:w-4 sm:h-4" />
          <span>View in Overseerr</span>
        </a>
        <button
          v-if="movie?.id"
          :disabled="isRequesting"
          @click="handleRequestMedia"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-400 to-purple-300 hover:from-purple-300 hover:to-purple-200 disabled:from-purple-500/50 disabled:to-purple-400/50 disabled:cursor-not-allowed text-white font-medium text-xs sm:text-sm transition-all shadow-lg hover:shadow-purple-400/50 touch-manipulation"
        >
          <SendIcon :size="14" class="sm:w-4 sm:h-4" :class="{ 'animate-pulse': isRequesting }" />
          <span>{{ isRequesting ? 'Requesting...' : 'Request in Overseerr' }}</span>
        </button>
        <div v-if="!overseerrUrl && !movie?.id" class="text-xs text-muted-foreground italic">
          Loading Overseerr URL...
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12">
      <AlertCircleIcon :size="48" class="text-muted-foreground mx-auto mb-4 opacity-50" />
      <p class="text-muted-foreground">Movie data not available</p>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import {
  Star as StarIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
  Users as UsersIcon,
  ExternalLink as ExternalLinkIcon,
  AlertCircle as AlertCircleIcon,
  Send as SendIcon,
} from 'lucide-vue-next'
import Modal from '~/components/ui/Modal.vue'
import type { CollectionMovie } from '~/types'

interface Props {
  modelValue: boolean
  movie: CollectionMovie | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleClose = () => {
  emit('close')
}

// Get Overseerr URL from config
const api = useApiService()
const overseerrBaseUrl = ref<string | null>(null)

// Load config when modal opens
watch(isOpen, async (open) => {
  if (open && !overseerrBaseUrl.value) {
    try {
      const config = await api.getConfig()
      overseerrBaseUrl.value = config.overseerr_url || null
    } catch (error) {
      console.error('Failed to load Overseerr URL from config:', error)
    }
  }
}, { immediate: true })

const posterUrl = computed(() => {
  if (props.movie?.poster_path) {
    return `https://image.tmdb.org/t/p/w500${props.movie.poster_path}`
  }
  return null
})

// Get Overseerr URL for the movie
const overseerrUrl = computed(() => {
  // Check if we have both the base URL and movie ID
  if (!overseerrBaseUrl.value || !props.movie?.id) {
    return null
  }
  
  // Ensure base URL doesn't have trailing slash
  const cleanBaseUrl = overseerrBaseUrl.value.replace(/\/$/, '')
  
  // Use TMDB ID to construct Overseerr URL
  return `${cleanBaseUrl}/movie/${props.movie.id}`
})

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

const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Request media functionality
const isRequesting = ref(false)
const { showSuccess, showError } = useToast()

const handleRequestMedia = async () => {
  if (!props.movie?.id || isRequesting.value) {
    return
  }
  
  isRequesting.value = true
  
  try {
    const response = await api.requestSingleMedia(props.movie.id, 'movie')
    
    if (response.success) {
      if (response.status === 'already_requested' || response.status === 'already_available') {
        showSuccess(response.message || 'Media is already in Overseerr')
      } else {
        showSuccess(response.message || 'Media successfully requested in Overseerr')
      }
    } else {
      showError(response.message || 'Failed to request media')
    }
  } catch (error: any) {
    console.error('Error requesting media:', error)
    showError(error?.message || 'Failed to request media. Please try again.')
  } finally {
    isRequesting.value = false
  }
}
</script>

