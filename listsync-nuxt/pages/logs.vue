<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Live Logs
        </h1>
        <p class="text-muted-foreground mt-1">
          Real-time view of ListSync log files
        </p>
      </div>

      <div class="flex items-center gap-3">
        <Button
          v-if="isAutoRefresh"
          variant="secondary"
          :icon="PauseIcon"
          @click="toggleAutoRefresh"
        >
          Pause
        </Button>
        <Button
          v-else
          variant="secondary"
          :icon="PlayIcon"
          @click="toggleAutoRefresh"
        >
          Resume
        </Button>
        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="isRefreshing"
          @click="handleRefresh"
        >
          {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
        </Button>
        <Button
          variant="secondary"
          :icon="DownloadIcon"
          @click="downloadLogs"
        >
          Download
        </Button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-border">
      <nav class="-mb-px flex space-x-8">
        <button
          @click="activeTab = 'frontend'"
          :class="[
            'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === 'frontend'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          ]"
        >
          Frontend Logs
        </button>
        <button
          @click="activeTab = 'backend'"
          :class="[
            'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === 'backend'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          ]"
        >
          Backend Logs
        </button>
      </nav>
    </div>

    <!-- Controls -->
    <Card variant="hover" class="group/controls">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex flex-wrap items-center gap-6">
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium text-foreground">Auto-refresh:</label>
            <div class="flex items-center gap-2">
              <input
                type="checkbox"
                v-model="isAutoRefresh"
                class="w-4 h-4 text-purple-600 bg-card border-border rounded focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-background"
              />
              <span class="text-sm text-muted-foreground">{{ isAutoRefresh ? 'On' : 'Off' }}</span>
            </div>
          </div>
          
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium text-foreground">Interval:</label>
            <div class="w-32">
              <Select
                v-model="refreshInterval"
                :options="intervalOptions"
              />
            </div>
          </div>

          <div class="flex items-center gap-3">
            <label class="text-sm font-medium text-foreground">Lines:</label>
            <div class="w-32">
              <Select
                v-model="maxLines"
                :options="lineOptions"
              />
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            :icon="ScrollToBottomIcon"
            @click="scrollToBottom"
          >
            Scroll to Bottom
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :icon="ClearIcon"
            @click="clearLogs"
          >
            Clear
          </Button>
        </div>
      </div>
    </Card>

    <!-- Log Display -->
    <Card variant="hover" class="flex-1 min-h-0">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse" v-if="isConnected"></div>
            <div class="w-2 h-2 rounded-full bg-red-500" v-else></div>
            <span class="text-sm font-medium text-foreground">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="h-4 w-px bg-border"></div>
          <span class="text-sm text-muted-foreground">
            {{ logLines.length }} lines
          </span>
          <div class="h-4 w-px bg-border"></div>
          <span class="text-sm text-muted-foreground">
            {{ activeTab === 'frontend' ? 'Frontend Logs' : 'Backend Logs' }}
          </span>
        </div>
        <div class="text-sm text-muted-foreground">
          Last updated: {{ lastUpdated }}
        </div>
      </div>

      <div
        ref="logContainer"
        class="bg-black/50 rounded-xl p-6 font-mono text-sm overflow-auto max-h-[70vh] custom-scrollbar border border-border/50"
        @scroll="handleScroll"
      >
        <div v-if="logLines.length === 0" class="text-muted-foreground text-center py-12">
          <component :is="FileTextIcon" :size="48" class="mx-auto mb-4 text-muted-foreground/60" />
          <p class="text-lg font-medium mb-2">No log data available</p>
          <p class="text-sm">Click refresh to load logs</p>
        </div>
        
        <div v-else class="space-y-1">
          <div
            v-for="(line, index) in displayLines"
            :key="index"
            :class="getLineClasses(line)"
            class="whitespace-pre-wrap break-words leading-relaxed"
          >
            {{ line }}
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Play as PlayIcon,
  Pause as PauseIcon,
  Download as DownloadIcon,
  ArrowDown as ScrollToBottomIcon,
  Trash2 as ClearIcon,
  FileText as FileTextIcon,
} from 'lucide-vue-next'

