<template>
  <div class="space-y-6">
    <!-- Search & Filters -->
    <Card class="glass-card">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Search -->
        <div>
          <Input
            v-model="searchQuery"
            placeholder="Search successful items..."
            :icon="SearchIcon"
            @input="debouncedSearch"
          />
        </div>

        <!-- Media Type Filter -->
        <div>
          <Select
            v-model="mediaTypeFilter"
            :options="mediaTypeOptions"
            @update:model-value="fetchItems"
          />
        </div>
      </div>
    </Card>

    <!-- Stats Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card class="glass-card">
        <div class="flex items-center gap-3">
          <div class="p-3 rounded-lg bg-success/10">
            <CheckCircleIcon class="w-5 h-5 text-success" />
          </div>
          <div>
            <div class="text-sm text-muted-foreground">Total Success</div>
            <div class="text-2xl font-bold">{{ totalItems }}</div>
          </div>
        </div>
      </Card>

      <Card class="glass-card">
        <div class="flex items-center gap-3">
          <div class="p-3 rounded-lg bg-primary/10">
            <FilmIcon class="w-5 h-5 text-primary" />
          </div>
          <div>
            <div class="text-sm text-muted-foreground">Movies</div>
            <div class="text-2xl font-bold">{{ movieCount }}</div>
          </div>
        </div>
      </Card>

      <Card class="glass-card">
        <div class="flex items-center gap-3">
          <div class="p-3 rounded-lg bg-accent/10">
            <TvIcon class="w-5 h-5 text-accent" />
          </div>
          <div>
            <div class="text-sm text-muted-foreground">TV Shows</div>
            <div class="text-2xl font-bold">{{ tvCount }}</div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading successful items..." />
    </div>

    <!-- Items Grid -->
    <template v-else-if="items.length > 0">
      <div class="grid grid-cols-1 gap-4">
        <Card
          v-for="item in items"
          :key="item.id"
          class="glass-card hover:border-success/30 transition-colors"
        >
          <div class="flex items-start gap-4">
            <!-- Poster/Icon -->
            <div class="w-16 h-24 bg-muted/20 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden relative">
              <img
                v-if="item.poster_url"
                :src="item.poster_url"
                :alt="item.title"
                class="w-full h-full object-cover"
              />
              <component
                v-else
                :is="item.media_type === 'movie' ? FilmIcon : TvIcon"
                class="w-8 h-8 text-muted-foreground"
              />
              <!-- Success Badge -->
              <div class="absolute top-1 right-1 bg-success rounded-full p-1">
                <CheckCircleIcon class="w-3 h-3 text-white" />
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <h4 class="font-semibold text-foreground mb-2">
                    {{ item.title }}
                  </h4>
                  <div class="flex flex-wrap items-center gap-2">
                    <Badge :variant="item.media_type === 'movie' ? 'primary' : 'accent'">
                      {{ item.media_type }}
                    </Badge>
                    <Badge v-if="item.year" variant="default">
                      {{ item.year }}
                    </Badge>
                    <Badge variant="success">
                      <CheckCircleIcon class="w-3 h-3 mr-1" />
                      Success
                    </Badge>
                    <span class="text-xs text-muted-foreground flex items-center gap-1">
                      <ClockIcon class="w-3 h-3" />
                      {{ formatRelativeTime(item.timestamp || item.processed_at) }}
                    </span>
                  </div>
                </div>

                <!-- View in Overseerr -->
                <Button
                  v-if="item.overseerr_url"
                  variant="ghost"
                  size="sm"
                  @click="openOverseerr(item.overseerr_url)"
                >
                  <ExternalLinkIcon class="w-4 h-4" />
                </Button>
              </div>

              <!-- Success Info -->
              <div class="mt-3 pt-3 border-t border-border/50">
                <div class="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                  <span v-if="item.match_score" class="flex items-center gap-1">
                    <TrendingUpIcon class="w-3 h-3" />
                    Match: {{ item.match_score }}%
                  </span>
                  <span v-if="item.list_name" class="flex items-center gap-1">
                    <ListIcon class="w-3 h-3" />
                    From: {{ item.list_name }}
                  </span>
                  <span v-if="item.source" class="flex items-center gap-1">
                    <DatabaseIcon class="w-3 h-3" />
                    Source: {{ item.source }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Pagination -->
      <Pagination
        :current-page="currentPage"
        :total-items="totalItems"
        :per-page="perPage"
        @update:current-page="currentPage = $event; fetchItems()"
        @update:per-page="perPage = $event; fetchItems()"
      />
    </template>

    <!-- Empty State -->
    <EmptyState
      v-else
      :icon="CheckCircleIcon"
      title="No successful items"
      description="No items have been successfully processed yet"
    />
  </div>
</template>

<script setup lang="ts">
import {
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  Clock as ClockIcon,
  ExternalLink as ExternalLinkIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  List as ListIcon,
  Database as DatabaseIcon,
  TrendingUp as TrendingUpIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow } from 'date-fns'
import { useDebounceFn } from '@vueuse/core'

interface SuccessItem {
  id: string
  title: string
  media_type: string
  year?: number
  poster_url?: string
  timestamp?: string
  processed_at?: string
  match_score?: number
  list_name?: string
  source?: string
  overseerr_url?: string
}

// State
const loading = ref(true)
const items = ref<SuccessItem[]>([])
const currentPage = ref(1)
const perPage = ref(25)
const totalItems = ref(0)
const searchQuery = ref('')
const mediaTypeFilter = ref('all')

// Filter options
const mediaTypeOptions = [
  { label: 'All Types', value: 'all' },
  { label: 'Movies', value: 'movie' },
  { label: 'TV Shows', value: 'tv' },
]

// State for total counts from API
const movieCount = ref(0)
const tvCount = ref(0)

// Fetch items
const fetchItems = async () => {
  loading.value = true
  try {
    const api = useApiService()
    const response: any = await api.getSuccessfulItems(currentPage.value, perPage.value)
    
    items.value = response.items || []
    // Use filtered_count for accurate count after filters, or total_count for all items
    totalItems.value = response.filtered_count || response.total_count || response.total || 0
    
    // Get media type counts from API response
    movieCount.value = response.movie_count || 0
    tvCount.value = response.tv_count || 0
    
    console.log(`Loaded ${items.value.length} successful items, total: ${totalItems.value}, movies: ${movieCount.value}, TV: ${tvCount.value}`)
  } catch (error) {
    console.error('Error fetching successful items:', error)
    items.value = []
    totalItems.value = 0
  } finally {
    loading.value = false
  }
}

// Debounced search
const debouncedSearch = useDebounceFn(() => {
  currentPage.value = 1
  fetchItems()
}, 500)

// Open Overseerr
const openOverseerr = (url: string) => {
  window.open(url, '_blank')
}

// Format relative time
const formatRelativeTime = (timestamp: string | undefined) => {
  if (!timestamp) return 'Unknown'
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return 'Unknown'
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Fetch on mount
onMounted(() => {
  fetchItems()
})
</script>

