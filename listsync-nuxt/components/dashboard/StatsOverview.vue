<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <!-- Total Processed Card -->
    <Card
      variant="hover"
      @click="$router.push('/processed')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Total Processed</p>
          <p class="text-3xl font-bold text-foreground tabular-nums">
            <AnimatedCounter :value="stats.total_processed" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            After deduplication
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover/card:from-purple-500/30 group-hover/card:to-purple-600/30 transition-all duration-300">
          <component :is="LayersIcon" :size="28" class="text-purple-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Successful Items Card -->
    <Card
      variant="hover"
      @click="$router.push('/successful')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Successful</p>
          <p class="text-3xl font-bold text-green-400 tabular-nums">
            <AnimatedCounter :value="stats.successful_items" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Requested + Available
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-600/20 group-hover/card:from-green-500/30 group-hover/card:to-emerald-600/30 transition-all duration-300">
          <component :is="CheckCircle2Icon" :size="28" class="text-green-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Total Requested Card -->
    <Card
      variant="hover"
      @click="$router.push('/requested')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Requested</p>
          <p class="text-3xl font-bold text-blue-400 tabular-nums">
            <AnimatedCounter :value="stats.total_requested" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Sent to Overseerr
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-600/20 group-hover/card:from-blue-500/30 group-hover/card:to-cyan-600/30 transition-all duration-300">
          <component :is="SendIcon" :size="28" class="text-blue-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Errors Card -->
    <Card
      variant="hover"
      @click="$router.push('/failures')"
      class="cursor-pointer group/card"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-muted-foreground mb-1">Errors</p>
          <p class="text-3xl font-bold text-red-400 tabular-nums">
            <AnimatedCounter :value="stats.total_errors" />
          </p>
          <p class="text-xs text-muted-foreground mt-2">
            Not found + Errors
          </p>
        </div>
        <div class="flex-shrink-0 p-4 rounded-xl bg-gradient-to-br from-red-500/20 to-rose-600/20 group-hover/card:from-red-500/30 group-hover/card:to-rose-600/30 transition-all duration-300">
          <component :is="AlertCircleIcon" :size="28" class="text-red-400 group-hover/card:scale-110 transition-transform duration-300" />
        </div>
      </div>
    </Card>

    <!-- Success Rate Card (Full Width) -->
    <Card variant="default" class="md:col-span-2 lg:col-span-4 overflow-hidden relative">
      <!-- Subtle animated background -->
      <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-50" />
      
      <div class="relative flex flex-col md:flex-row items-center justify-between gap-4 md:gap-6 py-2 px-2 md:px-0">
        <!-- Segmented Donut Chart -->
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
              
              <!-- Available segment (green) -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#10b981"
                stroke-width="20"
                :stroke-dasharray="`${availableCircumference} ${totalCircumference}`"
                :stroke-dashoffset="0"
                class="transition-all duration-500"
              />
              
              <!-- Requested segment (blue) -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#3b82f6"
                stroke-width="20"
                :stroke-dasharray="`${requestedCircumference} ${totalCircumference}`"
                :stroke-dashoffset="`${-availableCircumference}`"
                class="transition-all duration-500"
              />
              
              <!-- Errors segment (red) -->
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#ef4444"
                stroke-width="20"
                :stroke-dasharray="`${errorsCircumference} ${totalCircumference}`"
                :stroke-dashoffset="`${-(availableCircumference + requestedCircumference)}`"
                class="transition-all duration-500"
              />
            </svg>
            
            <!-- Center text -->
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <p class="text-3xl md:text-4xl font-bold text-foreground">{{ Math.round(stats.success_rate) }}%</p>
              <p class="text-xs text-muted-foreground mt-1">Success Rate</p>
            </div>
          </div>
          
          <!-- Breakdown Legend -->
          <div class="space-y-2 md:space-y-3 w-full md:w-auto">
            <div class="flex items-center gap-2 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-green-500"></div>
              <span class="font-medium text-foreground min-w-[70px] md:min-w-[100px]">Available</span>
              <span class="text-muted-foreground">{{ formatNumber(availableItems) }}</span>
              <span class="text-muted-foreground ml-auto">({{ availablePercentage }}%)</span>
            </div>
            <div class="flex items-center gap-2 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-blue-500"></div>
              <span class="font-medium text-foreground min-w-[70px] md:min-w-[100px]">Requested</span>
              <span class="text-muted-foreground">{{ formatNumber(stats.total_requested) }}</span>
              <span class="text-muted-foreground ml-auto">({{ requestedPercentageChart }}%)</span>
            </div>
            <div class="flex items-center gap-2 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-red-500"></div>
              <span class="font-medium text-foreground min-w-[70px] md:min-w-[100px]">Errors</span>
              <span class="text-muted-foreground">{{ formatNumber(stats.total_errors) }}</span>
              <span class="text-muted-foreground ml-auto">({{ errorsPercentage }}%)</span>
            </div>
            <div class="flex items-center gap-2 pt-2 border-t border-border/50 text-xs md:text-sm">
              <div class="w-3 h-3 flex-shrink-0 rounded-full bg-purple-500"></div>
              <span class="font-bold text-foreground min-w-[70px] md:min-w-[100px]">Total</span>
              <span class="font-bold text-foreground">{{ formatNumber(stats.total_processed) }}</span>
            </div>
          </div>
        </div>

        <!-- Stats Summary -->
        <div class="flex-1 grid grid-cols-2 gap-4 md:gap-6 max-w-md w-full md:w-auto">
          <div class="text-center p-4 md:p-6 rounded-xl bg-gradient-to-br from-yellow-500/10 to-amber-600/10 border border-yellow-500/20 hover:border-yellow-500/40 transition-all">
            <p class="text-xs md:text-sm text-muted-foreground mb-1 md:mb-2">Duplicates</p>
            <p class="text-2xl md:text-3xl font-bold text-yellow-400 tabular-nums">
              <AnimatedCounter :value="stats.duplicates_in_current_sync" />
            </p>
          </div>
          
          <div class="text-center p-4 md:p-6 rounded-xl bg-gradient-to-br from-purple-500/10 to-indigo-600/10 border border-purple-500/20 hover:border-purple-500/40 transition-all">
            <p class="text-xs md:text-sm text-muted-foreground mb-1 md:mb-2">Last Updated</p>
            <p class="text-xs md:text-sm font-semibold text-foreground">
              <TimeAgo :timestamp="stats.last_updated" />
            </p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  Layers as LayersIcon,
  CheckCircle2 as CheckCircle2Icon,
  Send as SendIcon,
  AlertCircle as AlertCircleIcon,
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

// Calculate circumference segments for donut chart
const radius = 70
const totalCircumference = 2 * Math.PI * radius

// Calculate mutually exclusive segments:
// - Available (successful but not requested)
// - Requested (sent to Overseerr)
// - Errors (failed items)
const availableItems = computed(() => 
  props.stats.successful_items - props.stats.total_requested
)

const availableCircumference = computed(() => 
  (availableItems.value / props.stats.total_processed) * totalCircumference
)
const requestedCircumference = computed(() => 
  (props.stats.total_requested / props.stats.total_processed) * totalCircumference
)
const errorsCircumference = computed(() => 
  (props.stats.total_errors / props.stats.total_processed) * totalCircumference
)

// Percentages for display
const availablePercentage = computed(() => 
  Math.round((availableItems.value / props.stats.total_processed) * 100)
)
const requestedPercentageChart = computed(() => 
  Math.round((props.stats.total_requested / props.stats.total_processed) * 100)
)
</script>

