/**
 * Smart polling composable with visibility and focus detection
 * Automatically pauses when tab is not visible
 */

import { ref, onMounted, onUnmounted } from 'vue'

export interface PollingOptions {
  interval?: number
  immediate?: boolean
  pauseWhenHidden?: boolean
  onError?: (error: any) => void
}

export const usePolling = (
  callback: () => Promise<void> | void,
  options: PollingOptions = {}
) => {
  const {
    interval = 30000,
    immediate = true,
    pauseWhenHidden = true,
    onError,
  } = options

  const isPolling = ref(false)
  const isPaused = ref(false)
  const lastPollTime = ref<Date | null>(null)
  const errorCount = ref(0)

  let intervalId: NodeJS.Timeout | null = null

  const executePoll = async () => {
    if (isPaused.value) return

    try {
      await callback()
      lastPollTime.value = new Date()
      errorCount.value = 0
    } catch (error) {
      errorCount.value++
      console.error('[Polling] Error:', error)
      
      if (onError) {
        onError(error)
      }

      // Stop polling after 5 consecutive errors
      if (errorCount.value >= 5) {
        console.error('[Polling] Too many errors, stopping')
        stop()
      }
    }
  }

  const start = () => {
    if (isPolling.value) return

    isPolling.value = true
    isPaused.value = false

    // Execute immediately if requested
    if (immediate) {
      executePoll()
    }

    // Set up interval
    intervalId = setInterval(executePoll, interval)
  }

  const stop = () => {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
    isPolling.value = false
  }

  const pause = () => {
    isPaused.value = true
  }

  const resume = () => {
    isPaused.value = false
  }

  const reset = () => {
    errorCount.value = 0
    lastPollTime.value = null
  }

  // Handle visibility change
  const handleVisibilityChange = () => {
    if (!pauseWhenHidden || !process.client) return

    if (document.hidden) {
      pause()
    } else {
      resume()
      // Execute immediately when becoming visible
      if (isPolling.value) {
        executePoll()
      }
    }
  }

  // Setup visibility listener
  onMounted(() => {
    if (process.client && pauseWhenHidden) {
      document.addEventListener('visibilitychange', handleVisibilityChange)
    }
  })

  // Cleanup
  onUnmounted(() => {
    stop()
    if (process.client && pauseWhenHidden) {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  })

  return {
    isPolling,
    isPaused,
    lastPollTime,
    errorCount,
    start,
    stop,
    pause,
    resume,
    reset,
    startPolling: start, // Alias
  }
}

// Export alias for convenience
export const useSmartPolling = usePolling

