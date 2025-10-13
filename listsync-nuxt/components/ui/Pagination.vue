<template>
  <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
    <!-- Items Info -->
    <div class="text-sm text-muted-foreground">
      Showing <span class="font-medium text-foreground">{{ itemsStart }}</span> to 
      <span class="font-medium text-foreground">{{ itemsEnd }}</span> of 
      <span class="font-medium text-foreground">{{ totalItems }}</span> items
    </div>

    <!-- Pagination Controls -->
    <div class="flex items-center gap-2">
      <!-- Previous Button -->
      <Button
        variant="ghost"
        size="sm"
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        <ChevronLeftIcon class="w-4 h-4" />
        Previous
      </Button>

      <!-- Page Numbers -->
      <div class="flex items-center gap-1">
        <!-- First Page -->
        <button
          v-if="showFirstPage"
          class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
          :class="[
            currentPage === 1
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted/50 text-foreground'
          ]"
          @click="goToPage(1)"
        >
          1
        </button>

        <!-- First Ellipsis -->
        <span v-if="showFirstEllipsis" class="px-2 text-muted-foreground">
          ...
        </span>

        <!-- Middle Pages -->
        <button
          v-for="page in visiblePages"
          :key="page"
          class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
          :class="[
            currentPage === page
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted/50 text-foreground'
          ]"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>

        <!-- Last Ellipsis -->
        <span v-if="showLastEllipsis" class="px-2 text-muted-foreground">
          ...
        </span>

        <!-- Last Page -->
        <button
          v-if="showLastPage"
          class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
          :class="[
            currentPage === totalPages
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted/50 text-foreground'
          ]"
          @click="goToPage(totalPages)"
        >
          {{ totalPages }}
        </button>
      </div>

      <!-- Next Button -->
      <Button
        variant="ghost"
        size="sm"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        Next
        <ChevronRightIcon class="w-4 h-4" />
      </Button>
    </div>

    <!-- Items Per Page -->
    <div class="flex items-center gap-2">
      <span class="text-sm text-muted-foreground whitespace-nowrap">
        Per page:
      </span>
      <Select
        :model-value="perPage"
        :options="perPageOptions"
        @update:model-value="changePerPage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from 'lucide-vue-next'

interface Props {
  currentPage: number
  totalItems: number
  perPage: number
  maxVisiblePages?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxVisiblePages: 5,
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
  'update:perPage': [perPage: number]
}>()

// Per page options
const perPageOptions = [
  { label: '10', value: 10 },
  { label: '25', value: 25 },
  { label: '50', value: 50 },
  { label: '100', value: 100 },
]

// Calculate total pages
const totalPages = computed(() => {
  return Math.ceil(props.totalItems / props.perPage)
})

// Calculate items range
const itemsStart = computed(() => {
  if (props.totalItems === 0) return 0
  return (props.currentPage - 1) * props.perPage + 1
})

const itemsEnd = computed(() => {
  const end = props.currentPage * props.perPage
  return end > props.totalItems ? props.totalItems : end
})

// Calculate visible page numbers
const visiblePages = computed(() => {
  const pages: number[] = []
  const total = totalPages.value
  const current = props.currentPage
  const max = props.maxVisiblePages

  let start = Math.max(2, current - Math.floor(max / 2))
  let end = Math.min(total - 1, start + max - 1)

  // Adjust start if we're near the end
  if (end - start < max - 1) {
    start = Math.max(2, end - max + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

// Show/hide page elements
const showFirstPage = computed(() => totalPages.value > 0)
const showLastPage = computed(() => totalPages.value > 1)
const showFirstEllipsis = computed(() => visiblePages.value[0] > 2)
const showLastEllipsis = computed(() => {
  const lastVisible = visiblePages.value[visiblePages.value.length - 1]
  return lastVisible < totalPages.value - 1
})

// Navigation handlers
const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  emit('update:currentPage', page)
}

const changePerPage = (newPerPage: number) => {
  emit('update:perPage', newPerPage)
  // Reset to page 1 when changing per page
  emit('update:currentPage', 1)
}
</script>