// Meta
definePageMeta({
  title: 'Live Logs',
  description: 'Real-time view of the ListSync core log file'
})

// Reactive state
const activeTab = ref<'frontend' | 'backend'>('frontend')
const logLines = ref<string[]>([])
const isRefreshing = ref(false)
const isAutoRefresh = ref(true)
const refreshInterval = ref('2000')
const maxLines = ref('1000')
const isConnected = ref(false)
const lastUpdated = ref('')
const autoRefreshTimer = ref<NodeJS.Timeout | null>(null)
const logContainer = ref<HTMLElement | null>(null)
const isAtBottom = ref(true)

// Select options
const intervalOptions = [
  { label: '1 second', value: '1000' },
  { label: '2 seconds', value: '2000' },
  { label: '5 seconds', value: '5000' },
  { label: '10 seconds', value: '10000' },
]

const lineOptions = [
  { label: '100', value: '100' },
  { label: '500', value: '500' },
  { label: '1,000', value: '1000' },
  { label: '2,000', value: '2000' },
  { label: '5,000', value: '5000' },
]

// Computed
const displayLines = computed(() => {
  const max = parseInt(maxLines.value)
  if (max === 0) return logLines.value
  return logLines.value.slice(-max)
})

// Methods
const fetchLogs = async () => {
  try {
    isRefreshing.value = true
    const endpoint = activeTab.value === 'frontend' ? '/api/logs/live' : '/api/logs/backend'
    const response = await $fetch(endpoint)
    
    if (response.success) {
      logLines.value = response.lines
      isConnected.value = true
      lastUpdated.value = new Date().toLocaleTimeString()
      
      // Auto-scroll to bottom if user was at bottom
      if (isAtBottom.value) {
        nextTick(() => {
          scrollToBottom()
        })
      }
    } else {
      isConnected.value = false
      console.error('Failed to fetch logs:', response.error)
    }
  } catch (error) {
    isConnected.value = false
    console.error('Error fetching logs:', error)
  } finally {
    isRefreshing.value = false
  }
}

const handleRefresh = () => {
  fetchLogs()
}

const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
}

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
    isAtBottom.value = true
  }
}

const clearLogs = () => {
  logLines.value = []
}

const downloadLogs = () => {
  const content = logLines.value.join('\n')
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `listsync-logs-${new Date().toISOString().split('T')[0]}.log`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleScroll = () => {
  if (logContainer.value) {
    const { scrollTop, scrollHeight, clientHeight } = logContainer.value
    isAtBottom.value = scrollTop + clientHeight >= scrollHeight - 10
  }
}

const getLineClasses = (line: string) => {
  const classes = []
  
  if (line.includes('ERROR') || line.includes('❌')) {
    classes.push('text-red-400')
  } else if (line.includes('WARN') || line.includes('⚠️')) {
    classes.push('text-yellow-400')
  } else if (line.includes('INFO') || line.includes('✅') || line.includes('☑️') || line.includes('📌')) {
    classes.push('text-green-400')
  } else if (line.includes('DEBUG')) {
    classes.push('text-blue-400')
  } else if (line.includes('🎯') || line.includes('🔍') || line.includes('📊') || line.includes('🎬')) {
    classes.push('text-purple-400')
  } else {
    classes.push('text-gray-300')
  }
  
  return classes.join(' ')
}

// Watch for interval changes
watch(refreshInterval, (newInterval) => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
  }
  
  if (isAutoRefresh.value) {
    autoRefreshTimer.value = setInterval(fetchLogs, parseInt(newInterval))
  }
})

// Watch for auto-refresh toggle
watch(isAutoRefresh, (enabled) => {
  if (enabled) {
    autoRefreshTimer.value = setInterval(fetchLogs, parseInt(refreshInterval.value))
  } else if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }
})

// Watch for tab changes
watch(activeTab, () => {
  fetchLogs()
})

// Lifecycle
onMounted(() => {
  fetchLogs()
  if (isAutoRefresh.value) {
    autoRefreshTimer.value = setInterval(fetchLogs, parseInt(refreshInterval.value))
  }
})

onUnmounted(() => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
  }
})
</script>
