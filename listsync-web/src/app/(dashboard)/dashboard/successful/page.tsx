"use client"

import { useQuery } from "@tanstack/react-query"
import { formatRelativeTime } from "@/lib/utils"
import { CheckCircle, Clock, ArrowLeft, Search, X, Download, SkipForward, ExternalLink } from "lucide-react"
import Link from "next/link"
import { useState, useEffect } from "react"
import { Pagination } from "@/components/ui/pagination"
import { CustomSelect } from "@/components/ui/custom-select"
import { OverseerrLink } from "@/components/ui/overseerr-link"

interface SuccessfulItem {
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

interface SuccessfulData {
  items: SuccessfulItem[]
  total_count: number
  sync_sessions: Array<{
    timestamp: string
    total_items: number
    session_id: string
  }>
  log_file_exists: boolean
  pagination: {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export default function SuccessfulPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState<"all" | "already_available" | "already_requested" | "requested" | "skipped">("all")
  const [selectedMediaType, setSelectedMediaType] = useState<"all" | "movie" | "tv">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  const { data: successful, isLoading, error } = useQuery<SuccessfulData>({
    queryKey: ["successful", currentPage],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/successful?page=${currentPage}&limit=${pageSize}`)
      if (!response.ok) {
        throw new Error("Failed to fetch successful items")
      }
      return response.json()
    },
    refetchInterval: 10000, // Real-time updates every 10 seconds
  })

  // Filter items based on search and filters (client-side filtering on paginated results)
  const filteredItems = successful?.items.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = selectedStatus === "all" || item.status === selectedStatus
    const matchesMediaType = selectedMediaType === "all" || item.media_type === selectedMediaType
    return matchesSearch && matchesStatus && matchesMediaType
  }) || []

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    // Reset filters when changing pages to avoid confusion
    setSearchTerm("")
    setSelectedStatus("all")
    setSelectedMediaType("all")
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
      default:
        return CheckCircle
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "already_available":
        return "text-purple-400"
      case "requested":
        return "text-purple-300"
      case "already_requested":
        return "text-purple-200"
      case "skipped":
        return "text-gray-400"
      default:
        return "text-gray-400"
    }
  }

  const getStatusBorder = (status: string) => {
    switch (status) {
      case "already_available":
        return "border-purple-400"
      case "requested":
        return "border-purple-300"
      case "already_requested":
        return "border-purple-200"
      case "skipped":
        return "border-gray-400"
      default:
        return "border-gray-400"
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case "already_available":
        return "bg-purple-400/20 text-purple-400"
      case "requested":
        return "bg-purple-300/20 text-purple-300"
      case "already_requested":
        return "bg-purple-200/20 text-purple-200"
      case "skipped":
        return "bg-gray-400/20 text-gray-400"
      default:
        return "bg-gray-400/20 text-gray-400"
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
            <CheckCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Error Loading Successful Items</h2>
            <p className="text-white/70">Failed to load successful items data. Please try again.</p>
          </div>
        </div>
      </div>
    )
  }

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
                Successful Items
              </h1>
              <p className="text-white/70 titillium-web-light">
                Historic view of all successfully processed items across all syncs
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <CheckCircle className="h-4 w-4 text-purple-400" />
              <span className="text-white font-medium">
                {successful?.total_count || 0} Total Successful
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <Clock className="h-4 w-4 text-purple-400" />
              <span className="text-white font-medium">
                {successful?.sync_sessions?.length || 0} Sync Sessions
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
              placeholder="Search successful items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-10 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50"
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
            onChange={(value) => setSelectedStatus(value as "all" | "requested" | "already_requested" | "already_available" | "skipped")}
            options={[
              { value: "all", label: "All Statuses" },
              { value: "requested", label: "Requested" },
              { value: "already_requested", label: "Already Requested" },
              { value: "already_available", label: "Already Available" },
              { value: "skipped", label: "Skipped" }
            ]}
            className="min-w-[160px]"
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
        </div>

        {/* Results Summary */}
        <div className="text-sm text-white/60 mb-4">
          Showing {filteredItems.length} of {successful?.pagination?.total_items || 0} successful items
          {searchTerm && ` matching "${searchTerm}"`}
          {successful?.pagination && (
            <span className="ml-2">
              (Page {successful.pagination.page} of {successful.pagination.total_pages})
            </span>
          )}
        </div>
      </div>

      {/* Successful Items */}
      <div className="glass-card p-6">
        {filteredItems.length > 0 ? (
          <div className="space-y-4">
            {filteredItems.map((item, index) => {
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
            <CheckCircle className="h-12 w-12 text-white/30 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {searchTerm ? "No matching items found" : "No successful items found"}
            </h3>
            <p className="text-white/70">
              {searchTerm 
                ? `No successful items match your search for "${searchTerm}"`
                : "No items have been successfully processed yet."
              }
            </p>
          </div>
        )}

        {/* Pagination */}
        {successful?.pagination && successful.pagination.total_pages > 1 && (
          <div className="mt-6 flex justify-center">
            <Pagination
              currentPage={successful.pagination.page}
              totalPages={successful.pagination.total_pages}
              onPageChange={handlePageChange}
            />
          </div>
        )}

        {/* Pagination Info */}
        {successful?.pagination && (
          <div className="mt-4 text-center text-sm text-white/50">
            Page {successful.pagination.page} of {successful.pagination.total_pages}
          </div>
        )}
      </div>
    </div>
  )
} 
