<template>
  <Card variant="default" class="overflow-hidden relative group/card">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-5">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <component :is="PlaySquareIcon" :size="18" class="text-purple-400" />
          <span class="text-[10px] font-semibold text-purple-300 uppercase tracking-wide">Media Distribution</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="space-y-4">
        <div class="animate-pulse space-y-3">
          <div class="h-20 bg-purple-500/10 rounded-lg"></div>
          <div class="h-20 bg-purple-500/10 rounded-lg"></div>
        </div>
      </div>

      <!-- Content -->
      <div v-else class="space-y-4">
        <!-- Movie Count -->
        <div class="p-5 rounded-xl bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <component :is="FilmIcon" :size="18" class="text-purple-300" />
              <span class="text-xs font-medium text-muted-foreground">Movies</span>
            </div>
            <div class="px-2 py-0.5 rounded-full bg-purple-400/20">
              <span class="text-[10px] font-semibold text-purple-200">{{ moviePercentage }}%</span>
            </div>
          </div>
          <p class="text-4xl font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="movieCount" />
          </p>
        </div>

        <!-- TV Shows Count -->
        <div class="p-5 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-400/10 border border-purple-400/30">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <component :is="TvIcon" :size="18" class="text-purple-200" />
              <span class="text-xs font-medium text-muted-foreground">TV Shows</span>
            </div>
            <div class="px-2 py-0.5 rounded-full bg-purple-300/20">
              <span class="text-[10px] font-semibold text-purple-100">{{ tvPercentage }}%</span>
            </div>
          </div>
          <p class="text-4xl font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="tvCount" />
          </p>
        </div>

        <!-- Distribution Bar -->
        <div class="px-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-muted-foreground">Distribution</span>
            <span class="text-xs font-semibold text-purple-300">{{ totalCount }} Total</span>
          </div>
          <div class="relative h-3 bg-purple-950/30 rounded-full overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-purple-400/20" />
            <!-- Movies (left side) -->
            <div
              class="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-600 to-purple-500 rounded-full transition-all duration-1000 ease-out"
              :style="{ width: `${moviePercentage}%` }"
            />
            <!-- TV Shows (right side, calculated from remaining space) -->
            <div
              class="absolute inset-y-0 right-0 bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-1000 ease-out"
              :style="{ width: `${tvPercentage}%` }"
            />
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  PlaySquare as PlaySquareIcon,
  Film as FilmIcon,
  Tv as TvIcon,
} from 'lucide-vue-next'

interface Props {
  movieCount: number
  tvCount: number
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false
})

// Calculate percentages and totals
const totalCount = computed(() => props.movieCount + props.tvCount)

const moviePercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((props.movieCount / totalCount.value) * 100)
})

const tvPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((props.tvCount / totalCount.value) * 100)
})
</script>

