/**
 * SSE-based sync monitoring composable
 * Connects to the backend SSE endpoint for real-time sync updates
 */

import { ref, onMounted, onUnmounted } from 'vue'

export interface SyncEvent {
  type: 'log' | 'progress' | 'status' | 'error'
  data: any
  timestamp: string
}

export const useSyncMonitor = () => {
  const isConnected = ref(false)
  const lastEvent = ref<SyncEvent | null>(null)
  const events = ref<SyncEvent[]>([])
  const error = ref<string | null>(null)
  
  let eventSource: EventSource | null = null
  let reconnectTimeout: NodeJS.Timeout | null = null
  const maxReconnectAttempts = 5
  let reconnectAttempts = 0

  const connect = () => {
    if (!process.client) return

    // Clean up existing connection
    disconnect()

    const config = useRuntimeConfig()
    const apiUrl = config.public.apiUrl || 'http://localhost:4222'
    
    try {
      // Note: SSE endpoint may not exist yet in the backend
      // This is a placeholder for when it's implemented
      eventSource = new EventSource(`${apiUrl}/api/sync/status/live`)

      eventSource.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts = 0
        console.log('[SSE] Connected to sync monitor')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const syncEvent: SyncEvent = {
            type: data.type || 'log',
            data: data,
            timestamp: new Date().toISOString(),
          }

          lastEvent.value = syncEvent
          events.value.push(syncEvent)

          // Keep only last 100 events
          if (events.value.length > 100) {
            events.value.shift()
          }

          // Update sync store based on event type
          const syncStore = useSyncStore()
          
          if (syncEvent.type === 'status') {
            syncStore.isSyncing = data.is_syncing || false
            syncStore.syncStatus = data.status || 'idle'
          }
        } catch (err) {
          console.error('[SSE] Failed to parse event:', err)
        }
      }

      // Event types
      eventSource.addEventListener('log', (event: any) => {
        const data = JSON.parse(event.data)
        const syncEvent: SyncEvent = {
          type: 'log',
          data,
          timestamp: new Date().toISOString(),
        }
        lastEvent.value = syncEvent
        events.value.push(syncEvent)
      })

      eventSource.addEventListener('progress', (event: any) => {
        const data = JSON.parse(event.data)
        const syncEvent: SyncEvent = {
          type: 'progress',
          data,
          timestamp: new Date().toISOString(),
        }
        lastEvent.value = syncEvent
      })

      eventSource.onerror = (err) => {
        console.error('[SSE] Connection error:', err)
        isConnected.value = false
        error.value = 'Connection lost'

        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`)
          
          reconnectTimeout = setTimeout(() => {
            connect()
          }, delay)
        } else {
          error.value = 'Failed to connect after multiple attempts'
          eventSource?.close()
        }
      }
    } catch (err) {
      console.error('[SSE] Failed to create EventSource:', err)
      error.value = 'Failed to establish connection'
      isConnected.value = false
    }
  }

  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }

    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    isConnected.value = false
  }

  const retry = () => {
    reconnectAttempts = 0
    connect()
  }

  const clearEvents = () => {
    events.value = []
    lastEvent.value = null
  }

  // Auto-connect on mount (client-side only)
  // DISABLED: Endpoint doesn't support SSE yet, returns JSON instead
  // TODO: Enable when backend implements SSE endpoint
  onMounted(() => {
    // Disabled until backend supports SSE
    // if (process.client) {
    //   // Try to connect, but don't fail if SSE endpoint doesn't exist
    //   connect()
    // }
  })

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    lastEvent,
    events,
    error,
    connect,
    disconnect,
    retry,
    clearEvents,
  }
}

