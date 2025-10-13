<template>
  <Card class="glass-card">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <ActivityIcon class="w-5 h-5 text-primary" />
          <h3 class="text-lg font-semibold titillium-web-semibold">
            Sync Monitor
          </h3>
        </div>

        <Badge :variant="isSyncing ? 'primary' : 'default'">
          {{ isSyncing ? 'Active' : 'Idle' }}
        </Badge>
      </div>

      <!-- Progress Bar -->
      <div v-if="isSyncing" class="space-y-2">
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted-foreground">Progress</span>
          <span class="font-semibold">{{ progress }}%</span>
        </div>
        <div class="h-2 bg-muted/20 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-primary to-accent transition-all duration-300 ease-out"
            :style="{ width: `${progress}%` }"
          />
        </div>
      </div>

      <!-- Log Output -->
      <div
        ref="logContainer"
        class="bg-background/50 border border-border/50 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm"
      >
        <div v-if="syncLogs.length === 0" class="text-center text-muted-foreground py-8">
          <TerminalIcon class="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No sync activity</p>
          <p class="text-xs mt-1">Logs will appear here when sync starts</p>
        </div>

        <div v-else class="space-y-1">
          <div
            v-for="(log, index) in syncLogs"
            :key="index"
            class="flex items-start gap-2 py-1 hover:bg-muted/10 rounded px-2 -mx-2"
          >
            <!-- Timestamp -->
            <span class="text-muted-foreground text-xs flex-shrink-0">
              {{ formatLogTime(log.timestamp) }}
            </span>

            <!-- Level Icon -->
            <component
              :is="getLogIcon(log.level)"
              :class="[
                'w-4 h-4 flex-shrink-0 mt-0.5',
                getLogColor(log.level)
              ]"
            />

            <!-- Message -->
            <span :class="['flex-1', getLogColor(log.level)]">
              {{ log.message }}
            </span>
          </div>
        </div>
      </div>

      <!-- Clear Button -->
      <div v-if="syncLogs.length > 0" class="flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          @click="clearLogs"
        >
          <XIcon class="w-4 h-4 mr-2" />
          Clear Logs
        </Button>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Activity as ActivityIcon,
  Terminal as TerminalIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  AlertTriangle as AlertTriangleIcon,
  XCircle as XCircleIcon,
  X as XIcon,
} from 'lucide-vue-next'
import { format } from 'date-fns'

interface SyncLog {
  timestamp: string
  message: string
  level: string
}

interface Props {
  isSyncing: boolean
  syncLogs: SyncLog[]
  progress: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'clear-logs': []
}>()

const logContainer = ref<HTMLElement | null>(null)

// Format log timestamp
const formatLogTime = (timestamp: string) => {
  try {
    return format(new Date(timestamp), 'HH:mm:ss')
  } catch {
    return '--:--:--'
  }
}

// Get log icon based on level
const getLogIcon = (level: string) => {
  switch (level) {
    case 'success':
      return CheckCircleIcon
    case 'warning':
      return AlertTriangleIcon
    case 'error':
      return XCircleIcon
    default:
      return InfoIcon
  }
}

// Get log color based on level
const getLogColor = (level: string) => {
  switch (level) {
    case 'success':
      return 'text-success'
    case 'warning':
      return 'text-warning'
    case 'error':
      return 'text-danger'
    default:
      return 'text-foreground'
  }
}

// Clear logs
const clearLogs = () => {
  emit('clear-logs')
}

// Auto-scroll to bottom when new logs arrive
watch(
  () => props.syncLogs.length,
  () => {
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  }
)
</script>

