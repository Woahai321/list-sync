/**
 * Utility Formatters
 * Pure functions for formatting data
 */

import { formatDistanceToNow, formatDistance, format as formatDateFn } from 'date-fns'

/**
 * Format a date to relative time ("2 hours ago")
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return 'Never'

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    if (isNaN(dateObj.getTime())) return 'Invalid date'

    return formatDistanceToNow(dateObj, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Invalid date'
  }
}

/**
 * Format a future date ("in 3 hours")
 */
export function formatFutureTime(date: string | Date | null | undefined): string {
  if (!date) return 'Not scheduled'

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    if (isNaN(dateObj.getTime())) return 'Invalid date'

    const now = new Date()
    const diff = dateObj.getTime() - now.getTime()

    if (diff <= 0) return 'Overdue'

    return formatDistance(now, dateObj, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting future time:', error)
    return 'Invalid date'
  }
}

/**
 * Format a date with custom format string
 */
export function formatDate(
  date: string | Date | null | undefined,
  formatString: string = 'MMM dd, yyyy HH:mm'
): string {
  if (!date) return 'N/A'

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    
    if (isNaN(dateObj.getTime())) return 'Invalid date'

    return formatDateFn(dateObj, formatString)
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid date'
  }
}

/**
 * Format a number with commas (1234567 -> 1,234,567)
 */
export function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

/**
 * Format a large number to compact form (1234567 -> 1.2M)
 */
export function formatCompactNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return '0'

  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }

  return num.toString()
}

/**
 * Format a percentage (0.756 -> 75.6%)
 */
export function formatPercentage(
  value: number | null | undefined,
  decimals: number = 1
): string {
  if (value === null || value === undefined) return '0%'
  return `${value.toFixed(decimals)}%`
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * Format duration in milliseconds to human-readable format
 */
export function formatDuration(ms: number | null | undefined): string {
  if (!ms) return '0s'

  const seconds = Math.floor((ms / 1000) % 60)
  const minutes = Math.floor((ms / (1000 * 60)) % 60)
  const hours = Math.floor((ms / (1000 * 60 * 60)) % 24)
  const days = Math.floor(ms / (1000 * 60 * 60 * 24))

  const parts = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  if (seconds > 0 && days === 0) parts.push(`${seconds}s`)

  return parts.join(' ') || '0s'
}

/**
 * Truncate text to a maximum length
 */
export function truncate(
  text: string | null | undefined,
  maxLength: number = 50,
  suffix: string = '...'
): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - suffix.length) + suffix
}

/**
 * Capitalize first letter of a string
 */
export function capitalize(text: string | null | undefined): string {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/**
 * Convert snake_case to Title Case
 */
export function snakeToTitle(text: string | null | undefined): string {
  if (!text) return ''
  
  return text
    .split('_')
    .map(word => capitalize(word))
    .join(' ')
}

/**
 * Format media type to display name
 */
export function formatMediaType(type: string | null | undefined): string {
  if (!type) return 'Unknown'
  
  const types: Record<string, string> = {
    'movie': 'Movie',
    'tv': 'TV Show',
    'show': 'TV Show',
  }

  return types[type.toLowerCase()] || capitalize(type)
}

/**
 * Format list source to display name
 */
export function formatListSource(source: string | null | undefined): string {
  if (!source) return 'Unknown'

  const sources: Record<string, string> = {
    'imdb': 'IMDb',
    'trakt': 'Trakt',
    'trakt_special': 'Trakt Special',
    'letterboxd': 'Letterboxd',
    'mdblist': 'MDBList',
    'stevenlu': 'Steven Lu',
  }

  return sources[source.toLowerCase()] || capitalize(source)
}

/**
 * Format status to display name with color
 */
export function formatStatus(status: string | null | undefined): {
  text: string
  color: string
} {
  if (!status) return { text: 'Unknown', color: 'gray' }

  const statusMap: Record<string, { text: string; color: string }> = {
    'pending': { text: 'Pending', color: 'yellow' },
    'requested': { text: 'Requested', color: 'blue' },
    'available': { text: 'Available', color: 'green' },
    'failed': { text: 'Failed', color: 'red' },
    'error': { text: 'Error', color: 'red' },
    'success': { text: 'Success', color: 'green' },
    'skipped': { text: 'Skipped', color: 'gray' },
    'running': { text: 'Running', color: 'purple' },
    'completed': { text: 'Completed', color: 'green' },
    'cancelled': { text: 'Cancelled', color: 'gray' },
  }

  return statusMap[status.toLowerCase()] || { text: capitalize(status), color: 'gray' }
}

/**
 * Generate initials from a name
 */
export function getInitials(name: string | null | undefined): string {
  if (!name) return '?'

  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }

  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * Parse and format a sync interval to readable text
 */
export function formatSyncInterval(hours: number | null | undefined): string {
  if (!hours) return 'Not set'

  if (hours < 1) {
    return `${Math.round(hours * 60)} minutes`
  }

  if (hours === 1) return '1 hour'
  if (hours < 24) return `${hours} hours`
  
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24

  if (remainingHours === 0) {
    return days === 1 ? '1 day' : `${days} days`
  }

  return `${days}d ${remainingHours}h`
}

