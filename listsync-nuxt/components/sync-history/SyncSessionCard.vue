<template>
  <Card 
    variant="hover" 
    class="group/card relative overflow-hidden border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300"
  >
    <!-- Gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-purple-500/5 opacity-60 group-hover/card:opacity-80 transition-opacity duration-300" />
    
    <!-- Content -->
    <div class="space-y-3 relative">
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
          <div class="text-2xl font-bold text-foreground tabular-nums leading-none">
            {{ getDisplayItemCount() }}
          </div>
          <div class="text-[10px] text-muted-foreground font-medium mt-0.5">items</div>
        </div>
      </div>

      <!-- Lists -->
      <div v-if="session.lists.length > 0" class="flex flex-wrap gap-2">
        <div
          v-for="(list, index) in session.lists.slice(0, 3)"
          :key="index"
          class="px-2 py-1 rounded-lg bg-purple-600/10 border border-purple-500/20 text-[10px] text-muted-foreground font-medium"
        >
          <span class="font-bold text-purple-400 uppercase">{{ formatListSource(list.type) }}</span>: {{ getListDisplayName(list.id) }}
          <span v-if="list.item_count" class="text-muted-foreground ml-1">({{ list.item_count }})</span>
        </div>
        <div
          v-if="session.lists.length > 3"
          class="px-2 py-1 rounded-lg bg-purple-600/10 border border-purple-500/20 text-[10px] text-muted-foreground font-bold"
        >
          +{{ session.lists.length - 3 }} more
        </div>
      </div>

      <!-- Results Bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <!-- Requested -->
        <div v-if="session.results.requested > 0" class="flex items-center gap-1.5 group/stat">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <component :is="CheckCircleIcon" :size="14" class="text-purple-400" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Requested</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.requested }}</div>
          </div>
        </div>

        <!-- Available -->
        <div v-if="session.results.already_available > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28">
            <component :is="CheckCheckIcon" :size="14" class="text-purple-300" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Available</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.already_available }}</div>
          </div>
        </div>

        <!-- Already Requested -->
        <div v-if="session.results.already_requested > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-400/20 to-purple-300/10 border border-purple-300/30">
            <component :is="CheckCircleIcon" :size="14" class="text-purple-200" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Already Req.</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.already_requested }}</div>
          </div>
        </div>

        <!-- Skipped -->
        <div v-if="session.results.skipped > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-300/20 to-purple-200/10 border border-purple-200/30">
            <component :is="SkipForwardIcon" :size="14" class="text-purple-100" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Skipped</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.skipped }}</div>
          </div>
        </div>

        <!-- Not Found -->
        <div v-if="session.results.not_found > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <component :is="AlertCircleIcon" :size="14" class="text-purple-400" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Not Found</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.not_found }}</div>
          </div>
        </div>

        <!-- Errors -->
        <div v-if="session.results.error > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28">
            <component :is="AlertCircleIcon" :size="14" class="text-purple-300" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">Errors</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.results.error }}</div>
          </div>
        </div>

        <!-- Fallback for single syncs with no detailed results -->
        <div v-if="session.type === 'single' && getDisplayItemCount() === 0 && session.lists.length > 0" class="flex items-center gap-1.5">
          <div class="p-1.5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <component :is="ListIcon" :size="14" class="text-purple-400" />
          </div>
          <div>
            <div class="text-[10px] text-muted-foreground font-medium">List Items</div>
            <div class="text-base font-bold text-foreground tabular-nums leading-none">{{ session.lists[0]?.item_count || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between pt-2 border-t border-purple-500/10">
        <div class="flex items-center gap-4 text-[10px] text-muted-foreground font-medium">
          <div v-if="session.duration !== null" class="flex items-center gap-1">
            <component :is="ClockIcon" :size="12" />
            <span>{{ formatDuration(session.duration) }}</span>
          </div>
        </div>

        <div class="text-[10px] text-muted-foreground flex items-center gap-1 font-medium uppercase tracking-wide">
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
import { extractUrlSegment } from '~/utils/urlHelpers'
import { formatListSource } from '~/utils/formatters'

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

