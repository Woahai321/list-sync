"use client"

import { useQuery } from "@tanstack/react-query"
import { formatRelativeTime } from "@/lib/utils"
import { BarChart3, Clock, ArrowLeft, Search, X, CheckCircle, AlertTriangle, Download, SkipForward, ExternalLink } from "lucide-react"
import Link from "next/link"
import { useState, useEffect } from "react"
import { Pagination } from "@/components/ui/pagination"
import { CustomSelect } from "@/components/ui/custom-select"
import { OverseerrLink } from "@/components/ui/overseerr-link"

interface ProcessedItem {
  id: string
  title: string
  media_type: string
  status: string
  category: string
  timestamp: string
  item_number?: number
  total_items?: number
  sync_session?: string
  action: string
  imdb_id?: string | null
  overseerr_id?: number | null
  db_status?: string | null
}

interface ProcessedData {
  items: ProcessedItem[]
  total_count: number
  filtered_count: number
  sync_sessions: Array<{
    timestamp: string
    total_items: number
    session_id: string
  }>
  log_file_exists: boolean
  filters: {
    search: string
    status_filter: string
    media_type_filter: string
  }
  pagination: {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export default function ProcessedPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState<"all" | "successful" | "failed">("all")
  const [selectedMediaType, setSelectedMediaType] = useState<"all" | "movie" | "tv">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const pageSize = 50

  // Debounce search term to avoid too many API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
      setCurrentPage(1) // Reset to first page when searching
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedStatus, selectedMediaType])

  const { data: processed, isLoading, error } = useQuery<ProcessedData>({
    queryKey: ["processed", currentPage, debouncedSearch, selectedStatus, selectedMediaType],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: pageSize.toString(),
      })
      
      if (debouncedSearch.trim()) {
        params.append('search', debouncedSearch.trim())
      }
      
      if (selectedStatus !== 'all') {
        params.append('status_filter', selectedStatus)
      }
      
      if (selectedMediaType !== 'all') {
        params.append('media_type_filter', selectedMediaType)
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/processed?${params}`)
      if (!response.ok) {
        throw new Error("Failed to fetch processed items")
      }
      return response.json()
    },
    refetchInterval: 10000, // Real-time updates every 10 seconds
  })

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const clearFilters = () => {
    setSearchTerm("")
    setSelectedStatus("all")
    setSelectedMediaType("all")
    setCurrentPage(1)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "already_available":
      case "requested":
        return CheckCircle
      case "already_requested":
        return Download
      case "skipped":
        return SkipForward
      case "not_found":
      case "error":
        return AlertTriangle
      default:
        return CheckCircle
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "already_available":
      case "requested":
        return "text-purple-400"
      case "already_requested":
        return "text-purple-300"
      case "skipped":
        return "text-gray-400"
      case "not_found":
      case "error":
        return "text-red-400"
      default:
        return "text-gray-400"
    }
  }

  const getStatusBorder = (status: string) => {
    switch (status) {
      case "already_available":
      case "requested":
        return "border-purple-400"
      case "already_requested":
        return "border-purple-300"
      case "skipped":
        return "border-gray-400"
      case "not_found":
      case "error":
        return "border-red-400"
      default:
        return "border-gray-400"
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-full">
        <div className="glass-card p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-white/10 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-white/10 rounded w-1/2 mb-8"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-24 bg-white/5 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 max-w-full">
        <div className="glass-card p-8">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Error Loading Processed Items</h2>
            <p className="text-white/70">Failed to load processed items data. Please try again.</p>
          </div>
        </div>
      </div>
    )
  }

  const hasActiveFilters = searchTerm || selectedStatus !== "all" || selectedMediaType !== "all"

  return (
    <div className="space-y-6 max-w-full">
      {/* Header */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Link 
              href="/dashboard" 
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-white" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white titillium-web-bold">
                Processed Items
              </h1>
              <p className="text-white/70 titillium-web-light">
                Historic view of all items processed across all syncs
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <BarChart3 className="h-4 w-4 text-purple-400" />
              <span className="text-white font-medium">
                {processed?.total_count || 0} Total Processed
              </span>
            </div>
            {hasActiveFilters && (
              <div className="flex items-center gap-2 px-3 py-2 glass-card">
                <Search className="h-4 w-4 text-purple-400" />
                <span className="text-white font-medium">
                  {processed?.filtered_count || 0} Filtered Results
                </span>
              </div>
            )}
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <Clock className="h-4 w-4 text-purple-400" />
              <span className="text-white font-medium">
                {processed?.sync_sessions?.length || 0} Sync Sessions
              </span>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col lg:flex-row gap-4 mb-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/50" />
            <input
              type="text"
              placeholder="Search across all processed items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-10 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Status Filter */}
          <CustomSelect
            value={selectedStatus}
            onChange={(value) => setSelectedStatus(value as "all" | "successful" | "failed")}
            options={[
              { value: "all", label: "All Statuses" },
              { value: "successful", label: "Successful" },
              { value: "failed", label: "Failed" }
            ]}
            className="min-w-[140px]"
          />

          {/* Media Type Filter */}
          <CustomSelect
            value={selectedMediaType}
            onChange={(value) => setSelectedMediaType(value as "all" | "movie" | "tv")}
            options={[
              { value: "all", label: "All Types" },
              { value: "movie", label: "Movies" },
              { value: "tv", label: "TV Shows" }
            ]}
            className="min-w-[120px]"
          />

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-red-500/20 border border-red-400/30 rounded-lg text-red-300 hover:bg-red-500/30 transition-colors flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Clear Filters
            </button>
          )}
        </div>

        {/* Results Info */}
        {hasActiveFilters && (
          <div className="mb-4 p-3 bg-purple-500/20 border border-purple-400/30 rounded-lg">
            <p className="text-purple-200 text-sm">
              Showing {processed?.filtered_count || 0} results 
              {searchTerm && ` matching "${searchTerm}"`}
              {selectedStatus !== "all" && ` with status "${selectedStatus}"`}
              {selectedMediaType !== "all" && ` of type "${selectedMediaType}"`}
              {" "}out of {processed?.total_count || 0} total processed items
            </p>
          </div>
        )}
      </div>

      {/* Items List */}
      <div className="glass-card p-6">
        {processed?.items && processed.items.length > 0 ? (
          <div className="space-y-4">
            {processed.items.map((item, index) => {
              const StatusIcon = getStatusIcon(item.status)
              return (
                <div
                  key={`${item.id}-${index}`}
                  className={`p-4 rounded-lg border bg-white/5 hover:bg-white/10 transition-colors ${getStatusBorder(item.status)}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className={`p-2 rounded-lg border ${getStatusBorder(item.status)} bg-white/5`}>
                        <StatusIcon className={`h-5 w-5 ${getStatusColor(item.status)}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-white truncate titillium-web-semibold">
                          {item.title}
                        </h3>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-sm text-white/70 capitalize">
                            {item.media_type}
                          </span>
                          <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
                            {item.action}
                          </span>
                          {item.imdb_id && (
                            <a
                              href={`https://www.imdb.com/title/${item.imdb_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1"
                            >
                              <ExternalLink className="h-3 w-3" />
                              IMDb
                            </a>
                          )}
                          <OverseerrLink
                            overseerrId={item.overseerr_id}
                            mediaType={item.media_type}
                            title={item.title}
                          />
                          {item.sync_session && (
                            <span className="text-xs text-white/50">
                              Session: {item.sync_session}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm text-white/70">
                        {formatRelativeTime(item.timestamp)}
                      </div>
                      {item.item_number && item.total_items && (
                        <div className="text-xs text-white/50 mt-1">
                          Item {item.item_number} of {item.total_items}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-white/30 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {hasActiveFilters ? "No matching items found" : "No processed items found"}
            </h3>
            <p className="text-white/70">
              {hasActiveFilters 
                ? "Try adjusting your search or filter criteria."
                : "Items will appear here after sync operations complete."
              }
            </p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 px-4 py-2 bg-purple-500/20 border border-purple-400/30 rounded-lg text-purple-300 hover:bg-purple-500/30 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Pagination */}
        {processed?.pagination && processed.pagination.total_pages > 1 && (
          <div className="mt-6 flex justify-center">
            <Pagination
              currentPage={processed.pagination.page}
              totalPages={processed.pagination.total_pages}
              onPageChange={handlePageChange}
            />
          </div>
        )}

        {/* Pagination Info */}
        {processed?.pagination && (
          <div className="mt-4 text-center text-sm text-white/50">
            Page {processed.pagination.page} of {processed.pagination.total_pages}
            {hasActiveFilters && (
              <span> • {processed.filtered_count} filtered results</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 
