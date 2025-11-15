<template>
  <Card variant="default" class="overflow-hidden relative group/card">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-3">
      <!-- Top Row: Overall Health -->
      <div :class="`p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border ${systemStore.isHealthy ? 'border-green-500/40' : 'border-red-500/40'}`">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-1.5">
            <component :is="ActivityIcon" :size="14" class="text-purple-400" />
            <span class="text-[9px] font-bold text-purple-300 uppercase tracking-wide">System</span>
          </div>
          <div :class="systemStore.isHealthy ? 'px-2 py-0.5 rounded-full bg-purple-400/20 border border-purple-400/30' : 'px-2 py-0.5 rounded-full bg-red-400/20 border border-red-400/30'">
            <span :class="systemStore.isHealthy ? 'text-[10px] font-bold text-purple-200' : 'text-[10px] font-bold text-red-300'">
              {{ systemStore.isHealthy ? 'Healthy' : 'Issues' }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-2xl font-bold text-foreground tabular-nums leading-none">
            {{ systemStore.healthyServicesCount }}<span class="text-base text-muted-foreground">/{{ systemStore.totalServicesCount }}</span>
          </div>
          <div class="flex-1">
            <p class="text-[10px] text-purple-300/70">Services Operational</p>
          </div>
        </div>
      </div>

      <!-- Service Status Grid -->
      <div class="grid grid-cols-3 gap-2">
        <!-- Database -->
        <div :class="`p-2.5 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-400/10 border ${health?.database ? 'border-green-500/40' : 'border-red-500/40'}`">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="DatabaseIcon" :size="14" :class="health?.database ? 'text-purple-300' : 'text-red-400'" />
            <div :class="health?.database ? 'w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse' : 'w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse'" />
          </div>
          <p class="text-xs font-semibold text-foreground mb-0.5">Database</p>
          <p class="text-[10px] text-muted-foreground">
            {{ health?.database ? 'Connected' : 'Disconnected' }}
          </p>
        </div>

        <!-- Process -->
        <div :class="`p-2.5 rounded-lg bg-gradient-to-br from-purple-400/20 to-purple-300/10 border ${health?.process ? 'border-green-500/40' : 'border-red-500/40'}`">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="CpuIcon" :size="14" :class="health?.process ? 'text-purple-200' : 'text-red-400'" />
            <div :class="health?.process ? 'w-1.5 h-1.5 rounded-full bg-purple-300 animate-pulse' : 'w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse'" />
          </div>
          <p class="text-xs font-semibold text-foreground mb-0.5">Process</p>
          <p class="text-[10px] text-muted-foreground">
            {{ health?.process ? 'Running' : 'Stopped' }}
          </p>
        </div>

        <!-- Overseerr -->
        <div :class="`p-2.5 rounded-lg bg-gradient-to-br from-purple-300/20 to-purple-200/10 border ${systemStore.isOverseerrConnected ? 'border-green-500/40' : 'border-red-500/40'}`">
          <div class="flex items-center gap-1.5 mb-1.5">
            <component :is="ServerIcon" :size="14" :class="systemStore.isOverseerrConnected ? 'text-purple-100' : 'text-red-400'" />
            <div :class="systemStore.isOverseerrConnected ? 'w-1.5 h-1.5 rounded-full bg-purple-200 animate-pulse' : 'w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse'" />
          </div>
          <p class="text-xs font-semibold text-foreground mb-0.5">Overseerr</p>
          <p class="text-[10px] text-muted-foreground">
            {{ systemStore.isOverseerrConnected ? 'Connected' : 'Disconnected' }}
          </p>
        </div>
      </div>

      <!-- Sync Timing Info -->
      <div v-if="health" class="grid grid-cols-2 gap-2 items-stretch">
        <!-- Last Sync -->
        <div class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10 flex flex-col">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">Last Sync</span>
          </div>
          <p class="text-xs font-semibold text-foreground flex-1">
            <ClientOnly>
              {{ health.last_sync ? formatRelativeTime(health.last_sync) : 'Never' }}
              <template #fallback>
                <span class="opacity-50">...</span>
              </template>
            </ClientOnly>
          </p>
        </div>

        <!-- Next Sync -->
        <div class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10 flex flex-col">
          <div class="flex items-center gap-1.5 mb-1">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-300"></div>
            <span class="text-[9px] text-muted-foreground uppercase font-medium">Next Sync</span>
          </div>
          <p class="text-xs font-semibold text-foreground flex-1">
            <ClientOnly>
              {{ health.next_sync ? formatFutureTime(health.next_sync) : 'Not scheduled' }}
              <template #fallback>
                <span class="opacity-50">...</span>
              </template>
            </ClientOnly>
          </p>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Database as DatabaseIcon,
  Cpu as CpuIcon,
  Server as ServerIcon,
  Activity as ActivityIcon,
} from 'lucide-vue-next'
import type { SystemHealth } from '~/types'
import { formatRelativeTime, formatFutureTime } from '~/utils/formatters'

interface Props {
  health?: SystemHealth | null
}

defineProps<Props>()

const systemStore = useSystemStore()
</script>

