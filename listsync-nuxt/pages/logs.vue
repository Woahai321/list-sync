<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
          Live Logs
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
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
    <div class="border-b border-purple-500/20">
      <nav class="-mb-px flex space-x-8">
        <button
          @click="activeTab = 'frontend'"
          :class="[
            'py-2 px-1 border-b-2 font-bold text-xs uppercase tracking-wide transition-colors',
            activeTab === 'frontend'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-purple-500/30'
          ]"
        >
          Frontend Logs
        </button>
        <button
          @click="activeTab = 'backend'"
          :class="[
            'py-2 px-1 border-b-2 font-bold text-xs uppercase tracking-wide transition-colors',
            activeTab === 'backend'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-purple-500/30'
          ]"
        >
          Backend Logs
        </button>
      </nav>
    </div>

    <!-- Controls -->
    <Card variant="hover" class="group/controls border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-[10px] font-bold text-foreground uppercase tracking-wide">Auto-refresh:</label>
            <div class="flex items-center gap-1.5">
              <input
                type="checkbox"
                v-model="isAutoRefresh"
                class="w-3.5 h-3.5 text-purple-600 bg-card border-purple-500/30 rounded focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-background"
              />
              <span class="text-[10px] text-muted-foreground font-medium">{{ isAutoRefresh ? 'On' : 'Off' }}</span>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <label class="text-[10px] font-bold text-foreground uppercase tracking-wide">Interval:</label>
            <div class="w-28">
              <Select
                v-model="refreshInterval"
                :options="intervalOptions"
              />
            </div>
          </div>

          <div class="flex items-center gap-2">
            <label class="text-[10px] font-bold text-foreground uppercase tracking-wide">Lines:</label>
            <div class="w-24">
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
    <Card variant="hover" class="flex-1 min-h-0 border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" v-if="isConnected"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-purple-300" v-else></div>
            <span class="text-[10px] font-bold text-foreground uppercase tracking-wide">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="h-3 w-px bg-purple-500/20"></div>
          <span class="text-[10px] text-muted-foreground font-medium">
            {{ logLines.length }} lines ({{ currentPage }}/{{ totalPages }} pages)
          </span>
          <div class="h-3 w-px bg-purple-500/20"></div>
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
    
    // If this is initial load or refresh, fetch multiple pages starting from the last page
    let requestedPage = page
    let allLines: string[] = []
    let totalPagesCount = 1
    let totalLinesCount = 0
    let lastPageResponse: any = null
    
    if (requestedPage === null) {
      // First fetch to get total pages
      const metaResponse = await $fetch(endpoint, { 
        params: { page: 1, limit: parseInt(maxLines.value), sort_order: 'asc' } 
      })
      if (metaResponse.success) {
        totalPagesCount = metaResponse.total_pages
        totalLinesCount = metaResponse.total_lines
        requestedPage = totalPagesCount // Start with last page (newest)
      } else {
        requestedPage = 1
      }
      
      // On initial load, fetch multiple pages backwards from the last page
      // to get enough log lines to display
      const targetLines = parseInt(maxLines.value)
      let currentPageNum = requestedPage
      const pagesToFetch: number[] = []
      
      // Calculate how many pages we need to fetch
      // Start from last page and work backwards until we have enough lines
      while (currentPageNum >= 1 && pagesToFetch.length < totalPagesCount) {
        pagesToFetch.push(currentPageNum)
        currentPageNum--
        // Stop if we've collected enough pages (rough estimate: each page has ~limit lines)
        if (pagesToFetch.length * parseInt(maxLines.value) >= targetLines) {
          break
        }
      }
      
      // Reverse the array so we fetch from oldest to newest (e.g., [1, 2, 3] instead of [3, 2, 1])
      // This ensures chronological order: oldest logs at top, newest at bottom
      pagesToFetch.reverse()
      
      // Fetch pages from oldest to newest and append them
      for (const pageNum of pagesToFetch) {
        const params = {
          page: pageNum,
          limit: parseInt(maxLines.value),
          sort_order: 'asc'
        }
        
        const response = await $fetch(endpoint, { params })
        
        if (response.success) {
          // Append lines in chronological order (oldest first, newest last)
          allLines = [...allLines, ...response.lines]
          lastPageResponse = response
          
          // Stop if we have enough lines
          if (allLines.length >= targetLines) {
            break
          }
        }
      }
      
      // Update pagination info from the last page response
      if (lastPageResponse) {
        currentPage.value = lastPageResponse.page
        totalPages.value = lastPageResponse.total_pages
        totalLines.value = lastPageResponse.total_lines
        hasNextPage.value = lastPageResponse.has_prev // Has older logs (previous pages)
        hasPrevPage.value = lastPageResponse.has_next // Has newer logs (next pages)
      }
    } else {
      // Fetching a specific page (for pagination)
      const params = {
        page: requestedPage,
        limit: parseInt(maxLines.value),
        sort_order: 'asc' // Get oldest to newest from API
      }
      
      const response = await $fetch(endpoint, { params })
      
      if (response.success) {
        allLines = response.lines
        currentPage.value = response.page
        totalPages.value = response.total_pages
        totalLines.value = response.total_lines
        hasNextPage.value = response.has_prev // Has older logs (previous pages)
        hasPrevPage.value = response.has_next // Has newer logs (next pages)
      } else {
        isConnected.value = false
        console.error('Failed to fetch logs:', response.error)
        return
      }
    }
    
    // Update log lines
    if (append) {
      // Save scroll position before adding content at top
      const oldScrollHeight = logContainer.value?.scrollHeight || 0
      
      // Prepend older logs to the beginning
      logLines.value = [...allLines, ...logLines.value]
      
      // Restore scroll position after DOM update
      nextTick(() => {
        if (logContainer.value) {
          const newScrollHeight = logContainer.value.scrollHeight
          logContainer.value.scrollTop = newScrollHeight - oldScrollHeight
        }
      })
    } else {
      // Replace lines for refresh
      logLines.value = allLines
      isInitialLoad.value = false
    }
    
    isConnected.value = true
    lastUpdated.value = new Date().toLocaleTimeString()
    
    // Auto-scroll to bottom for new logs (only on initial load or refresh)
    if (!append) {
      nextTick(() => {
        scrollToBottom()
      })
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
    classes.push('text-purple-600') // Darker purple for errors
  } else if (line.includes('WARN') || line.includes('⚠️')) {
    classes.push('text-purple-500') // Medium-dark purple for warnings
  } else if (line.includes('INFO') || line.includes('✅') || line.includes('☑️') || line.includes('📌')) {
    classes.push('text-purple-400') // Medium purple for info
  } else if (line.includes('DEBUG')) {
    classes.push('text-purple-300') // Light purple for debug
  } else if (line.includes('🎯') || line.includes('🔍') || line.includes('📊') || line.includes('🎬')) {
    classes.push('text-purple-400') // Medium purple for special emojis
  } else {
    classes.push('text-purple-200') // Light purple-gray for default
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
