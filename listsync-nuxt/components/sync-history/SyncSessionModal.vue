<template>
  <Modal :is-open="true" size="xl" @close="$emit('close')">
    <template #header>
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-foreground titillium-web-bold">
            {{ session.type === 'full' ? 'Full' : 'Single List' }} Sync Session
          </h2>
          <p class="text-sm text-muted-foreground mt-1">
            {{ formatDate(session.start_timestamp, 'PPpp') }}
          </p>
        </div>
        <Badge :variant="getStatusVariant(session.status)" size="lg">
          <component :is="getStatusIcon(session.status)" :size="16" />
          {{ session.status }}
        </Badge>
      </div>
    </template>

    <div class="space-y-6">
      <!-- Performance Stats -->
      <div>
        <h3 class="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <component :is="ZapIcon" :size="20" class="text-orange-400" />
          Performance
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card variant="flat" class="p-4">
            <div class="text-xs text-muted-foreground mb-1">Duration</div>
            <div class="text-2xl font-bold text-foreground tabular-nums">
              {{ formatDuration(session.duration) }}
            </div>
          </Card>

          <Card variant="flat" class="p-4">
            <div class="text-xs text-muted-foreground mb-1">Total Items</div>
            <div class="text-2xl font-bold text-foreground tabular-nums">
              {{ session.processed_items }}
            </div>
          </Card>

          <Card variant="flat" class="p-4">
            <div class="text-xs text-muted-foreground mb-1">Avg/Item</div>
            <div class="text-2xl font-bold text-foreground tabular-nums">
              {{ session.average_time_ms ? `${session.average_time_ms.toFixed(1)}ms` : 'N/A' }}
            </div>
          </Card>

          <Card variant="flat" class="p-4">
            <div class="text-xs text-muted-foreground mb-1">Version</div>
            <div class="text-lg font-bold text-foreground truncate" :title="session.version || 'Unknown'">
              {{ session.version || 'Unknown' }}
            </div>
          </Card>
        </div>
      </div>

      <!-- Results -->
      <div>
        <h3 class="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <component :is="BarChartIcon" :size="20" class="text-purple-400" />
          Results
        </h3>
        <div class="space-y-3">
          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="flex items-center gap-2">
                <component :is="CheckCircleIcon" :size="16" class="text-green-400" />
                <span class="text-muted-foreground">Requested</span>
              </span>
              <span class="font-bold text-foreground tabular-nums">
                {{ session.results.requested }} ({{ getPercentage(session.results.requested) }}%)
              </span>
            </div>
            <div class="h-2 bg-black/30 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500"
                :style="{ width: `${getPercentage(session.results.requested)}%` }"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="flex items-center gap-2">
                <component :is="CheckCheckIcon" :size="16" class="text-blue-400" />
                <span class="text-muted-foreground">Already Available</span>
              </span>
              <span class="font-bold text-foreground tabular-nums">
                {{ session.results.already_available }} ({{ getPercentage(session.results.already_available) }}%)
              </span>
            </div>
            <div class="h-2 bg-black/30 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-blue-500 to-cyan-600 transition-all duration-500"
                :style="{ width: `${getPercentage(session.results.already_available)}%` }"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="flex items-center gap-2">
                <component :is="SkipForwardIcon" :size="16" class="text-gray-400" />
                <span class="text-muted-foreground">Skipped</span>
              </span>
              <span class="font-bold text-foreground tabular-nums">
                {{ session.results.skipped }} ({{ getPercentage(session.results.skipped) }}%)
              </span>
            </div>
            <div class="h-2 bg-black/30 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-gray-500 to-gray-600 transition-all duration-500"
                :style="{ width: `${getPercentage(session.results.skipped)}%` }"
              />
            </div>
          </div>

          <div v-if="session.results.error > 0" class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="flex items-center gap-2">
                <component :is="AlertCircleIcon" :size="16" class="text-red-400" />
                <span class="text-muted-foreground">Errors</span>
              </span>
              <span class="font-bold text-foreground tabular-nums">
                {{ session.results.error }} ({{ getPercentage(session.results.error) }}%)
              </span>
            </div>
            <div class="h-2 bg-black/30 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-red-500 to-red-600 transition-all duration-500"
                :style="{ width: `${getPercentage(session.results.error)}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Lists Synced -->
      <div v-if="session.lists.length > 0">
        <h3 class="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <component :is="ListIcon" :size="20" class="text-blue-400" />
          Lists Synced ({{ session.lists.length }})
        </h3>
        <div class="space-y-2">
          <Card
            v-for="(list, index) in session.lists"
            :key="index"
            variant="flat"
            class="p-4 group/list hover:border-purple-500/30 transition-all"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="font-medium text-foreground mb-1">
                  <Badge variant="info" size="sm" class="mr-2">{{ formatListSource(list.type) }}</Badge>
                  {{ extractUrlSegment(list.id) }}
                </div>
                <a 
                  v-if="list.url" 
                  :href="list.url" 
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-xs text-purple-400 hover:text-purple-300 hover:underline mt-1 flex items-center gap-1 w-fit transition-colors"
                  @click.stop
                >
                  <component :is="ExternalLinkIcon" :size="12" />
                  <span class="truncate max-w-md">{{ list.url }}</span>
                </a>
              </div>
              <Badge variant="success" class="ml-3 shrink-0">
                {{ list.item_count }} items
              </Badge>
            </div>
          </Card>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="session.errors.length > 0">
        <h3 class="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <component :is="AlertCircleIcon" :size="20" class="text-red-400" />
          Errors ({{ session.errors.length }})
        </h3>
        <div class="space-y-2 max-h-60 overflow-y-auto">
          <Card
            v-for="(error, index) in session.errors"
            :key="index"
            variant="flat"
            class="p-4 border-l-4 border-red-500/50"
          >
            <div class="font-medium text-foreground mb-1">{{ error.title }}</div>
            <div class="text-sm text-muted-foreground">{{ error.error }}</div>
            <div class="text-xs text-muted-foreground/70 mt-2">
              {{ formatDate(error.timestamp, 'PPpp') }}
            </div>
          </Card>
        </div>
      </div>

      <!-- Items Preview -->
      <div v-if="session.items.length > 0">
        <h3 class="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <component :is="FilmIcon" :size="20" class="text-purple-400" />
          Items ({{ session.items.length }})
        </h3>
        <div class="space-y-2 max-h-60 overflow-y-auto">
          <div
            v-for="(item, index) in session.items.slice(0, 50)"
            :key="index"
            class="flex items-center justify-between p-3 rounded-lg bg-black/20 border border-purple-500/10"
          >
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <component :is="getItemStatusIcon(item.status)" :size="16" :class="getItemStatusClass(item.status)" />
              <span class="text-sm text-foreground truncate">{{ item.title }}</span>
              <span v-if="item.year" class="text-xs text-muted-foreground">({{ item.year }})</span>
            </div>
            <Badge :variant="getItemStatusVariant(item.status)" size="sm">
              {{ item.status.replace('_', ' ') }}
            </Badge>
          </div>
          <div v-if="session.items.length > 50" class="text-center text-sm text-muted-foreground py-2">
            + {{ session.items.length - 50 }} more items
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <Button
          variant="ghost"
          :icon="FileTextIcon"
          @click="showRawLogs = true"
        >
          View Raw Logs
        </Button>
        <Button variant="secondary" @click="$emit('close')">
          Close
        </Button>
      </div>
    </template>
    
    <!-- Raw Logs Modal -->
    <RawLogsModal
      v-if="showRawLogs"
      :session-id="session.id"
      @close="showRawLogs = false"
    />
  </Modal>
