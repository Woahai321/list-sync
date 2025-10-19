<template>
  <div class="space-y-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-foreground titillium-web-bold">
          Sync Management
        </h1>
        <p class="text-muted-foreground mt-1">
          Trigger and monitor synchronization operations
        </p>
      </div>

      <Button
        variant="secondary"
        :icon="RefreshIcon"
        :loading="isRefreshing"
        @click="handleRefresh"
      >
        Refresh
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="isInitialLoading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading sync data..." />
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Sync Trigger -->
      <SyncTrigger
        :is-syncing="syncStore.isSyncing"
        :last-sync="systemStore.health?.last_sync || null"
        :next-sync="systemStore.health?.next_sync || null"
        @trigger-sync="handleTriggerSync"
      />

      <!-- Sync Status Cards -->
      <SyncStatusCards
        :current-status="syncStore.status"
        :last-sync="systemStore.health?.last_sync || null"
        :next-sync="systemStore.health?.next_sync || null"
        :is-syncing="syncStore.isSyncing"
      />

      <!-- Sync Monitor & Interval Config -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Sync Monitor -->
        <SyncMonitor
          :is-syncing="syncStore.isSyncing"
          :sync-logs="syncLogs"
          :progress="syncProgress"
          @clear-logs="syncLogs = []"
        />

        <!-- Interval Configuration -->
        <IntervalConfig
          :current-interval="syncStore.syncInterval?.interval_hours || 24"
          :interval-source="syncStore.syncInterval?.source === 'env' ? 'env' : 'database'"
          @update-interval="handleUpdateInterval"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
} from 'lucide-vue-next'

const syncStore = useSyncStore()
const systemStore = useSystemStore()
const { showSuccess, showError } = useToast()
const api = useApiService()

// Set page title
useHead({
  title: 'Sync Management - ListSync',
})

// State
const isInitialLoading = ref(true)
const isRefreshing = ref(false)
const syncLogs = ref<Array<{ timestamp: string; message: string; level: string }>>([])
const syncProgress = ref(0)

// Fetch initial data
const fetchSyncData = async () => {
  try {
    await Promise.all([
      syncStore.fetchLiveSyncStatus(),
      syncStore.fetchSyncInterval(),
      systemStore.checkHealth(), // Get last_sync and next_sync
    ])
  } catch (error) {
    console.error('Error loading sync data:', error)
  } finally {
    isInitialLoading.value = false
  }
}

// Refresh data
const handleRefresh = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      syncStore.fetchLiveSyncStatus(),
      syncStore.fetchSyncInterval(),
      systemStore.checkHealth(),
    ])
    showSuccess('Sync data refreshed')
  } catch (error: any) {
    showError('Refresh Failed', error.message)
  } finally {
    isRefreshing.value = false
  }
}

// Trigger sync
const handleTriggerSync = async () => {
  try {
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Synchronization has been triggered')
    
    // Clear previous logs
    syncLogs.value = []
    syncProgress.value = 0
    
    // Add initial log entry
    syncLogs.value.push({
      timestamp: new Date().toISOString(),
      message: '🚀 Sync triggered - Waiting for logs...',
      level: 'info'
    })
    
    console.log('[Sync Monitor] Starting monitoring after sync trigger')
    // Start monitoring
    startMonitoring()
  } catch (error: any) {
    showError('Sync Failed', error.message)
    console.error('[Sync Monitor] Failed to trigger sync:', error)
  }
}

// Update interval
const handleUpdateInterval = async (newInterval: number) => {
  try {
    await syncStore.updateSyncInterval(newInterval)
    showSuccess('Interval Updated', `Sync interval set to ${newInterval} hours`)
  } catch (error: any) {
    showError('Update Failed', error.message)
  }
}

