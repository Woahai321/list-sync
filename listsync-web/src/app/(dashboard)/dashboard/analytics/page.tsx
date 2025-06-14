"use client"

import { useState, useEffect } from 'react'
import { Clock, Activity, BarChart3, PieChart, AlertTriangle, TrendingUp } from 'lucide-react'

interface SyncRun {
  timestamp: string
  totalItems: number
  totalTime: string
  avgTimeMs: number
  requested: number
  available: number
  alreadyRequested: number
  skipped: number
  notFound: number
  movies: number
  tvShows: number
  notFoundItems: string[]
}

interface AnalyticsData {
  runs: SyncRun[]
  aggregated: {
    totalRuns: number
    avgProcessingTime: number
    avgItemsPerRun: number
    avgSpeedMs: number
    totalRequested: number
    totalAvailable: number
    totalAlreadyRequested: number
    totalSkipped: number
    totalNotFound: number
    totalMovies: number
    totalTvShows: number
    uniqueNotFoundItems: { title: string; count: number }[]
  }
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAnalyticsData()
  }, [])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch the log file content
      const response = await fetch('/api/analytics/log-data')
      if (!response.ok) {
        throw new Error('Failed to fetch log data')
      }
      
      const logContent = await response.text()
      const parsedData = parseLogData(logContent)
      setData(parsedData)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  const parseLogData = (logContent: string): AnalyticsData => {
    const lines = logContent.split('\n')
    const runs: SyncRun[] = []
    let currentRun: Partial<SyncRun> = {}
    let inSummary = false
    let notFoundItems: string[] = []

    for (const line of lines) {
      const trimmedLine = line.trim()
      
      // Detect start of a new sync run - look for various patterns
      if (trimmedLine.includes('Starting automated sync') || 
          trimmedLine.includes('Sync operation completed') ||
          trimmedLine.includes('starting in automated mode') ||
          trimmedLine.includes('List Sync Summary')) {
        if (Object.keys(currentRun).length > 0) {
          // Finish previous run
          if (currentRun.totalItems && currentRun.totalItems > 0) {
            currentRun.notFoundItems = [...notFoundItems]
            // Only set notFound from notFoundItems length if we didn't already get it from the header
            if (typeof currentRun.notFound !== 'number') {
              currentRun.notFound = notFoundItems.length
            }
            runs.push({
              timestamp: currentRun.timestamp || '',
              totalItems: currentRun.totalItems || 0,
              totalTime: currentRun.totalTime || '0s',
              avgTimeMs: currentRun.avgTimeMs || 0,
              requested: currentRun.requested || 0,
              available: currentRun.available || 0,
              alreadyRequested: currentRun.alreadyRequested || 0,
              skipped: currentRun.skipped || 0,
              notFound: currentRun.notFound || 0,
              movies: currentRun.movies || 0,
              tvShows: currentRun.tvShows || 0,
              notFoundItems: [...notFoundItems]
            })
          }
        }
        currentRun = {}
        inSummary = false
        notFoundItems = []
      }

      // Extract timestamp from any line with a timestamp
      if (!currentRun.timestamp && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(trimmedLine)) {
        currentRun.timestamp = trimmedLine.substring(0, 19)
      }

      // Detect summary section - look for "List Sync Summary" or other summary indicators
      if (trimmedLine.includes('List Sync Summary') || 
          trimmedLine.includes('Processing Stats') ||
          trimmedLine.includes('Results') ||
          (trimmedLine.includes('Summary') && !trimmedLine.includes('docker')) ||
          trimmedLine.includes('SUMMARY')) {
        inSummary = true
        continue
      }

      // Look for various data patterns throughout the log
      if (inSummary || trimmedLine.includes('✅') || trimmedLine.includes('☑️') || 
          trimmedLine.includes('📌') || trimmedLine.includes('⏭️')) {
        
        // Extract total items - handle various formats
        const totalItemsMatch = trimmedLine.match(/Total Items?:?\s*(\d+)/) ||
                               trimmedLine.match(/(\d+)\s*total items?/i) ||
                               trimmedLine.match(/processed\s*(\d+)\s*items?/i)
        if (totalItemsMatch) {
          currentRun.totalItems = parseInt(totalItemsMatch[1])
        }

        // Extract total time - handle various formats
        const totalTimeMatch = trimmedLine.match(/Total Time:?\s*([^\s]+(?:\s+[^\s]+)?)/) ||
                              trimmedLine.match(/took\s*(.+?)(?:\s|$)/) ||
                              trimmedLine.match(/completed in\s*(.+?)(?:\s|$)/)
        if (totalTimeMatch) {
          currentRun.totalTime = totalTimeMatch[1].trim()
        }

        // Extract avg time - handle various formats  
        const avgTimeMatch = trimmedLine.match(/Avg Time:?\s*([^\s]+)/) ||
                            trimmedLine.match(/average:?\s*(\d+\.?\d*)\s*ms/i) ||
                            trimmedLine.match(/(\d+\.?\d*)\s*ms\s*per\s*item/i)
        if (avgTimeMatch) {
          const avgTimeStr = avgTimeMatch[1]
          const msMatch = avgTimeStr.match(/(\d+\.?\d*)\s*ms/)
          if (msMatch) {
            currentRun.avgTimeMs = parseFloat(msMatch[1])
          }
        }

        // Extract status counts with improved patterns - more specific to avoid overlap
        if (trimmedLine.includes('✅') && trimmedLine.includes('Requested:')) {
          const requestedMatch = trimmedLine.match(/✅\s*Requested:?\s*(\d+)/)
          if (requestedMatch) {
            currentRun.requested = parseInt(requestedMatch[1])
          }
        }

        if (trimmedLine.includes('☑️') && trimmedLine.includes('Available:')) {
          const availableMatch = trimmedLine.match(/☑️\s*Available:?\s*(\d+)/)
          if (availableMatch) {
            currentRun.available = parseInt(availableMatch[1])
          }
        }

        if (trimmedLine.includes('📌') && trimmedLine.includes('Already Requested:')) {
          const alreadyRequestedMatch = trimmedLine.match(/📌\s*Already Requested:?\s*(\d+)/)
          if (alreadyRequestedMatch) {
            currentRun.alreadyRequested = parseInt(alreadyRequestedMatch[1])
          }
        }

        if (trimmedLine.includes('⏭️') && trimmedLine.includes('Skipped:')) {
          const skippedMatch = trimmedLine.match(/⏭️\s*Skipped:?\s*(\d+)/)
          if (skippedMatch) {
            currentRun.skipped = parseInt(skippedMatch[1])
          }
        }

        // Extract media types
        const moviesMatch = trimmedLine.match(/Movies?:?\s*(\d+)/) ||
                           trimmedLine.match(/(\d+)\s*movies?/i)
        if (moviesMatch) {
          currentRun.movies = parseInt(moviesMatch[1])
        }

        const tvShowsMatch = trimmedLine.match(/TV Shows?:?\s*(\d+)/) ||
                            trimmedLine.match(/(\d+)\s*tv\s*shows?/i) ||
                            trimmedLine.match(/(\d+)\s*series/i)
        if (tvShowsMatch) {
          currentRun.tvShows = parseInt(tvShowsMatch[1])
        }
      }

      // Extract "Not Found Items" count from the header line
      const notFoundHeaderMatch = trimmedLine.match(/Not Found Items?\s*\((\d+)\)/)
      if (notFoundHeaderMatch) {
        currentRun.notFound = parseInt(notFoundHeaderMatch[1])
      }

      // Extract individual not found items - look for various patterns
      if (trimmedLine.includes('not found') || trimmedLine.includes('Not Found') || trimmedLine.includes('❓')) {
        const patterns = [
          /• (.+?) \(\d+\) \(Not Found\)/,
          /❓ (.+?): Not Found/,
          /(.+?) - not found/i,
          /not found: (.+)/i,
          /• (.+?) \(Not Found\)/
        ]
        
        for (const pattern of patterns) {
          const match = trimmedLine.match(pattern)
          if (match && match[1]) {
            const itemTitle = match[1].trim()
            if (itemTitle && !notFoundItems.includes(itemTitle)) {
              notFoundItems.push(itemTitle)
            }
            break
          }
        }
      }
    }

    // Finish last run
    if (Object.keys(currentRun).length > 0) {
      currentRun.notFoundItems = [...notFoundItems]
      // Only set notFound from notFoundItems length if we didn't already get it from the header
      if (typeof currentRun.notFound !== 'number') {
        currentRun.notFound = notFoundItems.length
      }
      if (currentRun.totalItems && currentRun.totalItems > 0) {
        runs.push({
          timestamp: currentRun.timestamp || new Date().toISOString(),
          totalItems: currentRun.totalItems || 0,
          totalTime: currentRun.totalTime || '0s',
          avgTimeMs: currentRun.avgTimeMs || 0,
          requested: currentRun.requested || 0,
          available: currentRun.available || 0,
          alreadyRequested: currentRun.alreadyRequested || 0,
          skipped: currentRun.skipped || 0,
          notFound: currentRun.notFound || 0,
          movies: currentRun.movies || 0,
          tvShows: currentRun.tvShows || 0,
          notFoundItems: [...notFoundItems]
        })
      }
    }

    // If no runs found, create a dummy run to prevent NaN errors
    if (runs.length === 0) {
      runs.push({
        timestamp: new Date().toISOString(),
        totalItems: 0,
        totalTime: '0s',
        avgTimeMs: 0,
        requested: 0,
        available: 0,
        alreadyRequested: 0,
        skipped: 0,
        notFound: 0,
        movies: 0,
        tvShows: 0,
        notFoundItems: []
      })
    }

    // Calculate aggregated data with safety checks
    const totalRuns = runs.length
    const avgProcessingTime = runs.length > 0 
      ? runs.reduce((sum, run) => {
          const timeInSeconds = parseTimeToSeconds(run.totalTime)
          return sum + (isNaN(timeInSeconds) ? 0 : timeInSeconds)
        }, 0) / totalRuns 
      : 0

    const avgItemsPerRun = runs.length > 0 
      ? runs.reduce((sum, run) => sum + (run.totalItems || 0), 0) / totalRuns 
      : 0
      
    const avgSpeedMs = runs.length > 0 
      ? runs.reduce((sum, run) => sum + (run.avgTimeMs || 0), 0) / totalRuns 
      : 0

    const totalRequested = runs.reduce((sum, run) => sum + (run.requested || 0), 0)
    const totalAvailable = runs.reduce((sum, run) => sum + (run.available || 0), 0)
    const totalAlreadyRequested = runs.reduce((sum, run) => sum + (run.alreadyRequested || 0), 0)
    const totalSkipped = runs.reduce((sum, run) => sum + (run.skipped || 0), 0)
    const totalNotFound = runs.reduce((sum, run) => sum + (run.notFound || 0), 0)
    const totalMovies = runs.reduce((sum, run) => sum + (run.movies || 0), 0)
    const totalTvShows = runs.reduce((sum, run) => sum + (run.tvShows || 0), 0)

    // Get unique not found items with counts
    const notFoundMap = new Map<string, number>()
    runs.forEach(run => {
      run.notFoundItems?.forEach(item => {
        if (item && item.trim()) {
          notFoundMap.set(item, (notFoundMap.get(item) || 0) + 1)
        }
      })
    })
    const uniqueNotFoundItems = Array.from(notFoundMap.entries())
      .map(([title, count]) => ({ title, count }))
      .sort((a, b) => b.count - a.count)

    return {
      runs,
      aggregated: {
        totalRuns,
        avgProcessingTime: isNaN(avgProcessingTime) ? 0 : avgProcessingTime,
        avgItemsPerRun: isNaN(avgItemsPerRun) ? 0 : avgItemsPerRun,
        avgSpeedMs: isNaN(avgSpeedMs) ? 0 : avgSpeedMs,
        totalRequested,
        totalAvailable,
        totalAlreadyRequested,
        totalSkipped,
        totalNotFound,
        totalMovies,
        totalTvShows,
        uniqueNotFoundItems
      }
    }
  }

  const parseTimeToSeconds = (timeStr: string): number => {
    if (!timeStr || typeof timeStr !== 'string') return 0
    
    // Handle various time formats: "1m 30s", "90s", "1.5m", etc.
    const minMatch = timeStr.match(/(\d+\.?\d*)\s*m/)
    const secMatch = timeStr.match(/(\d+\.?\d*)\s*s/)
    
    let totalSeconds = 0
    if (minMatch) totalSeconds += parseFloat(minMatch[1]) * 60
    if (secMatch) totalSeconds += parseFloat(secMatch[1])
    
    return isNaN(totalSeconds) ? 0 : totalSeconds
  }

  const formatTime = (seconds: number): string => {
    if (!seconds || isNaN(seconds)) return '0s'
    
    if (seconds >= 60) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.round(seconds % 60)
      return `${mins}m ${secs}s`
    }
    return `${Math.round(seconds)}s`
  }

  const formatSpeed = (speedMs: number): string => {
    if (!speedMs || isNaN(speedMs)) return '0ms'
    
    if (speedMs >= 1000) {
      const seconds = speedMs / 1000
      return `${seconds.toFixed(1)}s`
    }
    return `${Math.round(speedMs)}ms`
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-white/10 rounded-lg"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-64 bg-white/10 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="glass-card p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2 titillium-web-semibold">Failed to Load Analytics</h2>
          <p className="text-purple-200/70 mb-4 titillium-web-light">{error}</p>
          <button
            onClick={fetchAnalyticsData}
            className="glass-button-primary px-4 py-2 rounded-lg transition-all duration-300 titillium-web-semibold"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <div className="glass-card p-8 text-center">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2 titillium-web-semibold">No Analytics Data</h2>
          <p className="text-purple-200/70 titillium-web-light">No sync runs found in the log file.</p>
        </div>
      </div>
    )
  }

  const { runs, aggregated } = data

  // Get the most recent sync run for status distribution
  const lastSyncRun = runs.length > 0 ? runs[runs.length - 1] : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">Performance Analytics</h1>
        <p className="text-purple-200/70 titillium-web-light">
          Sync operation insights and performance metrics from log analysis
        </p>
      </div>

      {/* Status Distribution - Last Sync Only */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="h-5 w-5 text-purple-400" />
          <span className="text-lg font-semibold text-white titillium-web-semibold">
            Status Distribution - Last Sync
          </span>
          {lastSyncRun && (
            <span className="text-sm text-white/50 ml-2">
              ({new Date(lastSyncRun.timestamp).toLocaleDateString()})
            </span>
          )}
        </div>

        {lastSyncRun ? (
          <div className="space-y-4">
            {/* Requested */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-white/80">Requested</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-64 bg-white/10 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 transition-all duration-1000"
                    style={{ 
                      width: `${lastSyncRun.requested > 0 ? 
                        (lastSyncRun.requested / Math.max(lastSyncRun.requested, lastSyncRun.available, lastSyncRun.alreadyRequested, lastSyncRun.skipped, lastSyncRun.notFound)) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12 text-right">
                  {lastSyncRun.requested}
                </span>
                <span className="text-white/50 w-12 text-right">
                  ({((lastSyncRun.requested / (lastSyncRun.requested + lastSyncRun.available + lastSyncRun.alreadyRequested + lastSyncRun.skipped + lastSyncRun.notFound)) * 100).toFixed(1) || '0.0'}%)
                </span>
              </div>
            </div>

            {/* Available */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
                <span className="text-white/80">Already Available</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-64 bg-white/10 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-purple-400 transition-all duration-1000"
                    style={{ 
                      width: `${lastSyncRun.available > 0 ? 
                        (lastSyncRun.available / Math.max(lastSyncRun.requested, lastSyncRun.available, lastSyncRun.alreadyRequested, lastSyncRun.skipped, lastSyncRun.notFound)) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12 text-right">
                  {lastSyncRun.available}
                </span>
                <span className="text-white/50 w-12 text-right">
                  ({((lastSyncRun.available / (lastSyncRun.requested + lastSyncRun.available + lastSyncRun.alreadyRequested + lastSyncRun.skipped + lastSyncRun.notFound)) * 100).toFixed(1) || '0.0'}%)
                </span>
              </div>
            </div>

            {/* Already Requested */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                <span className="text-white/80">Already Requested</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-64 bg-white/10 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-red-400 transition-all duration-1000"
                    style={{ 
                      width: `${lastSyncRun.alreadyRequested > 0 ? 
                        (lastSyncRun.alreadyRequested / Math.max(lastSyncRun.requested, lastSyncRun.available, lastSyncRun.alreadyRequested, lastSyncRun.skipped, lastSyncRun.notFound)) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12 text-right">
                  {lastSyncRun.alreadyRequested}
                </span>
                <span className="text-white/50 w-12 text-right">
                  ({((lastSyncRun.alreadyRequested / (lastSyncRun.requested + lastSyncRun.available + lastSyncRun.alreadyRequested + lastSyncRun.skipped + lastSyncRun.notFound)) * 100).toFixed(1) || '0.0'}%)
                </span>
              </div>
            </div>

            {/* Skipped */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-purple-300 rounded-full"></div>
                <span className="text-white/80">Skipped</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-64 bg-white/10 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-purple-300 transition-all duration-1000"
                    style={{ 
                      width: `${lastSyncRun.skipped > 0 ? 
                        (lastSyncRun.skipped / Math.max(lastSyncRun.requested, lastSyncRun.available, lastSyncRun.alreadyRequested, lastSyncRun.skipped, lastSyncRun.notFound)) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12 text-right">
                  {lastSyncRun.skipped}
                </span>
                <span className="text-white/50 w-12 text-right">
                  ({((lastSyncRun.skipped / (lastSyncRun.requested + lastSyncRun.available + lastSyncRun.alreadyRequested + lastSyncRun.skipped + lastSyncRun.notFound)) * 100).toFixed(1) || '0.0'}%)
                </span>
              </div>
            </div>

            {/* Not Found */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span className="text-white/80">Not Found</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-64 bg-white/10 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-red-500 transition-all duration-1000"
                    style={{ 
                      width: `${lastSyncRun.notFound > 0 ? 
                        (lastSyncRun.notFound / Math.max(lastSyncRun.requested, lastSyncRun.available, lastSyncRun.alreadyRequested, lastSyncRun.skipped, lastSyncRun.notFound)) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <span className="text-white font-medium w-12 text-right">
                  {lastSyncRun.notFound}
                </span>
                <span className="text-white/50 w-12 text-right">
                  ({((lastSyncRun.notFound / (lastSyncRun.requested + lastSyncRun.available + lastSyncRun.alreadyRequested + lastSyncRun.skipped + lastSyncRun.notFound)) * 100).toFixed(1) || '0.0'}%)
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-white/50 py-8">
            No sync run data available
          </div>
        )}
      </div>

      {/* Media Types */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <PieChart className="h-5 w-5 text-purple-400" />
          <span className="text-lg font-semibold text-white titillium-web-semibold">Media Types</span>
        </div>

        <div className="flex items-center justify-center">
          <div className="relative w-48 h-48">
            {/* Simple circular progress indicator */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-3xl font-bold text-white titillium-web-bold">
                  {aggregated.totalMovies + aggregated.totalTvShows}
                </div>
                <div className="text-sm text-white/60">Total Items</div>
              </div>
            </div>
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="8"
              />
              {/* Movies arc */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#a855f7"
                strokeWidth="8"
                strokeDasharray={`${(aggregated.totalMovies / (aggregated.totalMovies + aggregated.totalTvShows) * 251.2) || 0} 251.2`}
                strokeLinecap="round"
              />
              {/* TV Shows arc */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#8b5cf6"
                strokeWidth="8"
                strokeDasharray={`${(aggregated.totalTvShows / (aggregated.totalMovies + aggregated.totalTvShows) * 251.2) || 0} 251.2`}
                strokeDashoffset={`-${(aggregated.totalMovies / (aggregated.totalMovies + aggregated.totalTvShows) * 251.2) || 0}`}
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-white/80">Movies</span>
            </div>
            <div className="text-xl font-bold text-white">
              {aggregated.totalMovies}
            </div>
            <div className="text-sm text-white/50">
              {((aggregated.totalMovies / (aggregated.totalMovies + aggregated.totalTvShows)) * 100).toFixed(1) || '0.0'}%
            </div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
              <span className="text-white/80">TV Shows</span>
            </div>
            <div className="text-xl font-bold text-white">
              {aggregated.totalTvShows}
            </div>
            <div className="text-sm text-white/50">
              {((aggregated.totalTvShows / (aggregated.totalMovies + aggregated.totalTvShows)) * 100).toFixed(1) || '0.0'}%
            </div>
          </div>
        </div>
      </div>

      {/* Not Found Items */}
      {aggregated.uniqueNotFoundItems.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <span className="text-lg font-semibold text-white titillium-web-semibold">
              Not Found Items ({aggregated.uniqueNotFoundItems.length})
            </span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {aggregated.uniqueNotFoundItems.slice(0, 20).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-red-500/20">
                <span className="text-white/90 truncate">{item.title}</span>
                <span className="text-red-400 font-medium ml-3 flex-shrink-0">
                  {item.count} {item.count === 1 ? 'occurrence' : 'occurrences'}
                </span>
              </div>
            ))}
            {aggregated.uniqueNotFoundItems.length > 20 && (
              <div className="text-center text-white/50 text-sm py-2">
                ... and {aggregated.uniqueNotFoundItems.length - 20} more items
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
} 