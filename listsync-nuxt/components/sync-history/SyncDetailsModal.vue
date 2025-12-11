<template>
  <Modal
    v-model="isOpen"
    size="xl"
    @close="handleClose"
  >
    <template #title>
      <h2 class="text-xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
        Sync Session Details
      </h2>
    </template>
    <div v-if="session" class="space-y-4">
      <!-- Session Overview -->
      <div :class="[
        'grid gap-3',
        session.duration !== null ? 'grid-cols-1 md:grid-cols-4' : 'grid-cols-1 md:grid-cols-3'
      ]">
        <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
          <div class="flex flex-col items-center justify-center text-center p-2">
            <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-2">Type</p>
            <div :class="[
              'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border',
              session.type === 'full' 
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' 
                : 'bg-purple-500/15 text-purple-300/80 border-purple-500/30'
            ]">
              <component :is="session.type === 'full' ? LayersIcon : ListIcon" :size="14" />
              {{ session.type === 'full' ? 'Full Sync' : 'Single List' }}
            </div>
          </div>
        </Card>

        <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
          <div class="flex flex-col items-center justify-center text-center p-2">
            <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-2">Status</p>
            <div :class="[
              'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border',
              getStatusClass(session.status)
            ]">
              <component :is="getStatusIcon(session.status)" :size="14" :class="{ 'animate-spin': session.status === 'in_progress' }" />
              {{ formatStatus(session.status) }}
            </div>
          </div>
        </Card>

        <Card v-if="session.duration !== null" variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
          <div class="flex flex-col items-center justify-center text-center p-2">
            <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-2">Duration</p>
            <p class="text-lg font-bold text-foreground tabular-nums">
              {{ formatDuration(session.duration) }}
            </p>
          </div>
        </Card>

        <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
          <div class="flex flex-col items-center justify-center text-center p-2">
            <p class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-2">Started</p>
            <Tooltip :content="formatDate(session.start_timestamp, 'PPpp')">
              <p class="text-sm font-semibold text-foreground">
                <TimeAgo :timestamp="session.start_timestamp" />
              </p>
            </Tooltip>
          </div>
        </Card>
      </div>

      <!-- Results Breakdown -->
      <div class="space-y-3">
        <h3 class="text-base font-bold text-foreground titillium-web-semibold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Results Breakdown
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3">
          <!-- Total -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-foreground tabular-nums mb-1">{{ getDisplayItemCount() }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Total Items</div>
            </div>
          </Card>

          <!-- Requested -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-300 tabular-nums mb-1">{{ session.results.requested }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Requested</div>
            </div>
          </Card>

          <!-- Available -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-300/80 tabular-nums mb-1">{{ session.results.already_available }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Available</div>
            </div>
          </Card>

          <!-- Already Requested -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-300/70 tabular-nums mb-1">{{ session.results.already_requested }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Pending</div>
            </div>
          </Card>

          <!-- Skipped -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-300/60 tabular-nums mb-1">{{ session.results.skipped }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Skipped</div>
            </div>
          </Card>

          <!-- Not Found -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-300/50 tabular-nums mb-1">{{ session.results.not_found }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Not Found</div>
            </div>
          </Card>

          <!-- Errors -->
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="flex flex-col items-center justify-center text-center p-2">
              <div class="text-2xl font-bold text-purple-400/60 tabular-nums mb-1">{{ session.results.error }}</div>
              <div class="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">Errors</div>
            </div>
          </Card>
        </div>
      </div>

      <!-- Lists Synced -->
      <div v-if="session.lists.length > 0" class="space-y-3">
        <h3 class="text-base font-bold text-foreground titillium-web-semibold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Lists Synced ({{ session.lists.length }})
        </h3>
        <div class="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
          <Card
            v-for="(list, index) in session.lists"
            :key="index"
            variant="default"
            class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-3 flex-1 min-w-0">
                <div class="px-2.5 py-1 rounded-lg bg-purple-500/20 border border-purple-500/40">
                  <span class="text-xs font-bold text-purple-300 uppercase">{{ formatListSource(list.type) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-foreground truncate">{{ getListDisplayName(list.id) }}</p>
                  <p class="text-xs text-muted-foreground truncate">{{ list.id }}</p>
                </div>
              </div>
              <div v-if="list.item_count" class="text-right flex-shrink-0">
                <div class="text-lg font-bold text-foreground tabular-nums">{{ list.item_count }}</div>
                <div class="text-[10px] text-muted-foreground">items</div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <!-- Session Metadata -->
      <div class="space-y-3">
        <h3 class="text-base font-bold text-foreground titillium-web-semibold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Session Information
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="space-y-3 p-1">
              <div class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide whitespace-nowrap">Session ID</span>
                <code class="text-xs font-mono text-foreground bg-black/30 px-2 py-1 rounded border border-purple-500/20 truncate">{{ session.id }}</code>
              </div>
              <div class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide whitespace-nowrap">Start Time</span>
                <span class="text-xs text-foreground font-medium text-right">{{ formatDate(session.start_timestamp, 'PPpp') }}</span>
              </div>
              <div v-if="session.end_timestamp" class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide whitespace-nowrap">End Time</span>
                <span class="text-xs text-foreground font-medium text-right">{{ formatDate(session.end_timestamp, 'PPpp') }}</span>
              </div>
            </div>
          </Card>

          <Card variant="default" class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all">
            <div class="space-y-3 p-1">
              <div class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide whitespace-nowrap">Success Rate</span>
                <span class="text-lg font-bold text-purple-300 tabular-nums">{{ getSuccessRate() }}%</span>
              </div>
              <div v-if="session.duration !== null" class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wide whitespace-nowrap">Items/Second</span>
                <span class="text-lg font-bold text-purple-300 tabular-nums">{{ getItemsPerSecond() }}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end">
        <Button
          variant="ghost"
          @click="handleClose"
        >
          Close
        </Button>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  Layers as LayersIcon,
  List as ListIcon,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-vue-next'
import type { SyncHistorySession } from '~/types'
import { extractUrlSegment } from '~/utils/urlHelpers'
import { formatListSource } from '~/utils/formatters'

interface Props {
  modelValue: boolean
  session: SyncHistorySession | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleClose = () => {
  isOpen.value = false
}

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

const getDisplayItemCount = (): number => {
  if (!props.session) return 0
  const results = props.session.results
  return results.requested + results.already_available + results.already_requested + results.skipped + results.not_found + results.error
}

const getListDisplayName = (listId: string): string => {
  return extractUrlSegment(listId)
}

const getSuccessRate = (): string => {
  if (!props.session) return '0.0'
  const total = getDisplayItemCount()
  if (total === 0) return '0.0'
  const successful = props.session.results.requested + props.session.results.already_available + props.session.results.already_requested
  return ((successful / total) * 100).toFixed(1)
}

const getItemsPerSecond = (): string => {
  if (!props.session || !props.session.duration || props.session.duration === 0) return '0.0'
  const total = getDisplayItemCount()
  return (total / props.session.duration).toFixed(1)
}
</script>