// Monitoring
let monitoringInterval: NodeJS.Timeout | null = null
let lastLogTimestamp: string | null = null
let lastProcessedLine: number = 0
let totalItems = 0
let currentItem = 0
let syncStartDetected = false
let syncCompleteDetected = false
let currentSessionId: string | null = null

// Process log entries (extracted for reuse)
const processLogEntries = (entries: any[]) => {
  for (const entry of entries) {
    // Skip if we've already processed this log
    if (lastLogTimestamp && entry.timestamp <= lastLogTimestamp) continue
    
    const message = entry.message || ''
    
    // Debug: Log each entry we're processing
    if (import.meta.dev && (message.includes('Processing') || message.includes('Found') || message.includes('Sync') || message.includes('======'))) {
      console.log('[Sync Monitor] Processing entry:', {
        timestamp: entry.timestamp,
        message: message,
        level: entry.level,
        category: entry.category
      })
    }
    
    // Detect sync start marker - "========== SYNC START"
    if (message.includes('========== SYNC START')) {
      syncStartDetected = true
      syncCompleteDetected = false
      
      // Extract session ID
      const sessionMatch = message.match(/Session: ([a-zA-Z0-9_-]+)/)
      if (sessionMatch) {
        currentSessionId = sessionMatch[1]
      }
      
      // Extract sync type (FULL or SINGLE)
      const typeMatch = message.match(/SYNC START \[(FULL|SINGLE)\]/)
      const syncType = typeMatch ? typeMatch[1] : 'FULL'
      
      syncLogs.value.push({
        timestamp: entry.timestamp,
        message: `🚀 Sync Started [${syncType}]`,
        level: 'info'
      })
      console.log('[Sync Monitor] Sync start detected:', { sessionId: currentSessionId, type: syncType })
    }
    
    // Detect sync complete marker - "========== SYNC COMPLETE"
    else if (message.includes('========== SYNC COMPLETE')) {
      syncCompleteDetected = true
      syncStartDetected = false
      syncProgress.value = 100
      
      // Extract status
      const statusMatch = message.match(/Status: (\w+)/)
      const status = statusMatch ? statusMatch[1] : 'UNKNOWN'
      
      syncLogs.value.push({
        timestamp: entry.timestamp,
        message: `✅ Sync Complete! Status: ${status}`,
        level: status === 'SUCCESS' ? 'success' : 'warning'
      })
      
      console.log('[Sync Monitor] Sync complete detected:', { sessionId: currentSessionId, status })
      
      // Stop monitoring after a brief delay
      setTimeout(() => {
        if (monitoringInterval) {
          clearInterval(monitoringInterval)
          monitoringInterval = null
        }
        showSuccess('Sync Complete', `Sync session ${currentSessionId || 'unknown'} completed`)
        currentSessionId = null
      }, 3000)
    }
    
    // Detect sync start - "🔍  Fetching items from"
    else if (message.includes('Fetching items from')) {
      if (!syncStartDetected) {
        syncStartDetected = true
        syncCompleteDetected = false
      }
      
      // Extract list type and name
      const listMatch = message.match(/Fetching items from (\w+) list: (.+)\.\.\./)
      let displayMsg = message
      if (listMatch) {
        displayMsg = `🔍 Fetching ${listMatch[1]} list: ${listMatch[2]}`
      }
      
      syncLogs.value.push({
        timestamp: entry.timestamp,
        message: displayMsg,
        level: 'info'
      })
    }
    
    // Detect items found - "✅  Found X items"
    else if (message.includes('Found') && message.includes('items in')) {
      const itemMatch = message.match(/Found (\d+) items/)
      if (itemMatch) {
        const foundItems = parseInt(itemMatch[1], 10)
        totalItems += foundItems
        
        syncLogs.value.push({
          timestamp: entry.timestamp,
          message: `✅ Found ${foundItems} items`,
          level: 'success'
        })
      }
    }
    
    // Detect total items ready for sync
    else if (message.includes('Total unique media items ready for sync')) {
      const totalMatch = message.match(/(\d+)/)
      if (totalMatch) {
        totalItems = parseInt(totalMatch[1], 10)
        
        syncLogs.value.push({
          timestamp: entry.timestamp,
          message: `📊 Total items to process: ${totalItems}`,
          level: 'info'
        })
      }
    }
    
    // Detect processing start
    else if (message.includes('Processing') && message.includes('media items')) {
      syncLogs.value.push({
        timestamp: entry.timestamp,
        message: '🎬 Starting item processing...',
        level: 'info'
      })
    }
    
    // Parse individual item progress - "(X/Y)"
    else if (message.match(/\((\d+)\/(\d+)\)/)) {
      const progressMatch = message.match(/\((\d+)\/(\d+)\)/)
      if (progressMatch) {
        currentItem = parseInt(progressMatch[1], 10)
        const total = parseInt(progressMatch[2], 10)
        totalItems = total // Update total if it changed
        
        // Calculate percentage
        syncProgress.value = Math.round((currentItem / totalItems) * 100)
        
        // Determine status icon and level
        let icon = '⏭️'
        let level = 'warning'
        
        if (message.includes('✅') || message.includes('Requested')) {
          icon = '✅'
          level = 'success'
        } else if (message.includes('☑️') || message.includes('Already Available')) {
          icon = '☑️'
          level = 'success'
        } else if (message.includes('❓') || message.includes('Not Found')) {
          icon = '❓'
          level = 'error'
        } else if (message.includes('❌') || message.includes('Error')) {
          icon = '❌'
          level = 'error'
        } else if (message.includes('📌') || message.includes('Already Requested')) {
          icon = '📌'
          level = 'info'
        }
        
        // Extract title
        const titleMatch = message.match(/^[⏭️✅☑️❓❌📌]\s+(.+?):\s+(Skipped|Requested|Already Available|Not Found|Error|Already Requested)/)
        let title = 'Processing item'
        if (titleMatch) {
          title = titleMatch[1]
        }
        
        // Only add every 5th item to avoid spam (or important status changes)
        if (currentItem % 5 === 0 || level === 'success' || level === 'error') {
          syncLogs.value.push({
            timestamp: entry.timestamp,
            message: `${icon} ${title} (${currentItem}/${totalItems})`,
            level
          })
        }
      }
    }
    
    // Detect summary section (sync complete)
    else if (message.includes('Soluify - List Sync Summary') || message.includes('------')) {
      if (message.includes('Summary') && !syncCompleteDetected) {
        syncCompleteDetected = true
        syncProgress.value = 100
        
        syncLogs.value.push({
          timestamp: entry.timestamp,
          message: '✅ Sync Complete! Processing summary...',
          level: 'success'
        })
        
        // Stop monitoring after a brief delay
        setTimeout(() => {
          if (monitoringInterval) {
            clearInterval(monitoringInterval)
            monitoringInterval = null
          }
          showSuccess('Sync Complete', `Successfully processed ${totalItems} items`)
        }, 3000)
      }
    }
    
    // Update last processed timestamp
    lastLogTimestamp = entry.timestamp
  }
  
  // Keep only last 150 logs for performance
  if (syncLogs.value.length > 150) {
    syncLogs.value = syncLogs.value.slice(-150)
  }
}

