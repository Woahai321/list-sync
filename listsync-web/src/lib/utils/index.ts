import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date))
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const target = new Date(date)
  const diffInSeconds = Math.floor((now.getTime() - target.getTime()) / 1000)

  if (diffInSeconds < 60) {
    return "just now"
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`
  }

  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) {
    return `${diffInHours}h ago`
  }

  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 7) {
    return `${diffInDays}d ago`
  }

  return formatDate(date)
}

export function formatFutureTime(date: string | Date): string {
  const now = new Date()
  const target = new Date(date)
  const diffInSeconds = Math.floor((target.getTime() - now.getTime()) / 1000)

  // If it's in the past, show as overdue
  if (diffInSeconds < 0) {
    const pastSeconds = Math.abs(diffInSeconds)
    if (pastSeconds < 60) {
      return "overdue"
    }
    const pastMinutes = Math.floor(pastSeconds / 60)
    if (pastMinutes < 60) {
      return `${pastMinutes}m overdue`
    }
    const pastHours = Math.floor(pastMinutes / 60)
    if (pastHours < 24) {
      return `${pastHours}h overdue`
    }
    return "overdue"
  }

  // Future time
  if (diffInSeconds < 60) {
    return "in less than 1m"
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (diffInMinutes < 60) {
    return `in ${diffInMinutes}m`
  }

  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) {
    return `in ${diffInHours}h ${diffInMinutes % 60}m`
  }

  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 7) {
    return `in ${diffInDays}d ${diffInHours % 24}h`
  }

  return formatDate(date)
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`
  }
  return `${secs}s`
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

export function formatPercentage(value: number, total: number): string {
  if (total === 0) return "0%"
  return `${Math.round((value / total) * 100)}%`
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + "..."
}

export function getListTypeColor(type: string): string {
  const colors = {
    imdb: "bg-yellow-500/20 text-yellow-300 border-yellow-400/30",
    trakt: "bg-red-500/20 text-red-300 border-red-400/30", 
    letterboxd: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
    mdblist: "bg-blue-500/20 text-blue-300 border-blue-400/30",
    stevenlu: "bg-purple-500/20 text-purple-300 border-purple-400/30",
  }
  return colors[type as keyof typeof colors] || "bg-gray-500/20 text-gray-300 border-gray-400/30"
}

export function getStatusColor(status: string): string {
  const colors = {
    pending: "bg-amber-500/20 text-amber-300 border-amber-400/30",
    available: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
    requested: "bg-blue-500/20 text-blue-300 border-blue-400/30",
    failed: "bg-red-500/20 text-red-300 border-red-400/30",
    running: "bg-purple-500/20 text-purple-300 border-purple-400/30",
    completed: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
    cancelled: "bg-gray-500/20 text-gray-300 border-gray-400/30",
    active: "bg-emerald-500/20 text-emerald-300 border-emerald-400/30",
    inactive: "bg-gray-500/20 text-gray-300 border-gray-400/30",
    error: "bg-red-500/20 text-red-300 border-red-400/30",
  }
  return colors[status as keyof typeof colors] || "bg-gray-500/20 text-gray-300 border-gray-400/30"
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

export function isValidUrl(string: string): boolean {
  try {
    new URL(string)
    return true
  } catch {
    return false
  }
} 