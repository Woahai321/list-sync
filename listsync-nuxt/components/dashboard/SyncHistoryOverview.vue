<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <!-- Total Syncs Card -->
    <Card
      variant="hover"
      @click="$router.push('/sync-history')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Total Syncs</p>
          <p class="text-3xl font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="stats.total_sessions" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            All time
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/card:from-purple-500/30 group-hover/card:to-purple-600/30 transition-all duration-300">
          <component :is="HistoryIcon" :size="28" class="text-purple-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Recent Syncs (7d) Card -->
    <Card
      variant="hover"
      @click="$router.push('/sync-history')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Last 7 Days</p>
          <p class="text-3xl font-bold text-blue-400 tabular-nums">
            <AnimatedCounter :value="stats.recent_stats.last_7d" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Recent activity
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-600/20 group-hover/card:from-blue-500/30 group-hover/card:to-cyan-600/30 transition-all duration-300">
          <component :is="CalendarIcon" :size="28" class="text-blue-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Success Rate Card -->
    <Card
      variant="hover"
      @click="$router.push('/sync-history')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Success Rate</p>
          <p class="text-3xl font-bold text-green-400 tabular-nums">
            {{ Math.round(stats.success_rate) }}%
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Sync reliability
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-600/20 group-hover/card:from-green-500/30 group-hover/card:to-emerald-600/30 transition-all duration-300">
          <component :is="CheckCircleIcon" :size="28" class="text-green-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Average Per Item Processing Time Card -->
    <Card
      variant="hover"
      @click="$router.push('/sync-history')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Avg Per Item</p>
          <p class="text-2xl font-bold text-orange-400 tabular-nums">
            {{ formatDuration(stats.avg_duration_seconds) }}
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Processing time
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-orange-500/20 to-amber-600/20 group-hover/card:from-orange-500/30 group-hover/card:to-amber-600/30 transition-all duration-300">
          <component :is="ClockIcon" :size="28" class="text-orange-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Sync Breakdown (Full Width) -->
    <Card variant="default" class="md:col-span-2 lg:col-span-4 overflow-hidden relative">
      <!-- Subtle animated background -->
      <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-50" />
      
      <div class="relative flex flex-col md:flex-row items-center justify-between gap-4 md:gap-6 py-2 px-2 md:px-0">
        <!-- Sync Type Breakdown -->
        <div class="flex flex-col md:flex-row items-center gap-4 md:gap-8 w-full md:w-auto">
          <div class="relative flex-shrink-0">
            <!-- SVG Donut Chart -->
            <svg width="140" height="140" viewBox="0 0 160 160" class="transform -rotate-90">
              <!-- Background circle -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="rgba(255, 255, 255, 0.05)"
                stroke-width="20"
              />
              
              <!-- Full syncs segment (purple) -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#8b5cf6"
                stroke-width="20"
                :stroke-dasharray="`${fullSyncCircumference} ${totalCircumference}`"
                :stroke-dashoffset="0"
                class="transition-all duration-500"
              />
              
              <!-- Single syncs segment (blue) -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#3b82f6"
                stroke-width="20"
                :stroke-dasharray="`${singleSyncCircumference} ${totalCircumference}`"
                :stroke-dashoffset="`${-fullSyncCircumference}`"
                class="transition-all duration-500"
              />
            </svg>
            
            <!-- Center text -->
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <p class="text-3xl md:text-4xl font-bold text-foreground">{{ Math.round(avgItemsPerSync) }}</p>
              <p class="text-xs text-muted-foreground mt-1">Avg Items/Sync</p>
            </div>
          </div>
          
          <!-- Breakdown Legend -->
          <div class="space-y-2 md:space-y-3 w-full md:w-auto">
            <div class="flex items-center gap-2 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-purple-500"></div>
              <span class="font-medium text-foreground min-w-[70px] md:min-w-[100px]">Full Syncs</span>
              <span class="text-muted-foreground">{{ formatNumber(stats.full_syncs) }}</span>
              <span class="text-muted-foreground ml-auto">({{ fullSyncPercentage }}%)</span>
            </div>
            <div class="flex items-center gap-2 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-blue-500"></div>
              <span class="font-medium text-foreground min-w-[70px] md:min-w-[100px]">Single Syncs</span>
              <span class="text-muted-foreground">{{ formatNumber(stats.single_syncs) }}</span>
              <span class="text-muted-foreground ml-auto">({{ singleSyncPercentage }}%)</span>
            </div>
            <div class="flex items-center gap-2 pt-2 border-t border-border/50 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-indigo-500"></div>
              <span class="font-bold text-foreground min-w-[70px] md:min-w-[100px]">Total Items</span>
              <span class="font-bold text-foreground">{{ formatNumber(stats.total_items_processed) }}</span>
            </div>
          </div>
        </div>

        <!-- Recent Activity Summary -->
        <div class="flex-1 grid grid-cols-2 gap-4 md:gap-6 max-w-md w-full md:w-auto">
          <div class="text-center p-4 md:p-6 rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-600/10 border border-green-500/20 hover:border-green-500/40 transition-all">
            <p class="text-xs md:text-sm text-muted-foreground mb-1 md:mb-2">Last 24h</p>
            <p class="text-2xl md:text-3xl font-bold text-green-400 tabular-nums">
              <AnimatedCounter :value="stats.recent_stats.last_24h" />
            </p>
          </div>
          
          <div class="text-center p-4 md:p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-cyan-600/10 border border-blue-500/20 hover:border-blue-500/40 transition-all">
            <p class="text-xs md:text-sm text-muted-foreground mb-1 md:mb-2">Last 30d</p>
            <p class="text-2xl md:text-3xl font-bold text-blue-400 tabular-nums">
              <AnimatedCounter :value="stats.recent_stats.last_30d" />
            </p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  History as HistoryIcon,
  Calendar as CalendarIcon,
  CheckCircle2 as CheckCircleIcon,
  Clock as ClockIcon,
} from 'lucide-vue-next'
import type { SyncHistoryStats } from '~/types'

interface Props {
  stats: SyncHistoryStats
}

const props = defineProps<Props>()

// Format number with commas
const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Format duration
const formatDuration = (seconds: number | null): string => {
  if (!seconds) return 'N/A'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

// Calculate percentages
const fullSyncPercentage = computed(() => 
  Math.round((props.stats.full_syncs / props.stats.total_sessions) * 100)
)
const singleSyncPercentage = computed(() => 
  Math.round((props.stats.single_syncs / props.stats.total_sessions) * 100)
)

// Calculate circumference segments for donut chart
const radius = 70
const totalCircumference = 2 * Math.PI * radius

const fullSyncCircumference = computed(() => 
  (props.stats.full_syncs / props.stats.total_sessions) * totalCircumference
)
const singleSyncCircumference = computed(() => 
  (props.stats.single_syncs / props.stats.total_sessions) * totalCircumference
)

// Average items per sync
const avgItemsPerSync = computed(() => 
  Math.round(props.stats.avg_items_per_sync)
)
</script>
