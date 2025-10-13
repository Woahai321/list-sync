<template>
  <Card 
    variant="hover" 
    class="group/card relative overflow-hidden"
  >
    <!-- Gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-accent/5 opacity-0 group-hover/card:opacity-100 transition-opacity duration-300" />
    
    <!-- Content -->
    <div class="space-y-4 relative">
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <!-- Type Badge -->
            <Badge :variant="session.type === 'full' ? 'primary' : 'info'" size="md">
              <component :is="session.type === 'full' ? LayersIcon : ListIcon" :size="14" />
              {{ session.type === 'full' ? 'Full Sync' : 'Single List' }}
            </Badge>

            <!-- Status Badge -->
            <Badge :variant="getStatusVariant(session.status)" size="md">
              <component :is="getStatusIcon(session.status)" :size="14" />
              {{ session.status }}
            </Badge>
          </div>

          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <component :is="CalendarIcon" :size="16" />
            <Tooltip :content="formatDate(session.start_timestamp, 'PPpp')">
              <TimeAgo :timestamp="session.start_timestamp" />
            </Tooltip>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="text-right">
          <div class="text-2xl font-bold text-foreground tabular-nums">
            {{ getDisplayItemCount() }}
          </div>
          <div class="text-xs text-muted-foreground">items</div>
        </div>
      </div>

      <!-- Lists -->
      <div v-if="session.lists.length > 0" class="flex flex-wrap gap-2">
        <div
          v-for="(list, index) in session.lists.slice(0, 3)"
          :key="index"
          class="px-3 py-1 rounded-lg bg-black/30 border border-purple-500/20 text-xs text-muted-foreground"
        >
          <span class="font-medium text-purple-400">{{ list.type }}</span>: {{ getListDisplayName(list.id) }}
          <span v-if="list.item_count" class="text-muted-foreground ml-1">({{ list.item_count }})</span>
        </div>
        <div
          v-if="session.lists.length > 3"
          class="px-3 py-1 rounded-lg bg-black/30 border border-purple-500/20 text-xs text-muted-foreground"
        >
          +{{ session.lists.length - 3 }} more
        </div>
      </div>

      <!-- Results Bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <!-- Requested -->
        <div v-if="session.results.requested > 0" class="flex items-center gap-2 group/stat">
          <div class="p-2 rounded-lg bg-gradient-to-br from-green-500/20 to-emerald-600/20">
            <component :is="CheckCircleIcon" :size="16" class="text-green-400" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Requested</div>
            <div class="text-sm font-bold text-foreground tabular-nums">{{ session.results.requested }}</div>
          </div>
        </div>

        <!-- Available -->
        <div v-if="session.results.already_available > 0" class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-600/20">
            <component :is="CheckCheckIcon" :size="16" class="text-blue-400" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Available</div>
            <div class="text-sm font-bold text-foreground tabular-nums">{{ session.results.already_available }}</div>
          </div>
        </div>

        <!-- Skipped -->
        <div v-if="session.results.skipped > 0" class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-gradient-to-br from-gray-500/20 to-gray-600/20">
            <component :is="SkipForwardIcon" :size="16" class="text-gray-400" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Skipped</div>
            <div class="text-sm font-bold text-foreground tabular-nums">{{ session.results.skipped }}</div>
          </div>
        </div>

        <!-- Errors -->
        <div v-if="session.results.error > 0" class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-gradient-to-br from-red-500/20 to-red-600/20">
            <component :is="AlertCircleIcon" :size="16" class="text-red-400" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Errors</div>
            <div class="text-sm font-bold text-foreground tabular-nums">{{ session.results.error }}</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between pt-3 border-t border-purple-500/10">
        <div class="flex items-center gap-4 text-xs text-muted-foreground">
          <div v-if="session.duration !== null" class="flex items-center gap-1">
            <component :is="ClockIcon" :size="14" />
            <span>{{ formatDuration(session.duration) }}</span>
          </div>
        </div>

        <div class="text-xs text-muted-foreground flex items-center gap-1">
          Session Details
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Layers as LayersIcon,
  List as ListIcon,
  Calendar as CalendarIcon,
  CheckCircle2 as CheckCircleIcon,
  CheckCheck as CheckCheckIcon,
  SkipForward as SkipForwardIcon,
  AlertCircle as AlertCircleIcon,
  Clock as ClockIcon,
  Tag as TagIcon,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-vue-next'
import type { SyncHistorySession } from '~/types'

interface Props {
  session: SyncHistorySession
}

const props = defineProps<Props>()

// Utilities
const getStatusVariant = (status: string): 'success' | 'warning' | 'error' => {
  if (status === 'completed') return 'success'
  if (status === 'in_progress') return 'warning'
  return 'error'
}

const getStatusIcon = (status: string) => {
  if (status === 'completed') return CheckCircle
  if (status === 'in_progress') return Loader2
  return XCircle
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

// Get display item count - use total_items for single syncs, processed_items for full syncs
const getDisplayItemCount = (): number => {
  if (props.session.type === 'single' && props.session.total_items > 0) {
    return props.session.total_items
  }
  return props.session.processed_items
}

// Extract list name from URL for better display
const getListDisplayName = (listId: string): string => {
  // Handle Trakt URLs
  if (listId.includes('trakt.tv/users/') && listId.includes('/lists/')) {
    const match = listId.match(/\/lists\/([^\/\?]+)/)
    if (match) {
      return `/${match[1]}`
    }
  }
  
  // Handle IMDb URLs
  if (listId.includes('imdb.com/list/')) {
    const match = listId.match(/\/list\/([^\/\?]+)/)
    if (match) {
      return `/${match[1]}`
    }
  }
  
  // Handle other URLs - extract the last part after the final slash
  const parts = listId.split('/')
  const lastPart = parts[parts.length - 1]
  if (lastPart && lastPart !== '') {
    return `/${lastPart}`
  }
  
  // Fallback to original ID
  return listId
}
</script>

