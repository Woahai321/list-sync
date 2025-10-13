<template>
  <Card class="glass-card">
    <div class="text-center py-8">
      <!-- Status Icon -->
      <div class="flex items-center justify-center mb-6">
        <div
          class="relative w-24 h-24 rounded-full flex items-center justify-center"
          :class="[
            isSyncing
              ? 'bg-primary/10 border-2 border-primary animate-pulse'
              : 'bg-primary/5 border-2 border-primary/20'
          ]"
        >
          <component
            :is="statusIcon"
            :class="[
              'w-12 h-12',
              isSyncing ? 'text-primary animate-spin' : 'text-primary'
            ]"
          />
        </div>
      </div>

      <!-- Status Text -->
      <h2 class="text-2xl font-bold mb-2 titillium-web-bold">
        {{ statusTitle }}
      </h2>
      <p class="text-muted-foreground mb-8">
        {{ statusDescription }}
      </p>

      <!-- Sync Button - MUCH MORE PROMINENT -->
      <button
        :disabled="isSyncing"
        :class="[
          'relative group px-16 py-6 text-xl font-bold rounded-2xl transition-all duration-300',
          'bg-gradient-to-r from-primary via-purple-600 to-accent',
          'hover:scale-105 active:scale-95',
          'disabled:opacity-70 disabled:cursor-not-allowed',
          'shadow-2xl shadow-primary/50',
          isSyncing ? '' : 'animate-pulse-glow'
        ]"
        @click="$emit('trigger-sync')"
      >
        <!-- Glow effect -->
        <span 
          v-if="!isSyncing"
          class="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary to-accent opacity-75 blur-xl animate-pulse-slow"
        />
        
        <!-- Content -->
        <span class="relative flex items-center justify-center gap-3 text-white">
          <component
            :is="isSyncing ? RefreshCwIcon : PlayIcon"
            :class="[
              'w-7 h-7',
              isSyncing && 'animate-spin'
            ]"
          />
          <span class="titillium-web-bold">
            {{ isSyncing ? 'Syncing...' : 'Start Sync' }}
          </span>
        </span>
      </button>

      <!-- Helper text -->
      <p class="text-sm text-muted-foreground mt-4">
        {{ isSyncing ? 'Sync is currently running...' : 'Click to start synchronization now' }}
      </p>

      <!-- Sync Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8 pt-8 border-t border-border/50">
        <!-- Last Sync -->
        <div>
          <div class="flex items-center justify-center gap-2 mb-2">
            <ClockIcon class="w-4 h-4 text-muted-foreground" />
            <span class="text-sm font-medium text-muted-foreground">Last Sync</span>
          </div>
          <div class="text-lg font-semibold">
            {{ lastSyncFormatted }}
          </div>
          <div class="text-sm text-muted-foreground mt-1">
            {{ lastSyncRelative }}
          </div>
        </div>

        <!-- Next Sync -->
        <div>
          <div class="flex items-center justify-center gap-2 mb-2">
            <CalendarIcon class="w-4 h-4 text-muted-foreground" />
            <span class="text-sm font-medium text-muted-foreground">Next Sync</span>
          </div>
          <div class="text-lg font-semibold">
            {{ nextSyncFormatted }}
          </div>
          <div class="text-sm text-muted-foreground mt-1">
            {{ nextSyncCountdown }}
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Play as PlayIcon,
  RefreshCw as RefreshIcon,
  RefreshCw as RefreshCwIcon,
  CheckCircle as CheckCircleIcon,
  Clock as ClockIcon,
  Calendar as CalendarIcon,
} from 'lucide-vue-next'
import { formatDistanceToNow, format } from 'date-fns'

interface Props {
  isSyncing: boolean
  lastSync: string | null
  nextSync: string | null
}

const props = defineProps<Props>()

defineEmits<{
  'trigger-sync': []
}>()

// Status computed
const statusIcon = computed(() => {
  return props.isSyncing ? RefreshIcon : CheckCircleIcon
})

const statusTitle = computed(() => {
  return props.isSyncing ? 'Sync in Progress' : 'Ready to Sync'
})

const statusDescription = computed(() => {
  return props.isSyncing
    ? 'Synchronization is currently running...'
    : 'Click the button below to start a new sync operation'
})

// Format last sync
const lastSyncFormatted = computed(() => {
  if (!props.lastSync) return 'Never'
  try {
    return format(new Date(props.lastSync), 'MMM d, yyyy h:mm a')
  } catch {
    return 'Unknown'
  }
})

const lastSyncRelative = computed(() => {
  if (!props.lastSync) return ''
  try {
    return formatDistanceToNow(new Date(props.lastSync), { addSuffix: true })
  } catch {
    return ''
  }
})

// Format next sync
const nextSyncFormatted = computed(() => {
  if (!props.nextSync) return 'Not scheduled'
  try {
    return format(new Date(props.nextSync), 'MMM d, yyyy h:mm a')
  } catch {
    return 'Unknown'
  }
})

// Countdown to next sync
const nextSyncCountdown = ref('')

const updateCountdown = () => {
  if (!props.nextSync) {
    nextSyncCountdown.value = ''
    return
  }

  try {
    const now = new Date()
    const next = new Date(props.nextSync)
    const diff = next.getTime() - now.getTime()

    if (diff <= 0) {
      nextSyncCountdown.value = 'Due now'
      return
    }

    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)

    if (hours > 0) {
      nextSyncCountdown.value = `in ${hours}h ${minutes}m`
    } else if (minutes > 0) {
      nextSyncCountdown.value = `in ${minutes}m ${seconds}s`
    } else {
      nextSyncCountdown.value = `in ${seconds}s`
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

// Watch for next sync changes
watch(() => props.nextSync, () => {
  updateCountdown()
})
</script>

