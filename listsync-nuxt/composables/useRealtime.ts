/**
 * Real-time Utilities Composable
 * Provides SSE and sync monitoring capabilities
 */

/**
 * Server-Sent Events (SSE) composable
 */
export function useSSE(endpoint: string) {
  const config = useRuntimeConfig()
  const baseURL = `${config.public.apiUrl}${config.public.apiBase}`
  
  const eventSource = ref<EventSource | null>(null)
  const data = ref<any>(null)
  const error = ref<string | null>(null)
  const status = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')

  /**
   * Connect to SSE endpoint
   */
  const connect = () => {
    if (eventSource.value) {
      return // Already connected
    }

    try {
      status.value = 'connecting'
      error.value = null

      const url = `${baseURL}${endpoint}`
      eventSource.value = new EventSource(url)

      eventSource.value.onopen = () => {
        status.value = 'connected'
        console.log(`SSE connected: ${endpoint}`)
      }

      eventSource.value.onmessage = (event) => {
        try {
          data.value = JSON.parse(event.data)
        } catch (err) {
          data.value = event.data
        }
      }

      eventSource.value.onerror = (err) => {
        console.error(`SSE error: ${endpoint}`, err)
        status.value = 'error'
        error.value = 'Connection error'
        disconnect()
      }
    } catch (err: any) {
      console.error(`Failed to connect to SSE: ${endpoint}`, err)
      status.value = 'error'
      error.value = err.message
    }
  }

  /**
   * Disconnect from SSE
   */
  const disconnect = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
      status.value = 'disconnected'
    }
  }

  /**
   * Reconnect to SSE
   */
  const reconnect = () => {
    disconnect()
    setTimeout(connect, 1000)
  }

  // Auto-connect on mount
  onMounted(() => {
    if (process.client) {
      connect()
    }
  })

  // Auto-disconnect on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    data: readonly(data),
    error: readonly(error),
    status: readonly(status),
    connect,
    disconnect,
    reconnect,
  }
}

/**
 * Smart polling composable - only polls when tab is active
 */
export function useSmartPolling(
  callback: () => void | Promise<void>,
  intervalMs: number = 30000
) {
  const intervalId = ref<NodeJS.Timeout | null>(null)
  const isActive = ref(true)
  const isPaused = ref(false)

  /**
   * Start polling
   */
  const startPolling = () => {
    if (intervalId.value) return

    intervalId.value = setInterval(async () => {
      if (isActive.value && !isPaused.value) {
        try {
          await callback()
        } catch (err) {
          console.error('Polling error:', err)
        }
      }
    }, intervalMs)

    // Initial call
    if (isActive.value && !isPaused.value) {
      callback()
    }
  }

  /**
   * Stop polling
   */
  const stopPolling = () => {
    if (intervalId.value) {
      clearInterval(intervalId.value)
      intervalId.value = null
    }
  }

  /**
   * Pause polling
   */
  const pause = () => {
    isPaused.value = true
  }

  /**
   * Resume polling
   */
  const resume = () => {
    isPaused.value = false
    // Immediate call on resume
    if (isActive.value) {
      callback()
    }
  }

  // Handle visibility change
  const handleVisibilityChange = () => {
    isActive.value = !document.hidden
    
    if (isActive.value && !isPaused.value) {
      // Immediate call when tab becomes active
      callback()
    }
  }

  // Setup visibility listener
  onMounted(() => {
    if (process.client) {
      document.addEventListener('visibilitychange', handleVisibilityChange)
      startPolling()
    }
  })

  // Cleanup
  onUnmounted(() => {
    if (process.client) {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
    stopPolling()
  })

  return {
    isActive: readonly(isActive),
    isPaused: readonly(isPaused),
    startPolling,
    stopPolling,
    pause,
    resume,
  }
}

