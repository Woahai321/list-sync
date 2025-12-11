<template>
  <Card 
    variant="hover" 
    class="group/card relative overflow-hidden border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 cursor-pointer"
    @click="$emit('click')"
  >
    <!-- Gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-purple-500/5 opacity-60 group-hover/card:opacity-80 transition-opacity duration-300" />
    
    <!-- Content -->
    <div class="space-y-4 relative">
      <!-- Header -->
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <!-- Type Badge -->
          <div :class="[
            'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border',
            session.type === 'full' 
              ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' 
              : 'bg-purple-500/15 text-purple-300/80 border-purple-500/30'
          ]">
            <component :is="session.type === 'full' ? LayersIcon : ListIcon" :size="14" />
            {{ session.type === 'full' ? 'Full Sync' : 'Single List' }}
          </div>

          <!-- Status Badge -->
          <div :class="[
            'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border',
            getStatusClass(session.status)
          ]">
            <component :is="getStatusIcon(session.status)" :size="14" :class="{ 'animate-spin': session.status === 'in_progress' }" />
            {{ formatStatus(session.status) }}
          </div>
        </div>

        <!-- Timestamp -->
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <component :is="CalendarIcon" :size="14" />
          <Tooltip :content="formatDate(session.start_timestamp, 'PPpp')">
            <TimeAgo :timestamp="session.start_timestamp" />
          </Tooltip>
        </div>
      </div>

      <!-- Lists Summary -->
      <div v-if="session.lists.length > 0" class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 text-sm text-foreground">
          <component :is="ListIcon" :size="16" class="text-purple-400" />
          <span class="font-semibold">{{ session.lists.length }}</span>
          <span class="text-muted-foreground">{{ session.lists.length === 1 ? 'list' : 'lists' }}</span>
        </div>
        <span class="text-muted-foreground">·</span>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="(list, index) in session.lists.slice(0, 3)"
            :key="index"
            class="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30"
          >
            {{ formatListSource(list.type) }}
          </span>
          <span
            v-if="session.lists.length > 3"
            class="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20"
          >
            +{{ session.lists.length - 3 }}
          </span>
        </div>
      </div>

      <!-- Results Summary -->
      <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
        <!-- Total Items -->
        <div class="text-center">
          <div class="text-2xl font-bold text-foreground tabular-nums">{{ getDisplayItemCount() }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Total</div>
        </div>

        <!-- Requested -->
        <div v-if="session.results.requested > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-300 tabular-nums">{{ session.results.requested }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Requested</div>
        </div>

        <!-- Available -->
        <div v-if="session.results.already_available > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-300/80 tabular-nums">{{ session.results.already_available }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Available</div>
        </div>

        <!-- Already Requested -->
        <div v-if="session.results.already_requested > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-300/70 tabular-nums">{{ session.results.already_requested }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Pending</div>
        </div>

        <!-- Skipped -->
        <div v-if="session.results.skipped > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-300/60 tabular-nums">{{ session.results.skipped }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Skipped</div>
        </div>

        <!-- Not Found -->
        <div v-if="session.results.not_found > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-300/50 tabular-nums">{{ session.results.not_found }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Not Found</div>
        </div>

        <!-- Errors -->
        <div v-if="session.results.error > 0" class="text-center">
          <div class="text-2xl font-bold text-purple-400/60 tabular-nums">{{ session.results.error }}</div>
          <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Errors</div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between pt-3 border-t border-purple-500/10">
        <div v-if="session.duration !== null" class="flex items-center gap-1.5 text-xs text-muted-foreground">
          <component :is="ClockIcon" :size="14" />
          <span class="font-medium">{{ formatDuration(session.duration) }}</span>
        </div>
        <div v-else></div>

        <div class="text-xs text-purple-400 font-semibold group-hover/card:text-purple-300 transition-colors flex items-center gap-1">
          <span>View Details</span>
          <svg class="w-4 h-4 group-hover/card:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
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
import { extractUrlSegment } from '~/utils/urlHelpers'
import { formatListSource } from '~/utils/formatters'

interface Props {
  session: SyncHistorySession
}

const props = defineProps<Props>()

// Utilities
const getStatusClass = (status: string): string => {
  if (status === 'completed') return 'bg-purple-500/20 text-purple-300 border-purple-500/40'
  if (status === 'in_progress') return 'bg-purple-500/15 text-purple-300/80 border-purple-500/30'
  return 'bg-purple-500/10 text-purple-400/60 border-purple-500/20'
}

const getStatusIcon = (status: string) => {
  if (status === 'completed') return CheckCircle
  if (status === 'in_progress') return Loader2
  return XCircle
}

const formatStatus = (status: string): string => {
  if (status === 'completed') return 'Completed'
  if (status === 'in_progress') return 'In Progress'
  if (status === 'failed') return 'Failed'
  return status.charAt(0).toUpperCase() + status.slice(1)
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

// Get display item count - calculate from results for consistency
const getDisplayItemCount = (): number => {
  const results = props.session.results
  return results.requested + results.already_available + results.already_requested + results.skipped + results.not_found + results.error
}

// Extract list name from URL for better display
const getListDisplayName = (listId: string): string => {
  return extractUrlSegment(listId)
}
</script>


