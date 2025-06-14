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
  Clock,
  Filter,
  X
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
  
  // Filter states
  const [selectedLevels, setSelectedLevels] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  
  const limit = 50

  // Available filter options
  const logLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
  const logCategories = ['general', 'sync', 'webhook', 'fetching', 'items', 'scraping', 'matching', 'api', 'process']

  // Fetch log entries
  const fetchLogEntries = async (page = 1, search = '', levels: string[] = [], categories: string[] = []) => {
    try {
      setError(null)
      setRefreshing(true)
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_order: 'desc',
      })
      
      if (search) params.append('search', search)
      if (levels.length > 0) {
        levels.forEach(level => params.append('level', level))
      }
      if (categories.length > 0) {
        categories.forEach(category => params.append('category', category))
      }

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
    fetchLogEntries(1, searchTerm, selectedLevels, selectedCategories)
  }

  // Handle filter changes
  const handleLevelChange = (level: string) => {
    const newLevels = selectedLevels.includes(level)
      ? selectedLevels.filter(l => l !== level)
      : [...selectedLevels, level]
    
    setSelectedLevels(newLevels)
    setCurrentPage(1)
    fetchLogEntries(1, searchTerm, newLevels, selectedCategories)
  }

  const handleCategoryChange = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category]
    
    setSelectedCategories(newCategories)
    setCurrentPage(1)
    fetchLogEntries(1, searchTerm, selectedLevels, newCategories)
  }

  // Clear all filters
  const clearFilters = () => {
    setSelectedLevels([])
    setSelectedCategories([])
    setCurrentPage(1)
    fetchLogEntries(1, searchTerm, [], [])
  }

  // Handle page navigation
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
      fetchLogEntries(page, searchTerm, selectedLevels, selectedCategories)
    }
  }

  // Initial load
  useEffect(() => {
    fetchLogEntries()
  }, [])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchLogEntries(currentPage, searchTerm, selectedLevels, selectedCategories)
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [currentPage, searchTerm, selectedLevels, selectedCategories])

  // Get icon for log level
  const getLevelIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-400" />
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-amber-400" />
      case 'INFO':
        return <Info className="h-4 w-4 text-purple-400" />
      case 'DEBUG':
        return <Settings className="h-4 w-4 text-gray-400" />
      default:
        return <Info className="h-4 w-4 text-gray-400" />
    }
  }

  // Get button style for log level
  const getLevelButtonStyle = (level: string, isSelected: boolean) => {
    const baseStyle = "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 border-2 hover:scale-105"
    
    switch (level.toUpperCase()) {
      case 'ERROR':
        return `${baseStyle} ${isSelected 
          ? 'bg-red-500/30 border-red-400/60 text-red-200 shadow-lg shadow-red-500/20' 
          : 'bg-red-500/10 border-red-500/30 text-red-300 hover:bg-red-500/20 hover:border-red-400/50'}`
      case 'WARNING':
        return `${baseStyle} ${isSelected 
          ? 'bg-amber-500/30 border-amber-400/60 text-amber-200 shadow-lg shadow-amber-500/20' 
          : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20 hover:border-amber-400/50'}`
      case 'INFO':
        return `${baseStyle} ${isSelected 
          ? 'bg-purple-500/30 border-purple-400/60 text-purple-200 shadow-lg shadow-purple-500/20' 
          : 'bg-purple-500/10 border-purple-500/30 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400/50'}`
      case 'DEBUG':
        return `${baseStyle} ${isSelected 
          ? 'bg-gray-500/30 border-gray-400/60 text-gray-200 shadow-lg shadow-gray-500/20' 
          : 'bg-gray-500/10 border-gray-500/30 text-gray-300 hover:bg-gray-500/20 hover:border-gray-400/50'}`
      default:
        return `${baseStyle} ${isSelected 
          ? 'bg-gray-500/30 border-gray-400/60 text-gray-200' 
          : 'bg-gray-500/10 border-gray-500/30 text-gray-300 hover:bg-gray-500/20'}`
    }
  }

  // Get icon for category
  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'sync':
        return <RefreshCw className="h-4 w-4" />
      case 'fetching':
        return <Globe className="h-4 w-4" />
      case 'items':
        return <Database className="h-4 w-4" />
      case 'scraping':
        return <Zap className="h-4 w-4" />
      case 'matching':
        return <CheckCircle className="h-4 w-4" />
      case 'api':
        return <Globe className="h-4 w-4" />
      case 'webhook':
        return <Zap className="h-4 w-4" />
      case 'process':
        return <Settings className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  // Get button style for category
  const getCategoryButtonStyle = (category: string, isSelected: boolean) => {
    const baseStyle = "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 border-2 hover:scale-105"
    
    // Use purple variants for most categories, gray for neutral ones
    const isPurpleCategory = ['sync', 'fetching', 'items', 'scraping', 'matching', 'api', 'webhook'].includes(category.toLowerCase())
    
    if (isPurpleCategory) {
      return `${baseStyle} ${isSelected 
        ? 'bg-purple-500/30 border-purple-400/60 text-purple-200 shadow-lg shadow-purple-500/20' 
        : 'bg-purple-500/10 border-purple-500/30 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400/50'}`
    } else {
      return `${baseStyle} ${isSelected 
        ? 'bg-gray-500/30 border-gray-400/60 text-gray-200 shadow-lg shadow-gray-500/20' 
        : 'bg-gray-500/10 border-gray-500/30 text-gray-300 hover:bg-gray-500/20 hover:border-gray-400/50'}`
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
      <div className="min-h-screen p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
            <div className="space-y-4">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="h-16 bg-white/10 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white titillium-web-bold">Activity Logs</h1>
            <p className="text-white/70 titillium-web-light">
              Recent activity from your sync operations • Auto-refreshes every 30s
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showFilters 
                  ? 'bg-purple-600/30 border border-purple-500/50 text-purple-300' 
                  : 'bg-purple-600/20 border border-purple-500/30 text-purple-300 hover:bg-purple-600/30'
              }`}
            >
              <Filter className="h-4 w-4" />
              Filters
              {(selectedLevels.length > 0 || selectedCategories.length > 0) && (
                <span className="bg-purple-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {selectedLevels.length + selectedCategories.length}
                </span>
              )}
            </button>
            <button
              onClick={() => fetchLogEntries(currentPage, searchTerm, selectedLevels, selectedCategories)}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-300 hover:bg-purple-600/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="glass-card p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white titillium-web-semibold">Filter Options</h3>
              {(selectedLevels.length > 0 || selectedCategories.length > 0) && (
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 hover:bg-red-500/30 transition-colors font-medium"
                >
                  <X className="h-4 w-4" />
                  Clear All Filters
                </button>
              )}
            </div>
            
            <div className="space-y-8">
              {/* Log Levels */}
              <div>
                <h4 className="text-lg font-medium text-white/90 mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-purple-400" />
                  Log Levels
                </h4>
                <div className="flex flex-wrap gap-3">
                  {logLevels.map((level) => (
                    <button
                      key={level}
                      onClick={() => handleLevelChange(level)}
                      className={getLevelButtonStyle(level, selectedLevels.includes(level))}
                    >
                      {getLevelIcon(level)}
                      <span className="text-sm font-medium">{level}</span>
                      {selectedLevels.includes(level) && (
                        <div className="w-2 h-2 bg-current rounded-full ml-1"></div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Categories */}
              <div>
                <h4 className="text-lg font-medium text-white/90 mb-4 flex items-center gap-2">
                  <Settings className="h-5 w-5 text-purple-400" />
                  Categories
                </h4>
                <div className="flex flex-wrap gap-3">
                  {logCategories.map((category) => (
                    <button
                      key={category}
                      onClick={() => handleCategoryChange(category)}
                      className={getCategoryButtonStyle(category, selectedCategories.includes(category))}
                    >
                      {getCategoryIcon(category)}
                      <span className="text-sm font-medium capitalize">{category}</span>
                      {selectedCategories.includes(category) && (
                        <div className="w-2 h-2 bg-current rounded-full ml-1"></div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

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
                className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              Search
            </button>
          </div>
        </div>

        {/* Active Filters Display */}
        {(selectedLevels.length > 0 || selectedCategories.length > 0) && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-white/60">Active filters:</span>
            {selectedLevels.map((level) => (
              <span
                key={`level-${level}`}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-xs text-purple-300"
              >
                Level: {level}
                <button
                  onClick={() => handleLevelChange(level)}
                  className="hover:bg-white/10 rounded-full p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {selectedCategories.map((category) => (
              <span
                key={`category-${category}`}
                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-500/20 border border-gray-500/30 rounded-full text-xs text-gray-300"
              >
                {category}
                <button
                  onClick={() => handleCategoryChange(category)}
                  className="hover:bg-white/10 rounded-full p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="glass-card p-4 border-red-400/30 bg-red-400/10">
            <div className="flex items-center gap-3">
              <XCircle className="h-5 w-5 text-red-400" />
              <span className="text-red-300">{error}</span>
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
              <div className="text-sm text-white/60">
                Page {currentPage} of {totalPages}
              </div>
            </div>
          </div>

          <div className="divide-y divide-white/10">
            {entries.map((entry) => (
              <div key={entry.id} className="p-4 hover:bg-white/5 transition-colors">
                <div className="flex items-start gap-3">
                  {/* Level Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getLevelIcon(entry.level)}
                  </div>

                  {/* Category Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getCategoryIcon(entry.category)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-purple-300 bg-purple-500/20 px-2 py-1 rounded border border-purple-500/30">
                        {entry.level}
                      </span>
                      <span className="text-xs font-medium text-gray-300 bg-gray-500/20 px-2 py-1 rounded border border-gray-500/30">
                        {entry.category}
                      </span>
                      <span className="text-xs text-white/50">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    </div>
                    
                    <div className="text-sm text-white/90 break-words">
                      {entry.message}
                    </div>
                    
                    {/* Media Info */}
                    {entry.media_info && (
                      <div className="mt-2 text-xs text-white/60">
                        {entry.media_info.title && (
                          <span className="mr-3">
                            📺 {entry.media_info.title}
                            {entry.media_info.year && ` (${entry.media_info.year})`}
                          </span>
                        )}
                        {entry.media_info.position && entry.media_info.position > 0 && (
                          <span className="mr-3">
                            #{entry.media_info.position}
                          </span>
                        )}
                        {entry.media_info.score && (
                          <span>
                            ⭐ {entry.media_info.score}%
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
                  className="flex items-center gap-2 px-3 py-2 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-300 hover:bg-purple-600/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>

                <div className="flex items-center gap-2">
                  <span className="text-sm text-white/70">
                    Page {currentPage} of {totalPages}
                  </span>
                </div>

                <button
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="flex items-center gap-2 px-3 py-2 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-300 hover:bg-purple-600/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 