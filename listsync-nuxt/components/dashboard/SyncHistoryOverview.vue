<template>
  <Card variant="default" class="overflow-hidden relative cursor-pointer hover:border-purple-500/40 transition-all group/card" @click="$router.push('/sync-history')">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-3">
      <!-- Top Row: Main Metrics -->
      <div class="grid grid-cols-3 gap-2">
        <!-- Total Syncs -->
        <div class="p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="HistoryIcon" :size="14" class="text-purple-400" />
            <span class="text-[9px] font-bold text-purple-300 uppercase tracking-wide">Total</span>
          </div>
          <p class="text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            <AnimatedCounter :value="stats.total_sessions" />
          </p>
          <p class="text-[10px] text-purple-300/70 font-medium">Sync Sessions</p>
        </div>

        <!-- Success Rate -->
        <div class="p-3 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-400/10 border border-purple-400/30">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="CheckCircleIcon" :size="14" class="text-purple-300" />
            <span class="text-[9px] font-bold text-purple-200 uppercase tracking-wide">Success</span>
          </div>
          <p class="text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            {{ Math.round(stats.success_rate) }}%
          </p>
          <p class="text-[10px] text-purple-300/70 font-medium">Success Rate</p>
        </div>

        <!-- Avg Items -->
        <div class="p-3 rounded-lg bg-gradient-to-br from-purple-400/20 to-purple-300/10 border border-purple-300/30">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="LayersIcon" :size="14" class="text-purple-200" />
            <span class="text-[9px] font-bold text-purple-100 uppercase tracking-wide">Avg</span>
          </div>
          <p class="text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            {{ Math.round(avgItemsPerSync) }}
          </p>
          <p class="text-[10px] text-purple-300/70 font-medium">Items/Sync</p>
        </div>
      </div>

      <!-- Recent Activity & Stats -->
      <div class="grid grid-cols-3 gap-2">
        <!-- 24h Activity -->
        <div class="p-2 rounded-lg bg-purple-600/10 border border-purple-600/20">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">24h</span>
          </div>
          <p class="text-lg font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="stats.recent_stats?.last_24h ?? 0" />
          </p>
        </div>

        <!-- 7d Activity -->
        <div class="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">7 days</span>
          </div>
          <p class="text-lg font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="stats.recent_stats?.last_7d ?? 0" />
          </p>
        </div>

        <!-- 30d Activity -->
        <div class="p-2 rounded-lg bg-purple-400/10 border border-purple-400/20">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-300"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">30 days</span>
          </div>
          <p class="text-lg font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="stats.recent_stats?.last_30d ?? 0" />
          </p>
        </div>
      </div>

      <!-- Bottom Stats Grid -->
      <div class="grid grid-cols-3 gap-2">
        <!-- Full Syncs -->
        <div class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">Full</span>
          </div>
          <p class="text-base font-bold text-foreground tabular-nums">
            {{ formatNumber(stats.full_syncs) }}
          </p>
        </div>

        <!-- Single Syncs -->
        <div class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-300"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">Single</span>
          </div>
          <p class="text-base font-bold text-foreground tabular-nums">
            {{ formatNumber(stats.single_syncs) }}
          </p>
        </div>

        <!-- Avg Duration -->
        <div class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-200"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">Time</span>
          </div>
          <p class="text-base font-bold text-foreground tabular-nums">
            {{ formatDuration(stats.avg_duration_seconds) }}
          </p>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  History as HistoryIcon,
  CheckCircle2 as CheckCircleIcon,
  Layers as LayersIcon,
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

// Calculate circumference segments for donut chart (smaller radius for compact view)
const radius = 40
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