const startMonitoring = () => {
  console.log('[Sync Monitor] Starting monitoring...')
  
  // Clear previous state
  syncLogs.value = []
  syncProgress.value = 0
  lastLogTimestamp = null
  lastProcessedLine = 0
  totalItems = 0
  currentItem = 0
  syncStartDetected = false
  syncCompleteDetected = false
  currentSessionId = null

  // Clear any existing interval
  if (monitoringInterval) {
    clearInterval(monitoringInterval)
  }

  // Poll for live logs using /api/logs/live endpoint
  monitoringInterval = setInterval(async () => {
    console.log('[Sync Monitor] Polling for live logs...')
    try {
      // Fetch live logs from the /api/logs/live endpoint
      const response: any = await $fetch('/api/logs/live')
      
      // Debug logging
      console.log('[Sync Monitor] Live logs response:', {
        success: response.success,
        totalLines: response.total_lines,
        lastProcessedLine
      })
      
      if (!response || !response.success || !response.lines) {
        console.warn('[Sync Monitor] No logs found in response:', response)
        
        // Fallback to entries endpoint
        try {
          const altResponse: any = await $fetch('/api/logs/entries?page=1&limit=50&sort_order=desc')
          if (altResponse && altResponse.entries && altResponse.entries.length > 0) {
            console.log('[Sync Monitor] Using fallback entries endpoint:', altResponse.entries.length)
            processLogEntries(altResponse.entries)
            return
          }
        } catch (altError) {
          console.warn('[Sync Monitor] Fallback also failed:', altError)
        }
        return
      }
      
      const lines = response.lines
      
      // Process only new lines since last check
      const newLines = lines.slice(lastProcessedLine)
      lastProcessedLine = lines.length
      
      // Parse each line and convert to entry format
      for (const line of newLines) {
        if (!line.trim()) continue
        
        // Parse log line format: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - message
        const logMatch = line.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+-\s+(\w+)\s+-\s+(.+)$/)
        
        if (logMatch) {
          const [, timestamp, level, message] = logMatch
          const entry = {
            timestamp: timestamp.replace(',', '.'),
            level: level.toLowerCase(),
            message: message.trim(),
            category: 'sync'
          }
          
          // Process this entry using our existing logic
          processLogEntries([entry])
        } else if (line.includes('==========') || line.includes('🔍') || line.includes('✅') || line.includes('📊')) {
          // Handle unformatted lines (like print statements)
          const entry = {
            timestamp: new Date().toISOString(),
            level: 'info',
            message: line.trim(),
            category: 'sync'
          }
          processLogEntries([entry])
        }
      }
      
    } catch (error: any) {
      console.error('[Sync Monitor] Error fetching live logs:', error)
      
      // Show user-friendly error after multiple failures
      if (syncLogs.value.length === 0) {
        syncLogs.value.push({
          timestamp: new Date().toISOString(),
          message: `⚠️ Unable to fetch sync logs: ${error.message || 'Connection error'}`,
          level: 'warning'
        })
      }
      
      // Add debug info
      if (import.meta.dev) {
        console.error('[Sync Monitor] Full error details:', {
          error: error,
          message: error.message,
          stack: error.stack,
          response: error.response
        })
      }
    }
  }, 1000) // Poll every 1 second for responsive updates
}

// Cleanup on unmount
onUnmounted(() => {
  if (monitoringInterval) {
    clearInterval(monitoringInterval)
  }
})

// Fetch data on mount
onMounted(async () => {
  await fetchSyncData()
  
  // Test log API on mount
  if (process.client) {
    try {
      const testResponse = await $fetch('/api/logs/entries?page=1&limit=5&sort_order=desc')
      console.log('[Sync Monitor] Test API call result:', testResponse)
    } catch (error) {
      console.error('[Sync Monitor] Test API call failed:', error)
    }
  }
  
  // Auto-refresh every 30 seconds (client-side only)
  if (process.client) {
    const { startPolling } = useSmartPolling(async () => {
      await Promise.all([
        syncStore.fetchLiveSyncStatus(),
        systemStore.checkHealth(),
      ])
    }, 30000)
    
    startPolling()

    // Check if sync is running and start monitoring
    console.log('[Sync Monitor] Checking if sync is running:', syncStore.isSyncing)
    if (syncStore.isSyncing) {
      console.log('[Sync Monitor] Sync is running, starting monitoring...')
      startMonitoring()
    } else {
      console.log('[Sync Monitor] No sync running, monitoring not started')
    }
  }
})
</script>

