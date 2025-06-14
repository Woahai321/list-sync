"use client"

import { useQuery } from "@tanstack/react-query"
import { formatRelativeTime, truncateText } from "@/lib/utils"
import { CheckCircle, XCircle, Clock, ExternalLink, SkipForward, ChevronLeft, ChevronRight, Activity } from "lucide-react"
import { useEffect, useState } from "react"

interface RecentActivityItem {
  title: string
  status: "available" | "not_found" | "requested" | "skipped"
  status_text: string
  timestamp: string
  position: number
  total: number
}

interface RecentActivityResponse {
  items: RecentActivityItem[]
  total_items: number
  page: number
  limit: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
  log_file_used?: string
  error?: string
}

export function RecentActivity() {
  const [mounted, setMounted] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    setMounted(true)
  }, [])

  const { data: activityData, isLoading, error } = useQuery({
    queryKey: ["recent-activity", currentPage],
    queryFn: async (): Promise<RecentActivityResponse> => {
      const response = await fetch(`/api/recent-activity?page=${currentPage}&limit=6&media_only=true`)
      if (!response.ok) {
        throw new Error("Failed to fetch recent activity")
      }
      return response.json()
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: mounted, // Only run query after component is mounted
  })

  if (!mounted) {
    return (
      <div className="glass-card p-6 w-full h-full">
        <div className="animate-pulse h-full flex flex-col">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-6"></div>
          <div className="space-y-3 flex-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white/5 h-16 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="glass-card p-6 w-full h-full">
        <div className="animate-pulse h-full flex flex-col">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-6"></div>
          <div className="space-y-3 flex-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white/5 h-16 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const items = activityData?.items || []
  const hasError = activityData?.error || error?.message
  const totalPages = activityData?.total_pages || 0
  const totalItems = activityData?.total_items || 0

  const handlePrevPage = () => {
    if (activityData?.has_prev) {
      setCurrentPage(prev => prev - 1)
    }
  }

  const handleNextPage = () => {
    if (activityData?.has_next) {
      setCurrentPage(prev => prev + 1)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "available":
        return (
          <div className="p-2 bg-purple-600/20 border border-purple-500/30 rounded-lg">
            <CheckCircle className="h-4 w-4 text-purple-300" />
          </div>
        )
      case "not_found":
        return (
          <div className="p-2 bg-red-600/20 border border-red-500/30 rounded-lg">
            <XCircle className="h-4 w-4 text-red-300" />
          </div>
        )
      case "requested":
        return (
          <div className="p-2 bg-purple-600/20 border border-purple-500/30 rounded-lg">
            <CheckCircle className="h-4 w-4 text-purple-300" />
          </div>
        )
      case "skipped":
        return (
          <div className="p-2 bg-gray-600/20 border border-gray-500/30 rounded-lg">
            <SkipForward className="h-4 w-4 text-gray-300" />
          </div>
        )
      default:
        return (
          <div className="p-2 bg-gray-600/20 border border-gray-500/30 rounded-lg">
            <Clock className="h-4 w-4 text-gray-300" />
          </div>
        )
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "available":
        return "bg-purple-500/20 text-purple-300 border border-purple-500/30"
      case "not_found":
        return "bg-red-500/20 text-red-300 border border-red-500/30"
      case "requested":
        return "bg-purple-500/20 text-purple-300 border border-purple-500/30"
      case "skipped":
        return "bg-gray-500/20 text-gray-300 border border-gray-500/30"
      default:
        return "bg-gray-500/20 text-gray-300 border border-gray-500/30"
    }
  }

  const formatTime = (timestamp: string) => {
    if (!timestamp) return "Unknown time"
    
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
      
      if (diffInMinutes < 1) return "Just now"
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`
      
      const diffInHours = Math.floor(diffInMinutes / 60)
      if (diffInHours < 24) return `${diffInHours}h ago`
      
      const diffInDays = Math.floor(diffInHours / 24)
      return `${diffInDays}d ago`
    } catch {
      return "Unknown time"
    }
  }

  return (
    <div className="glass-card p-6 w-full flex flex-col h-full">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div className="min-w-0 flex-1">
          <h3 className="text-2xl font-bold text-white mb-2 titillium-web-bold">
            Recent Activity
          </h3>
          <p className="text-base titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Latest items
          </p>
        </div>
        {totalItems > 0 && (
          <div className="flex items-center gap-3 px-4 py-2 glass-card flex-shrink-0">
            <Activity className="h-5 w-5" style={{ color: '#9d34da' }} />
            <div className="text-right">
              <div className="text-lg font-bold text-white titillium-web-semibold">
                {totalItems}
              </div>
              <div className="text-xs titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>recent items</div>
            </div>
          </div>
        )}
      </div>

      {hasError ? (
        <div className="text-center py-8 text-red-300/70 flex-1 flex flex-col justify-center min-h-0">
          <div className="text-sm titillium-web-regular">Error loading activity</div>
          <div className="text-xs titillium-web-light mt-1">{hasError}</div>
          {activityData?.log_file_used && (
            <div className="text-xs titillium-web-light mt-1">
              Attempted to read from: {activityData.log_file_used}
            </div>
          )}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-8 text-purple-200/70 flex-1 flex flex-col justify-center min-h-0">
          <div className="text-sm titillium-web-regular">No recent activity</div>
          <div className="text-xs titillium-web-light mt-1">Items will appear here after syncing</div>
        </div>
      ) : (
        <>
          <div className="space-y-4 flex-1 min-h-0 overflow-y-auto">
            {items.slice(0, 4).map((item, index) => (
              <div key={`${item.title}-${item.position}-${index}`} className="flex items-center gap-3 p-4 bg-white/5 hover:bg-white/10 transition-colors rounded-lg border border-white/10">
                <div className="flex-shrink-0">
                  {getStatusIcon(item.status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-white truncate titillium-web-semibold text-sm">
                      {truncateText(item.title, 25)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium titillium-web-semibold ${getStatusColor(item.status)}`}>
                      {item.status_text}
                    </span>
                    
                    <span className="text-xs text-white/50 titillium-web-light">
                      {formatTime(item.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-6 pt-4 border-t border-white/10 flex-shrink-0">
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePrevPage}
                  disabled={!activityData?.has_prev}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors titillium-web-semibold ${
                    activityData?.has_prev
                      ? 'text-purple-300 hover:text-purple-100 hover:bg-white/10 border border-purple-500/30'
                      : 'text-gray-400 cursor-not-allowed border border-gray-500/30'
                  }`}
                >
                  <ChevronLeft className="h-3 w-3" />
                  Prev
                </button>

                <div className="flex items-center gap-1">
                  <span className="text-xs text-white/60 titillium-web-regular">
                    {currentPage}/{totalPages}
                  </span>
                </div>

                <button
                  onClick={handleNextPage}
                  disabled={!activityData?.has_next}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors titillium-web-semibold ${
                    activityData?.has_next
                      ? 'text-purple-300 hover:text-purple-100 hover:bg-white/10 border border-purple-500/30'
                      : 'text-gray-400 cursor-not-allowed border border-gray-500/30'
                  }`}
                >
                  Next
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
} 
