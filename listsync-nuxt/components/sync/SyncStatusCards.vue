<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- Current Status Card -->
    <Card class="glass-card">
      <div class="flex items-start gap-4">
        <div
          class="p-3 rounded-lg"
          :class="statusColorClass"
        >
          <component
            :is="statusIcon"
            :class="[
              'w-6 h-6',
              isSyncing && 'animate-spin'
            ]"
          />
        </div>

        <div class="flex-1">
          <div class="text-sm text-muted-foreground mb-1">
            Current Status
          </div>
          <div class="text-xl font-bold mb-1 titillium-web-bold">
            {{ statusText }}
          </div>
          <Badge :variant="statusBadgeVariant">
            {{ statusBadgeText }}
          </Badge>
        </div>
      </div>
    </Card>

    <!-- Last Sync Card -->
    <Card class="glass-card">
      <div class="flex items-start gap-4">
        <div class="p-3 rounded-lg bg-primary/10">
          <ClockIcon class="w-6 h-6 text-primary" />
        </div>

        <div class="flex-1">
          <div class="text-sm text-muted-foreground mb-1">
            Last Sync
          </div>
          <div class="text-xl font-bold mb-1 titillium-web-bold">
            {{ lastSyncTime }}
          </div>
          <div class="text-sm text-muted-foreground">
            {{ lastSyncRelative }}
          </div>
        </div>
      </div>
    </Card>

    <!-- Next Sync Card -->
    <Card class="glass-card">
      <div class="flex items-start gap-4">
        <div class="p-3 rounded-lg bg-accent/10">
          <CalendarIcon class="w-6 h-6 text-accent" />
        </div>

        <div class="flex-1">
          <div class="text-sm text-muted-foreground mb-1">
            Next Sync
          </div>
          <div class="text-xl font-bold mb-1 titillium-web-bold">
            {{ nextSyncTime }}
          </div>
          <div class="text-sm text-muted-foreground">
            {{ nextSyncCountdown }}
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Clock as ClockIcon,
  Calendar as CalendarIcon,
  Pause as PauseIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow, format } from 'date-fns'

interface Props {
  currentStatus: string
  lastSync: string | null
  nextSync: string | null
  isSyncing: boolean
}

const props = defineProps<Props>()

// Status computed
const statusIcon = computed(() => {
  if (props.isSyncing) return RefreshIcon
  if (props.currentStatus === 'completed') return CheckCircleIcon
  if (props.currentStatus === 'failed') return XCircleIcon
  if (props.currentStatus === 'idle') return PauseIcon
  return CheckCircleIcon
})

const statusText = computed(() => {
  if (props.isSyncing) return 'Running'
  if (props.currentStatus === 'completed') return 'Completed'
  if (props.currentStatus === 'failed') return 'Failed'
  if (props.currentStatus === 'idle') return 'Idle'
  return 'Ready'
})

const statusColorClass = computed(() => {
  if (props.isSyncing) return 'bg-primary/10 text-primary'
  if (props.currentStatus === 'completed') return 'bg-success/10 text-success'
  if (props.currentStatus === 'failed') return 'bg-danger/10 text-danger'
  return 'bg-muted/10 text-muted-foreground'
})

const statusBadgeVariant = computed(() => {
  if (props.isSyncing) return 'primary'
  if (props.currentStatus === 'completed') return 'success'
  if (props.currentStatus === 'failed') return 'danger'
  return 'default'
})

const statusBadgeText = computed(() => {
  if (props.isSyncing) return 'In Progress'
  if (props.currentStatus === 'completed') return 'Success'
  if (props.currentStatus === 'failed') return 'Error'
  return 'Ready'
})

// Last sync formatting
const lastSyncTime = computed(() => {
  if (!props.lastSync) return 'Never'
  try {
    return format(new Date(props.lastSync), 'h:mm a')
  } catch {
    return 'Unknown'
  }
})

const lastSyncRelative = computed(() => {
  if (!props.lastSync) return 'No sync performed yet'
  try {
    return formatDistanceToNow(new Date(props.lastSync), { addSuffix: true })
  } catch {
    return ''
  }
})

// Next sync formatting
const nextSyncTime = computed(() => {
  if (!props.nextSync) return 'Not scheduled'
  try {
    return format(new Date(props.nextSync), 'h:mm a')
  } catch {
    return 'Unknown'
  }
})

const nextSyncCountdown = ref('')

const updateCountdown = () => {
  if (!props.nextSync) {
    nextSyncCountdown.value = 'Automatic sync disabled'
    return
  }

  try {
    const now = new Date()
    const next = new Date(props.nextSync)
    const diff = next.getTime() - now.getTime()

    if (diff <= 0) {
      nextSyncCountdown.value = 'Starting soon...'
      return
    }

    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

    if (hours > 0) {
      nextSyncCountdown.value = `in ${hours}h ${minutes}m`
    } else if (minutes > 0) {
      nextSyncCountdown.value = `in ${minutes} minutes`
    } else {
      nextSyncCountdown.value = 'Less than a minute'
    }
  } catch {
    nextSyncCountdown.value = ''
  }
}

// Update countdown every second
onMounted(() => {
  if (process.client) {
    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    
    onUnmounted(() => clearInterval(interval))
  }
})

watch(() => props.nextSync, () => {
  updateCountdown()
})
</script>

