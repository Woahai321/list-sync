<template>
  <Card>
    <div class="space-y-4">
      <!-- Search and Sort Row -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Search -->
        <div class="md:col-span-2">
          <Input
            v-model="searchTerm"
            placeholder="Search lists by name or ID..."
            :icon="SearchIcon"
            clearable
            @update:model-value="handleSearch"
          />
        </div>

        <!-- Sort -->
        <Select
          v-model="sortBy"
          :options="sortOptions"
          @update:model-value="handleSort"
        />
      </div>

      <!-- Filter Chips Row -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm text-muted-foreground">Filter by source:</span>
        
        <button
          v-for="source in sources"
          :key="source.value"
          :class="getSourceChipClass(source.value)"
          @click="handleSourceFilter(source.value)"
        >
          <component v-if="source.icon" :is="source.icon" :size="14" />
          {{ source.label }}
          <span v-if="source.value !== 'all'" class="ml-1 text-xs opacity-70">
            ({{ getSourceCount(source.value) }})
          </span>
        </button>

        <!-- Clear Filters -->
        <button
          v-if="listsStore.hasActiveFilters"
          class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30 transition-colors"
          @click="handleClearFilters"
        >
          <component :is="XIcon" :size="14" />
          Clear Filters
        </button>
      </div>

      <!-- Active Filters Summary -->
      <div v-if="listsStore.hasActiveFilters" class="flex items-center gap-2 text-sm text-muted-foreground">
        <component :is="InfoIcon" :size="16" />
        <span>
          Showing {{ listsStore.filteredLists.length }} of {{ listsStore.totalLists }} lists
        </span>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Search as SearchIcon,
  X as XIcon,
  Info as InfoIcon,
  List as ListIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  Database as DatabaseIcon,
} from 'lucide-vue-next'

const listsStore = useListsStore()

// Local state for v-model
const searchTerm = ref(listsStore.searchTerm)
const sortBy = ref(listsStore.sortBy)

// Sort options
const sortOptions = [
  { label: 'Last Synced', value: 'last_synced' },
  { label: 'Name', value: 'name' },
  { label: 'Item Count', value: 'item_count' },
]

// Source options
const sources = [
  { label: 'All Sources', value: 'all', icon: ListIcon },
  { label: 'IMDb', value: 'imdb', icon: FilmIcon },
  { label: 'Trakt', value: 'trakt', icon: TvIcon },
  { label: 'Letterboxd', value: 'letterboxd', icon: FilmIcon },
  { label: 'MDBList', value: 'mdblist', icon: DatabaseIcon },
  { label: 'Steven Lu', value: 'stevenlu', icon: DatabaseIcon },
]

// Handlers
const handleSearch = (value: string) => {
  listsStore.setSearchTerm(value)
}

const handleSort = (value: string) => {
  listsStore.setSortBy(value as 'name' | 'last_synced' | 'item_count')
}

const handleSourceFilter = (source: string) => {
  listsStore.setSourceFilter(source)
}

const handleClearFilters = () => {
  searchTerm.value = ''
  sortBy.value = 'last_synced'
  listsStore.clearFilters()
}

// Get source count
const getSourceCount = (source: string) => {
  if (source === 'all') return listsStore.totalLists
  
  return listsStore.lists.filter(list => 
    list.list_type.toLowerCase().includes(source.toLowerCase())
  ).length
}

// Get chip class based on active state
const getSourceChipClass = (source: string) => {
  const isActive = listsStore.sourceFilter === source
  
  const baseClasses = [
    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
    'border transition-all duration-200',
  ]

  if (isActive) {
    return [
      ...baseClasses,
      'bg-purple-500/20 text-purple-300 border-purple-500/40',
      'shadow-sm shadow-purple-500/20',
    ].join(' ')
  }

  return [
    ...baseClasses,
    'bg-black/20 text-muted-foreground border-border',
    'hover:bg-white/5 hover:text-foreground hover:border-purple-500/30',
  ].join(' ')
}

// Sync local state with store on mount
onMounted(() => {
  searchTerm.value = listsStore.searchTerm
  sortBy.value = listsStore.sortBy
})
</script>

