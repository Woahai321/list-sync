"use client"

import { useState, useEffect } from 'react'
import { 
  Activity, 
  Search, 
  RefreshCw, 
  AlertTriangle, 
  Info, 
  CheckCircle, 
  XCircle,
  Database,
  Globe,
  Zap,
  Settings,
  ChevronLeft,
  ChevronRight,
  Clock
} from 'lucide-react'

// Types for log data
interface LogEntry {
  id: string
  timestamp: string
  level: string
  category: string
  message: string
  raw_line: string
  media_info?: {
    title?: string
    year?: number
    imdb_id?: string
    source?: string
    position?: number
    score?: number
  }
}

interface LogResponse {
  entries: LogEntry[]
  total_count: number
  has_more: boolean
  pagination: {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export default function ActivityPage() {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  
  const limit = 50

  // Fetch log entries
  const fetchLogEntries = async (page = 1, search = '') => {
    try {
      setError(null)
      if (page === currentPage && !search) {
        setRefreshing(true)
      }
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_order: 'desc',
      })
      
      if (search) params.append('search', search)
      
      const response = await fetch(`/api/logs/entries?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data: LogResponse = await response.json()
      
      setEntries(data.entries)
      setCurrentPage(data.pagination.page)
      setTotalPages(data.pagination.total_pages)
      setTotalCount(data.pagination.total_items)
      
    } catch (err) {
      console.error('Error fetching log entries:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch log entries')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // Handle search
  const handleSearch = () => {
    setCurrentPage(1)
    fetchLogEntries(1, searchTerm)
  }

  // Handle page navigation
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
      fetchLogEntries(page, searchTerm)
    }
  }

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchLogEntries()
    
    const interval = setInterval(() => {
      if (!searchTerm) { // Only auto-refresh if not searching
        fetchLogEntries(currentPage, searchTerm)
      }
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [currentPage, searchTerm])

  // Get color for log level
  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'bg-red-500/20 text-red-300 border-red-500/30'
      case 'WARNING':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
      case 'INFO':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'DEBUG':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
  }

  // Get color for category
  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'sync':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'fetching':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'items':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'scraping':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'matching':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'api':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'webhook':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30'
      case 'process':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      case 'general':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
  }

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return timestamp.slice(11, 19) // Fallback to string slice
    }
  }

  if (loading && entries.length === 0) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
          <div className="space-y-4">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-16 bg-white/10 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">Activity Logs</h1>
          <p className="text-purple-200/70 titillium-web-light">
            Recent activity from your sync operations • Auto-refreshes every 30s
          </p>
        </div>
        <button
          onClick={() => fetchLogEntries(currentPage, searchTerm)}
          disabled={refreshing}
          className="glass-button flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-purple-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="text-purple-200 titillium-web-regular">Refresh</span>
        </button>
      </div>

      {/* Search */}
      <div className="glass-card p-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/50" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-400 titillium-web-regular"
            />
          </div>
          <button
            onClick={handleSearch}
            className="glass-button-primary px-4 py-2 rounded-lg transition-all duration-300 titillium-web-semibold"
          >
            Search
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass-card p-4 border-red-400/30 bg-red-400/10">
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 text-red-400" />
            <span className="text-red-300 titillium-web-regular">{error}</span>
          </div>
        </div>
      )}

      {/* Log Entries */}
      <div className="glass-card">
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white titillium-web-semibold">
              Log Entries ({totalCount.toLocaleString()} total)
            </h2>
            <div className="text-sm text-white/60 titillium-web-light">
              Page {currentPage} of {totalPages}
            </div>
          </div>
        </div>

        <div className="p-4 space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="bg-white/5 hover:bg-white/10 transition-colors rounded-lg border border-white/10 p-4">
              <div className="flex items-start gap-3">
                {/* Timestamp */}
                <div className="flex-shrink-0 text-xs text-white/50 font-mono min-w-[60px] titillium-web-light">
                  {formatTimestamp(entry.timestamp)}
                </div>

                {/* Level Badge */}
                <div className="flex-shrink-0">
                  <span className={`text-xs font-medium px-2 py-1 rounded border titillium-web-semibold ${getLevelColor(entry.level)}`}>
                    {entry.level}
                  </span>
                </div>

                {/* Category Badge */}
                <div className="flex-shrink-0">
                  <span className={`text-xs font-medium px-2 py-1 rounded border titillium-web-semibold ${getCategoryColor(entry.category)}`}>
                    {entry.category}
                  </span>
                </div>

                {/* Message */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white/90 break-words font-mono titillium-web-regular">
                    {entry.message}
                  </div>
                  
                  {/* Media Info Display (if available) */}
                  {entry.media_info && (
                    <div className="mt-2 text-xs text-white/60 titillium-web-light">
                      {entry.media_info.title && (
                        <span className="mr-3">
                          📺 {entry.media_info.title}
                          {entry.media_info.year && ` (${entry.media_info.year})`}
                        </span>
                      )}
                      {entry.media_info.score && (
                        <span>
                          ⭐ {(entry.media_info.score * 100).toFixed(4)}%
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center justify-between">
              <button
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage <= 1}
                className="glass-button flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4 text-purple-400" />
                <span className="text-purple-200 titillium-web-regular">Previous</span>
              </button>

              <div className="flex items-center gap-2">
                <span className="text-sm text-white/70 titillium-web-light">
                  Page {currentPage} of {totalPages}
                </span>
              </div>

              <button
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="glass-button flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="text-purple-200 titillium-web-regular">Next</span>
                <ChevronRight className="h-4 w-4 text-purple-400" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 