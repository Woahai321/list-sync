/**
 * Time Utilities Composable
 * Provides reactive time management and formatting
 */

import { formatDistanceToNow, formatDistance, format as formatDate } from 'date-fns'

/**
 * Live time composable - updates every interval
 */
export function useLiveTime(intervalMs: number = 1000) {
  const currentTime = ref(new Date())

  // Update time every interval
  const intervalId = ref<NodeJS.Timeout | null>(null)

  onMounted(() => {
    intervalId.value = setInterval(() => {
      currentTime.value = new Date()
    }, intervalMs)
  })

  onUnmounted(() => {
    if (intervalId.value) {
      clearInterval(intervalId.value)
    }
  })

  // Formatted outputs
  const formatted = computed(() => ({
    date: formatDate(currentTime.value, 'MMM dd, yyyy'),
    time: formatDate(currentTime.value, 'HH:mm:ss'),
    full: formatDate(currentTime.value, 'MMM dd, yyyy HH:mm:ss'),
    iso: currentTime.value.toISOString(),
  }))

  return {
    currentTime,
    formatted,
  }
}

/**
 * Relative time composable - "2 hours ago"
 */
export function useRelativeTime(date: string | Date | Ref<string | Date | null>) {
  const dateRef = isRef(date) ? date : ref(date)

  const relativeTime = computed(() => {
    if (!dateRef.value) return null
    
    try {
      const dateObj = typeof dateRef.value === 'string' 
        ? new Date(dateRef.value) 
        : dateRef.value

      if (isNaN(dateObj.getTime())) return null

      return formatDistanceToNow(dateObj, { addSuffix: true })
    } catch (error) {
      console.error('Error formatting relative time:', error)
      return null
    }
  })

  return relativeTime
}

/**
 * Future time composable - "in 3 hours"
 */
export function useFutureTime(date: string | Date | Ref<string | Date | null>) {
  const dateRef = isRef(date) ? date : ref(date)

  const futureTime = computed(() => {
    if (!dateRef.value) return null
    
    try {
      const dateObj = typeof dateRef.value === 'string' 
        ? new Date(dateRef.value) 
        : dateRef.value

      if (isNaN(dateObj.getTime())) return null

      const now = new Date()
      return formatDistance(now, dateObj, { addSuffix: true })
    } catch (error) {
      console.error('Error formatting future time:', error)
      return null
    }
  })

  return futureTime
}

/**
 * Format a date/time string
 */
export function useFormattedDate(
  date: string | Date | Ref<string | Date | null>,
  formatString: string = 'MMM dd, yyyy HH:mm'
) {
  const dateRef = isRef(date) ? date : ref(date)

  const formattedDate = computed(() => {
    if (!dateRef.value) return null
    
    try {
      const dateObj = typeof dateRef.value === 'string' 
        ? new Date(dateRef.value) 
        : dateRef.value

      if (isNaN(dateObj.getTime())) return null

      return formatDate(dateObj, formatString)
    } catch (error) {
      console.error('Error formatting date:', error)
      return null
    }
  })

  return formattedDate
}

/**
 * Countdown timer composable
 */
export function useCountdown(targetDate: string | Date | Ref<string | Date | null>) {
  const targetRef = isRef(targetDate) ? targetDate : ref(targetDate)
  const timeRemaining = ref<number>(0)
  const isExpired = ref(false)

  const intervalId = ref<NodeJS.Timeout | null>(null)

  const updateCountdown = () => {
    if (!targetRef.value) {
      timeRemaining.value = 0
      isExpired.value = true
      return
    }

    const target = typeof targetRef.value === 'string' 
      ? new Date(targetRef.value) 
      : targetRef.value

    const now = new Date()
    const diff = target.getTime() - now.getTime()

    if (diff <= 0) {
      timeRemaining.value = 0
      isExpired.value = true
      if (intervalId.value) {
        clearInterval(intervalId.value)
      }
    } else {
      timeRemaining.value = diff
      isExpired.value = false
    }
  }

  onMounted(() => {
    updateCountdown()
    intervalId.value = setInterval(updateCountdown, 1000)
  })

  onUnmounted(() => {
    if (intervalId.value) {
      clearInterval(intervalId.value)
    }
  })

  const formatted = computed(() => {
    if (timeRemaining.value === 0) return '0s'

    const seconds = Math.floor((timeRemaining.value / 1000) % 60)
    const minutes = Math.floor((timeRemaining.value / (1000 * 60)) % 60)
    const hours = Math.floor((timeRemaining.value / (1000 * 60 * 60)) % 24)
    const days = Math.floor(timeRemaining.value / (1000 * 60 * 60 * 24))

    const parts = []
    if (days > 0) parts.push(`${days}d`)
    if (hours > 0) parts.push(`${hours}h`)
    if (minutes > 0) parts.push(`${minutes}m`)
    if (seconds > 0 && days === 0) parts.push(`${seconds}s`)

    return parts.join(' ')
  })

  return {
    timeRemaining,
    isExpired,
    formatted,
  }
}

