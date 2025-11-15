<template>
  <Card variant="default" class="overflow-hidden relative group/card">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-3">
      <!-- Responsive Main Stats Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
        <!-- Total Processed (Purple - Neutral) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/40 hover:border-purple-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="LayersIcon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-400 group-hover:scale-110 transition-transform flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300 uppercase tracking-wide">Total</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            <AnimatedCounter :value="stats.total_processed" />
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/70 font-medium">Processed</p>
        </div>

        <!-- Successful (Green - Positive) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-green-500/40 group-hover:border-green-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="CheckCircle2Icon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-300/80 group-hover:text-green-400/40 transition-colors group-hover:scale-110 transition-transform flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300/70 uppercase tracking-wide">{{ Math.round(successPercentage) }}%</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            <AnimatedCounter :value="stats.successful_items" />
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/50 font-medium">Successful</p>
        </div>

        <!-- Available (Green - Positive) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-green-500/40 group-hover:border-green-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="CheckIcon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-300/80 group-hover:text-green-400/35 transition-colors group-hover:scale-110 transition-transform flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300/70 uppercase tracking-wide">Avail</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            {{ formatNumber(availableItems) }}
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/50 font-medium">Available</p>
        </div>

        <!-- Requested (Blue - Info/Neutral) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-blue-500/40 group-hover:border-blue-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="SendIcon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-300/80 group-hover:text-blue-400/35 transition-colors group-hover:scale-110 transition-transform flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300/70 uppercase tracking-wide">{{ Math.round(requestedPercentage) }}%</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            <AnimatedCounter :value="stats.total_requested" />
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/50 font-medium">Requested</p>
        </div>

        <!-- Errors (Red - Negative) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-red-500/40 group-hover:border-red-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="AlertCircleIcon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-300/80 group-hover:text-red-400/40 transition-colors group-hover:scale-110 transition-transform flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300/70 uppercase tracking-wide">{{ Math.round(errorsPercentage) }}%</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            <AnimatedCounter :value="stats.total_errors" />
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/50 font-medium">Errors</p>
        </div>

        <!-- Success Rate (Green - Positive) -->
        <div 
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-green-500/40 group-hover:border-green-400/50 transition-all cursor-pointer group touch-manipulation min-h-[80px] sm:min-h-0"
          @click="$router.push('/items')"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="TrendingUpIcon" :size="14" class="sm:w-3.5 sm:h-3.5 text-purple-300/80 flex-shrink-0" />
            <span class="text-[10px] sm:text-[9px] font-bold text-purple-300/70 uppercase tracking-wide">Rate</span>
          </div>
          <p class="text-xl sm:text-2xl font-bold text-foreground tabular-nums leading-none mb-0.5">
            {{ Math.round(stats.success_rate) }}%
          </p>
          <p class="text-[11px] sm:text-[10px] text-purple-300/50 font-medium">Success</p>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Layers as LayersIcon,
  CheckCircle2 as CheckCircle2Icon,
  Check as CheckIcon,
  Send as SendIcon,
  AlertCircle as AlertCircleIcon,
  TrendingUp as TrendingUpIcon,
} from 'lucide-vue-next'
import type { SyncStats } from '~/types'

interface Props {
  stats: SyncStats
}

const props = defineProps<Props>()

// Format number with commas
const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Calculate percentages
const successPercentage = computed(() => 
  Math.round((props.stats.successful_items / props.stats.total_processed) * 100)
)
const requestedPercentage = computed(() => 
  Math.round((props.stats.total_requested / props.stats.total_processed) * 100)
)
const errorsPercentage = computed(() => 
  Math.round((props.stats.total_errors / props.stats.total_processed) * 100)
)

// Calculate available items (successful but not requested)
const availableItems = computed(() => 
  props.stats.successful_items - props.stats.total_requested
)
</script>