</template>

<script setup lang="ts">
import {
  Zap as ZapIcon,
  BarChart3 as BarChartIcon,
  CheckCircle2 as CheckCircleIcon,
  CheckCheck as CheckCheckIcon,
  SkipForward as SkipForwardIcon,
  AlertCircle as AlertCircleIcon,
  List as ListIcon,
  Film as FilmIcon,
  ExternalLink as ExternalLinkIcon,
  FileText as FileTextIcon,
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
defineEmits<{
  close: []
}>()

// State
const showRawLogs = ref(false)

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

const formatDuration = (seconds: number | null): string => {
  if (!seconds) return 'N/A'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

const getPercentage = (value: number): number => {
  if (!props.session.processed_items) return 0
  return Math.round((value / props.session.processed_items) * 100)
}

const getItemStatusIcon = (status: string) => {
  switch (status) {
    case 'requested': return CheckCircleIcon
    case 'already_available': return CheckCheckIcon
    case 'already_requested': return CheckCircleIcon
    case 'skipped': return SkipForwardIcon
    case 'error': return AlertCircleIcon
    case 'not_found': return XCircle
    default: return XCircle
  }
}

const getItemStatusClass = (status: string): string => {
  switch (status) {
    case 'requested': return 'text-green-400'
    case 'already_available': return 'text-blue-400'
    case 'already_requested': return 'text-cyan-400'
    case 'skipped': return 'text-gray-400'
    case 'error': return 'text-red-400'
    case 'not_found': return 'text-orange-400'
    default: return 'text-gray-400'
  }
}

const getItemStatusVariant = (status: string): 'success' | 'info' | 'warning' | 'error' => {
  switch (status) {
    case 'requested': return 'success'
    case 'already_available': return 'info'
    case 'already_requested': return 'info'
    case 'skipped': return 'warning'
    case 'error': return 'error'
    case 'not_found': return 'warning'
    default: return 'warning'
  }
}
</script>

