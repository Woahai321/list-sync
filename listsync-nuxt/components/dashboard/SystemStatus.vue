<template>
  <Card variant="default">
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">System Status</h3>
        <Badge
          :variant="systemStore.isHealthy ? 'success' : 'error'"
          size="sm"
        >
          {{ systemStore.isHealthy ? 'Healthy' : 'Issues Detected' }}
        </Badge>
      </div>
    </template>

    <div class="space-y-4">
      <!-- Service Status Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Database -->
        <div :class="serviceCardClasses(health?.database)">
          <div class="flex items-center gap-3">
            <component :is="DatabaseIcon" :size="20" :class="health?.database ? 'text-green-400' : 'text-red-400'" />
            <div class="flex-1">
              <p class="text-sm font-medium text-foreground">Database</p>
              <p class="text-xs text-muted-foreground">
                {{ health?.database ? 'Connected' : 'Disconnected' }}
              </p>
            </div>
            <div :class="statusDotClass(health?.database)" />
          </div>
        </div>

        <!-- Process -->
        <div :class="serviceCardClasses(health?.process)">
          <div class="flex items-center gap-3">
            <component :is="CpuIcon" :size="20" :class="health?.process ? 'text-green-400' : 'text-red-400'" />
            <div class="flex-1">
              <p class="text-sm font-medium text-foreground">Process</p>
              <p class="text-xs text-muted-foreground">
                {{ health?.process ? 'Running' : 'Stopped' }}
              </p>
            </div>
            <div :class="statusDotClass(health?.process)" />
          </div>
        </div>

        <!-- Overseerr -->
        <div :class="serviceCardClasses(systemStore.isOverseerrConnected)">
          <div class="flex items-center gap-3">
            <component :is="ServerIcon" :size="20" :class="systemStore.isOverseerrConnected ? 'text-green-400' : 'text-red-400'" />
            <div class="flex-1">
              <p class="text-sm font-medium text-foreground">Overseerr</p>
              <p class="text-xs text-muted-foreground">
                {{ systemStore.isOverseerrConnected ? 'Connected' : 'Disconnected' }}
              </p>
            </div>
            <div :class="statusDotClass(systemStore.isOverseerrConnected)" />
          </div>
        </div>
      </div>

      <!-- Health Percentage -->
      <div class="flex items-center gap-4 p-4 rounded-lg bg-black/20">
        <div class="flex-shrink-0">
          <ProgressRing
            :progress="systemStore.healthPercentage"
            :size="80"
            :stroke-width="6"
            :color="systemStore.healthPercentage >= 100 ? 'success' : systemStore.healthPercentage >= 66 ? 'warning' : 'error'"
          >
            <span class="text-sm font-bold">{{ systemStore.healthyServicesCount }}/{{ systemStore.totalServicesCount }}</span>
          </ProgressRing>
        </div>
        
        <div class="flex-1">
          <p class="text-sm font-medium text-foreground mb-1">Overall Health</p>
          <p class="text-xs text-muted-foreground">
            {{ systemStore.healthyServicesCount }} of {{ systemStore.totalServicesCount }} services operational
          </p>
        </div>
      </div>

      <!-- Sync Information -->
      <div v-if="health" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Sync Status -->
        <div class="p-3 rounded-lg bg-black/20">
          <p class="text-xs text-muted-foreground mb-1">Sync Status</p>
          <Badge :variant="getSyncStatusVariant(health.sync_status)" size="sm">
            {{ health.sync_status || 'Unknown' }}
          </Badge>
        </div>

        <!-- Last Sync -->
        <div class="p-3 rounded-lg bg-black/20">
          <p class="text-xs text-muted-foreground mb-1">Last Sync</p>
          <p class="text-sm font-medium text-foreground">
            <ClientOnly>
              {{ health.last_sync ? formatRelativeTime(health.last_sync) : 'Never' }}
              <template #fallback>
                <span class="opacity-50">...</span>
              </template>
            </ClientOnly>
          </p>
        </div>

        <!-- Next Sync -->
        <div class="p-3 rounded-lg bg-black/20">
          <p class="text-xs text-muted-foreground mb-1">Next Sync</p>
          <p class="text-sm font-medium text-foreground">
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
} from 'lucide-vue-next'
import type { SystemHealth } from '~/types'

interface Props {
  health?: SystemHealth | null
}

defineProps<Props>()

const systemStore = useSystemStore()

const serviceCardClasses = (isHealthy?: boolean) => {
  const baseClasses = 'p-4 rounded-lg border transition-all'
  
  if (isHealthy) {
    return `${baseClasses} bg-green-500/5 border-green-500/20 hover:border-green-500/30`
  }
  return `${baseClasses} bg-red-500/5 border-red-500/20 hover:border-red-500/30`
}

const statusDotClass = (isHealthy?: boolean) => {
  const baseClasses = 'w-2 h-2 rounded-full'
  
  if (isHealthy) {
    return `${baseClasses} bg-green-500 pulse-glow`
  }
  return `${baseClasses} bg-red-500 animate-pulse`
}

const getSyncStatusVariant = (status: string) => {
  const statusMap: Record<string, 'success' | 'error' | 'warning' | 'info'> = {
    'idle': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'error',
  }
  return statusMap[status?.toLowerCase()] || 'default'
}
</script>

