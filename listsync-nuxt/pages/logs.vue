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
            :icon="ScrollToLatestIcon"
            @click="scrollToBottom"
          >
            Scroll to Latest
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
            {{ logLines.length }} lines ({{ currentPage }}/{{ totalPages }} pages)
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
          <!-- Loading indicator for more logs -->
          <div v-if="isLoadingMore" class="text-center py-4 text-muted-foreground">
            <div class="animate-spin w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2"></div>
            Loading more logs...
          </div>
          
          <div
            v-for="(line, index) in displayLines"
            :key="index"
            :class="getLineClasses(line)"
            class="whitespace-pre-wrap break-words leading-relaxed"
          >
            {{ line }}
          </div>
          
          <!-- End of logs indicator -->
          <div v-if="!hasNextPage && logLines.length > 0" class="text-center py-4 text-muted-foreground text-sm">
            End of logs
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
  ArrowDown as ScrollToLatestIcon,
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
const maxLines = ref('200') // Reduced from 1000 to 200 for pagination
const isConnected = ref(false)
const lastUpdated = ref('')
const autoRefreshTimer = ref<NodeJS.Timeout | null>(null)
const logContainer = ref<HTMLElement | null>(null)
const isAtBottom = ref(true)

// Pagination state
const currentPage = ref(1)
const totalPages = ref(1)
const totalLines = ref(0)
const hasNextPage = ref(false)
const hasPrevPage = ref(false)
const isLoadingMore = ref(false)
const isInitialLoad = ref(true)

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
  // Return all lines - pagination is handled by the API
  return logLines.value
})

// Methods
const fetchLogs = async (page: number | null = null, append: boolean = false) => {
  try {
    if (!append) {
      isRefreshing.value = true
    } else {
      isLoadingMore.value = true
    }
    
    const endpoint = activeTab.value === 'frontend' ? '/api/logs/live' : '/api/logs/backend'
    
    // If this is initial load or refresh, fetch last page (newest logs)
    let requestedPage = page
    if (requestedPage === null) {
      // First fetch to get total pages
      const metaResponse = await $fetch(endpoint, { 
        params: { page: 1, limit: parseInt(maxLines.value), sort_order: 'asc' } 
      })
      if (metaResponse.success) {
        requestedPage = metaResponse.total_pages // Start with last page (newest)
      } else {
        requestedPage = 1
      }
    }
    
    const params = {
      page: requestedPage,
      limit: parseInt(maxLines.value),
      sort_order: 'asc' // Get oldest to newest from API
    }
    
    const response = await $fetch(endpoint, { params })
    
    if (response.success) {
      if (append) {
        // Save scroll position before adding content at top
        const oldScrollHeight = logContainer.value?.scrollHeight || 0
        
        // Prepend older logs to the beginning
        logLines.value = [...response.lines, ...logLines.value]
        
        // Restore scroll position after DOM update
        nextTick(() => {
          if (logContainer.value) {
            const newScrollHeight = logContainer.value.scrollHeight
            logContainer.value.scrollTop = newScrollHeight - oldScrollHeight
          }
        })
      } else {
        // Replace lines for refresh
        logLines.value = response.lines
        isInitialLoad.value = false
      }
      
      // Update pagination info
      currentPage.value = response.page
      totalPages.value = response.total_pages
      totalLines.value = response.total_lines
      // For reverse chronological: hasPrev means older logs (lower page numbers)
      hasNextPage.value = response.has_prev // Has older logs (previous pages)
      hasPrevPage.value = response.has_next // Has newer logs (next pages)
      
      isConnected.value = true
      lastUpdated.value = new Date().toLocaleTimeString()
      
      // Auto-scroll to bottom for new logs (only on initial load or refresh)
      if (!append) {
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
    isLoadingMore.value = false
  }
}

const handleRefresh = () => {
  // Reset to initial state and fetch newest logs (last page)
  isInitialLoad.value = true
  fetchLogs(null, false)
}

// Load older logs when scrolling up (going backwards in time = lower page numbers)
const loadOlderLogs = () => {
  if (hasNextPage.value && !isLoadingMore.value && currentPage.value > 1) {
    fetchLogs(currentPage.value - 1, true)
  }
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

const scrollToTop = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = 0
    isAtBottom.value = false
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
    const isAtBottomNow = scrollTop + clientHeight >= scrollHeight - 10
    const isAtTop = scrollTop <= 10
    
    isAtBottom.value = isAtBottomNow
    
    // Load older logs when user scrolls to top (to see older messages)
    if (isAtTop && hasNextPage.value && !isLoadingMore.value) {
      loadOlderLogs()
    }
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
    autoRefreshTimer.value = setInterval(() => fetchLogs(null, false), parseInt(newInterval))
  }
})

// Watch for auto-refresh toggle
watch(isAutoRefresh, (enabled) => {
  if (enabled) {
    autoRefreshTimer.value = setInterval(() => fetchLogs(null, false), parseInt(refreshInterval.value))
  } else if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }
})

// Watch for tab changes
watch(activeTab, () => {
  isInitialLoad.value = true
  fetchLogs(null, false)
})

// Watch for line limit changes
watch(maxLines, () => {
  isInitialLoad.value = true
  fetchLogs(null, false)
})

// Lifecycle
onMounted(() => {
  fetchLogs(null, false)
  if (isAutoRefresh.value) {
    autoRefreshTimer.value = setInterval(() => fetchLogs(null, false), parseInt(refreshInterval.value))
  }
})

onUnmounted(() => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
  }
})
</script>
