<template>
  <Modal
    v-model="isOpen"
    size="full"
    @close="handleClose"
  >
    <template #header>
      <div class="flex items-start gap-3 sm:gap-4">
        <!-- Collection Poster -->
        <div
          v-if="collection?.poster_url"
          class="w-16 h-24 sm:w-20 sm:h-30 rounded-lg sm:rounded-xl overflow-hidden flex-shrink-0 shadow-xl border-2 border-purple-500/30"
        >
          <img
            :src="collection.poster_url"
            :alt="`${collection.franchise} poster`"
            class="w-full h-full object-cover"
          />
        </div>
        <div v-else class="w-16 h-24 sm:w-20 sm:h-30 rounded-lg sm:rounded-xl bg-gradient-to-br from-gray-900 via-purple-950/20 to-gray-900 flex items-center justify-center border-2 border-purple-500/20">
          <FilmIcon :size="24" class="sm:w-8 sm:h-8 text-purple-500/30" />
        </div>
        
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 sm:gap-3 mb-2">
            <h2 class="text-lg sm:text-2xl md:text-3xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent line-clamp-2">
              {{ collection?.franchise || 'Collection Details' }}
            </h2>
          </div>
          
          <div class="flex flex-wrap items-center gap-2 text-xs sm:text-sm">
            <div class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 rounded-lg bg-yellow-500/20 border border-yellow-500/30">
              <StarIcon :size="14" class="sm:w-4 sm:h-4 text-yellow-400 fill-yellow-400" />
              <span class="text-yellow-300 font-bold">{{ formatRating(collection?.averageRating || 0) }}</span>
            </div>
            <div class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 rounded-lg bg-purple-500/20 border border-purple-500/30">
              <FilmIcon :size="14" class="sm:w-4 sm:h-4 text-purple-400" />
              <span class="text-purple-300 font-semibold">{{ collection?.totalMovies || 0 }}</span>
            </div>
            <div class="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-500/20 border border-blue-500/30">
              <UsersIcon :size="16" class="text-blue-400" />
              <span class="text-blue-300 font-semibold">{{ formatNumber(collection?.totalVotes || 0) }} votes</span>
            </div>
            <div v-if="collection?.popularity" class="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-500/20 border border-purple-500/30">
              <TrendingUpIcon :size="16" class="text-purple-400" />
              <span class="text-purple-300 font-semibold">{{ formatNumber(collection.popularity) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12 sm:py-20">
      <div class="text-center">
        <LoadingSpinner size="lg" color="primary" />
        <p class="text-xs sm:text-sm text-muted-foreground mt-4">Loading movies...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center py-12 sm:py-20">
      <Card variant="default" class="glass-card border-2 border-red-500/30 max-w-md mx-auto">
        <div class="text-center p-4 sm:p-6">
          <div class="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center">
            <AlertCircleIcon :size="24" class="sm:w-8 sm:h-8 text-red-400" />
          </div>
          <h3 class="text-base sm:text-lg font-bold text-red-400 mb-2">Failed to Load Movies</h3>
          <p class="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">{{ error }}</p>
          <Button variant="primary" @click="loadMovies" size="sm">
            <RefreshCwIcon :size="14" class="mr-2" />
            Try Again
          </Button>
        </div>
      </Card>
    </div>

    <!-- Movies Content -->
    <div v-else-if="movies.length > 0" class="space-y-4 sm:space-y-6">
      <!-- Overview (if available) -->
      <div v-if="collection?.overview" class="p-3 sm:p-4 rounded-xl bg-gradient-to-r from-purple-500/10 via-purple-600/10 to-purple-500/10 border border-purple-500/30 backdrop-blur-sm">
        <div class="flex items-start gap-2 sm:gap-3">
          <InfoIcon :size="16" class="sm:w-[18px] sm:h-[18px] text-purple-400 flex-shrink-0 mt-0.5" />
          <p class="text-xs sm:text-sm text-foreground leading-relaxed">{{ collection.overview }}</p>
        </div>
      </div>

      <!-- Quick Stats Bar -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
        <Card variant="default" class="glass-card border border-purple-500/20 p-2 sm:p-3">
          <div class="flex items-center gap-1.5 sm:gap-2">
            <div class="p-1 sm:p-1.5 rounded-lg bg-purple-600/20 border border-purple-500/30">
              <FilmIcon :size="12" class="sm:w-[14px] sm:h-[14px] text-purple-400" />
            </div>
            <div class="min-w-0">
              <p class="text-[9px] sm:text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Total</p>
              <p class="text-base sm:text-lg font-bold text-foreground tabular-nums">{{ movies.length }}</p>
            </div>
          </div>
        </Card>
        
        <Card variant="default" class="glass-card border border-yellow-500/20 p-2 sm:p-3">
          <div class="flex items-center gap-1.5 sm:gap-2">
            <div class="p-1 sm:p-1.5 rounded-lg bg-yellow-600/20 border border-yellow-500/30">
              <StarIcon :size="12" class="sm:w-[14px] sm:h-[14px] text-yellow-400 fill-yellow-400" />
            </div>
            <div class="min-w-0">
              <p class="text-[9px] sm:text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Rating</p>
              <p class="text-base sm:text-lg font-bold text-foreground tabular-nums">{{ calculateAverageRating() }}</p>
            </div>
          </div>
        </Card>
        
        <Card variant="default" class="glass-card border border-blue-500/20 p-2 sm:p-3">
          <div class="flex items-center gap-1.5 sm:gap-2">
            <div class="p-1 sm:p-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30">
              <CalendarIcon :size="12" class="sm:w-[14px] sm:h-[14px] text-blue-400" />
            </div>
            <div class="min-w-0">
              <p class="text-[9px] sm:text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Span</p>
              <p class="text-base sm:text-lg font-bold text-foreground tabular-nums">{{ getYearSpan() }}</p>
            </div>
          </div>
        </Card>
        
        <Card variant="default" class="glass-card border border-green-500/20 p-2 sm:p-3">
          <div class="flex items-center gap-1.5 sm:gap-2">
            <div class="p-1 sm:p-1.5 rounded-lg bg-green-600/20 border border-green-500/30">
              <ClockIcon :size="12" class="sm:w-[14px] sm:h-[14px] text-green-400" />
            </div>
            <div class="min-w-0">
              <p class="text-[9px] sm:text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Time</p>
              <p class="text-base sm:text-lg font-bold text-foreground tabular-nums">{{ getTotalRuntime() }}</p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Movies Grid -->
      <div>
        <div class="flex items-center justify-between mb-3 sm:mb-4">
          <h3 class="text-base sm:text-lg font-bold text-foreground flex items-center gap-2">
            <FilmIcon :size="18" class="sm:w-5 sm:h-5 text-purple-400" />
            Movies <span class="text-muted-foreground text-sm">({{ movies.length }})</span>
          </h3>
          <div class="text-[10px] sm:text-xs text-muted-foreground">
            By release date
          </div>
        </div>
        
        <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4">
          <CollectionMovieCard
            v-for="movie in movies"
            :key="movie.id"
            :movie="movie"
            @click="openMovieDetails(movie)"
          />
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex items-center justify-center py-20">
      <Card variant="default" class="glass-card border-2 border-dashed border-purple-500/20 max-w-md mx-auto">
        <div class="text-center p-8">
          <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center">
            <FilmIcon :size="40" class="text-purple-400 opacity-50" />
          </div>
          <h3 class="text-xl font-bold text-foreground mb-2">No Movies Found</h3>
          <p class="text-sm text-muted-foreground">This collection appears to be empty</p>
        </div>
      </Card>
    </div>

    <template #footer>
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 sm:gap-3">
        <div class="hidden sm:flex items-center gap-4">
          <div class="text-sm text-muted-foreground font-medium">
            <span class="text-foreground font-bold">{{ movies.length }}</span> 
            {{ movies.length === 1 ? 'movie' : 'movies' }}
          </div>
          <div v-if="movies.length > 0" class="flex items-center gap-2 text-xs text-muted-foreground">
            <span>•</span>
            <span>{{ getTotalRuntime() }} runtime</span>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <Button 
            variant="secondary" 
            @click="handleClose"
            class="flex-1 sm:flex-initial touch-manipulation"
            size="sm"
          >
            Close
          </Button>
          <Button 
            variant="primary" 
            @click="handleSyncCollection" 
            :disabled="isSyncing || movies.length === 0"
            :loading="isSyncing"
            class="flex-1 sm:flex-initial bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 touch-manipulation"
            size="sm"
          >
            <RefreshCwIcon v-if="!isSyncing" :size="14" />
            <span class="ml-2">{{ isSyncing ? 'Syncing...' : 'Sync' }}</span>
          </Button>
        </div>
      </div>
    </template>
  </Modal>

  <!-- Movie Details Modal -->
  <MovieDetailsModal
    v-model="showMovieDetails"
    :movie="selectedMovie"
  />
</template>

<script setup lang="ts">
import {
  Film as FilmIcon,
  Star as StarIcon,
  Users as UsersIcon,
  RefreshCw as RefreshCwIcon,
  AlertCircle as AlertCircleIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
} from 'lucide-vue-next'
import Modal from '~/components/ui/Modal.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import LoadingSpinner from '~/components/ui/LoadingSpinner.vue'
import CollectionMovieCard from '~/components/collections/CollectionMovieCard.vue'
import MovieDetailsModal from '~/components/collections/MovieDetailsModal.vue'
import { useApiService } from '~/composables/useApiService'
import { useToast } from '~/composables/useToast'
import { useRouter } from 'vue-router'
import type { Collection, CollectionMovie } from '~/types'

interface Props {
  modelValue: boolean
  collection: Collection | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const api = useApiService()
const { showSuccess, showError } = useToast()
const router = useRouter()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isLoading = ref(false)
const error = ref<string | null>(null)
const movies = ref<CollectionMovie[]>([])
const isSyncing = ref(false)
const showMovieDetails = ref(false)
const selectedMovie = ref<CollectionMovie | null>(null)

// Watch for modal open to load movies
watch(isOpen, (open) => {
  if (open && props.collection) {
    loadMovies()
  } else {
    // Reset state when closing
    movies.value = []
    error.value = null
    selectedMovie.value = null
    showMovieDetails.value = false
  }
})

const loadMovies = async () => {
  if (!props.collection) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const response = await api.getCollectionMovies(props.collection.franchise)
    movies.value = response.movies || []
  } catch (err: any) {
    error.value = err.message || 'Failed to load collection movies'
    console.error('Error loading collection movies:', err)
  } finally {
    isLoading.value = false
  }
}

const handleClose = () => {
  emit('close')
}

const formatRating = (rating: number) => {
  return rating.toFixed(1)
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

const calculateAverageRating = () => {
  if (movies.value.length === 0) return 'N/A'
  const ratings = movies.value.filter(m => m.rating && m.rating > 0).map(m => m.rating)
  if (ratings.length === 0) return 'N/A'
  const avg = ratings.reduce((sum, r) => sum + r, 0) / ratings.length
  return avg.toFixed(1)
}

const getYearSpan = () => {
  if (movies.value.length === 0) return 'N/A'
  const years = movies.value
    .map(m => m.releaseDate ? new Date(m.releaseDate).getFullYear() : 0)
    .filter(y => y > 0)
  if (years.length === 0) return 'N/A'
  const min = Math.min(...years)
  const max = Math.max(...years)
  if (min === max) return min.toString()
  return `${min}-${max}`
}

const getTotalRuntime = () => {
  const total = movies.value.reduce((sum, m) => sum + (m.runtime || 0), 0)
  if (total === 0) return 'N/A'
  const hours = Math.floor(total / 60)
  const mins = total % 60
  return `${hours}h ${mins}m`
}

const openMovieDetails = (movie: CollectionMovie) => {
  selectedMovie.value = movie
  showMovieDetails.value = true
}

const handleSyncCollection = async () => {
  if (!props.collection || isSyncing.value) return
  
  isSyncing.value = true
  
  try {
    await api.triggerSingleListSync('collections', props.collection.franchise)
    showSuccess('Sync Started', `Syncing ${props.collection.franchise} collection...`)
    
    // Close modal and redirect to logs
    setTimeout(() => {
      handleClose()
      router.push('/logs')
    }, 100)
  } catch (err: any) {
    showError('Sync Failed', err.message || 'Failed to sync collection')
  } finally {
    isSyncing.value = false
  }
}
</script>

