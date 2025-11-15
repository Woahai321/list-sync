<template>
  <div class="space-y-4">
    <!-- Search & Filters -->
    <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- Search -->
        <div>
          <Input
            v-model="searchQuery"
            placeholder="Search by title..."
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

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading processed items..." />
    </div>

    <!-- Items Grid -->
    <template v-else-if="items.length > 0">
      <div class="grid grid-cols-1 gap-3">
        <Card
          v-for="item in items"
          :key="item.id"
          class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300"
        >
          <div class="flex items-start gap-4">
            <!-- Poster/Icon -->
            <div class="w-16 h-24 bg-muted/20 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
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
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <h4 class="font-semibold text-foreground mb-2">
                    {{ item.title }}
                  </h4>
                  <div class="flex flex-wrap items-center gap-2 mb-2">
                    <Badge :variant="item.media_type === 'movie' ? 'primary' : 'accent'">
                      {{ item.media_type }}
                    </Badge>
                    <Badge v-if="item.year" variant="default">
                      {{ item.year }}
                    </Badge>
                    
                    <!-- List Source Link -->
                    <NuxtLink
                      v-if="item.list_name"
                      to="/lists"
                      class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors group"
                    >
                      <ListIcon class="w-3 h-3 group-hover:scale-110 transition-transform" />
                      {{ formatListSource(item.list_name, item.source) }}
                    </NuxtLink>
                    
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
      :icon="DatabaseIcon"
      title="No processed items"
      description="No items have been processed yet"
    />
  </div>
</template>

<script setup lang="ts">
import {
  Database as DatabaseIcon,
  Search as SearchIcon,
  Clock as ClockIcon,
  Info as InfoIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  List as ListIcon,
  ExternalLink as ExternalLinkIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow } from 'date-fns'
import { useDebounceFn } from '@vueuse/core'

interface ProcessedItem {
  id: string
  title: string
  media_type: string
  year?: number
  poster_url?: string
  timestamp?: string
  processed_at?: string
  source?: string
  list_name?: string
  overseerr_url?: string
}

// State
const loading = ref(true)
const items = ref<ProcessedItem[]>([])
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

// Fetch items
const fetchItems = async () => {
  loading.value = true
  try {
    const api = useApiService()
    const response = await api.getProcessedItems(currentPage.value, perPage.value)
    
    items.value = response.items || []
    totalItems.value = response.total || 0
  } catch (error) {
    console.error('Error fetching processed items:', error)
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

// View details
const viewDetails = (item: ProcessedItem) => {
  console.log('View details:', item)
  // Implement details modal
}

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

// Format list source
const formatListSource = (listName: string | undefined, source: string | undefined) => {
  if (!listName && !source) return 'Unknown List'
  
  const sourcePrefix = source ? source.toUpperCase() : ''
  const cleanName = listName ? listName.replace(/_/g, ' ').replace(/-/g, ' ') : ''
  
  if (sourcePrefix && cleanName) {
    return `${sourcePrefix}: ${cleanName}`
  }
  
  return cleanName || sourcePrefix || 'Unknown List'
}

// Fetch on mount
onMounted(() => {
  fetchItems()
})
</script>

