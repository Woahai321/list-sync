"use client"

import { useQuery } from "@tanstack/react-query"
import { formatRelativeTime } from "@/lib/utils"
import { Download, Clock, ArrowLeft, Search, X, ExternalLink } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { Pagination } from "@/components/ui/pagination"
import { CustomSelect } from "@/components/ui/custom-select"
import { OverseerrLink } from "@/components/ui/overseerr-link"

interface RequestedItem {
  id: number
  title: string
  media_type: string
  imdb_id?: string
  overseerr_id?: number
  status: string
  timestamp: string
  action: string
}

interface RequestedData {
  items: RequestedItem[]
  total_count: number
  database_exists: boolean
  pagination: {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export default function RequestedPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState<"all" | "requested" | "already_requested">("all")
  const [selectedMediaType, setSelectedMediaType] = useState<"all" | "movie" | "tv">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  const { data: requested, isLoading, error } = useQuery<RequestedData>({
    queryKey: ["requested", currentPage],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/requested?page=${currentPage}&limit=${pageSize}`)
      if (!response.ok) {
        throw new Error("Failed to fetch requested items")
      }
      return response.json()
    },
    refetchInterval: 10000, // Real-time updates every 10 seconds
  })

  // Filter items based on search and filters (client-side filtering on paginated results)
  const filteredItems = requested?.items.filter(item => {
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "requested":
        return "text-purple-300"
      case "already_requested":
        return "text-purple-200"
      default:
        return "text-gray-400"
    }
  }

  const getStatusBorder = (status: string) => {
    switch (status) {
      case "requested":
        return "border-purple-300"
      case "already_requested":
        return "border-purple-200"
      default:
        return "border-gray-400"
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case "requested":
        return "bg-purple-300/20 text-purple-300"
      case "already_requested":
        return "bg-purple-200/20 text-purple-200"
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
            <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Error Loading Requested Items</h2>
            <p className="text-white/70">Failed to load requested items data. Please try again.</p>
          </div>
        </div>
      </div>
    )
  }

  if (!requested?.database_exists) {
    return (
      <div className="space-y-6 max-w-full">
        <div className="glass-card p-8">
          <div className="text-center">
            <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Database Not Found</h2>
            <p className="text-white/70">The database file could not be found. Please ensure ListSync has been run at least once.</p>
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
                Requested Items
              </h1>
              <p className="text-white/70 titillium-web-light">
                Historic view of all items requested to Overseerr
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <Download className="h-4 w-4 text-purple-400" />
              <span className="text-white font-medium">
                {requested?.total_count || 0} Total Requested
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
              placeholder="Search requested items..."
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
            onChange={(value) => setSelectedStatus(value as "all" | "requested" | "already_requested")}
            options={[
              { value: "all", label: `All (${requested?.items.length || 0})` },
              { value: "requested", label: `Newly Requested (${requested?.items.filter(i => i.status === "requested").length || 0})` },
              { value: "already_requested", label: `Already Requested (${requested?.items.filter(i => i.status === "already_requested").length || 0})` }
            ]}
            className="min-w-[180px]"
          />

          {/* Media Type Filter */}
          <CustomSelect
            value={selectedMediaType}
            onChange={(value) => setSelectedMediaType(value as "all" | "movie" | "tv")}
            options={[
              { value: "all", label: "All Media" },
              { value: "movie", label: "Movies" },
              { value: "tv", label: "TV Shows" }
            ]}
            className="min-w-[120px]"
          />
        </div>

        {/* Results Summary */}
        <div className="text-sm text-white/60 mb-4">
          Showing {filteredItems.length} of {requested?.pagination?.total_items || 0} requested items
          {searchTerm && ` matching "${searchTerm}"`}
          {requested?.pagination && (
            <span className="ml-2">
              (Page {requested.pagination.page} of {requested.pagination.total_pages})
            </span>
          )}
        </div>
      </div>

      {/* Requested Items */}
      <div className="glass-card p-6">
        {filteredItems.length > 0 ? (
          <div className="space-y-4">
            {filteredItems.map((item, index) => (
              <div
                key={`${item.id}-${index}`}
                className={`p-4 rounded-lg border bg-white/5 hover:bg-white/10 transition-colors ${getStatusBorder(item.status)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className={`p-2 rounded-lg border ${getStatusBorder(item.status)} bg-white/5`}>
                      <Download className={`h-5 w-5 ${getStatusColor(item.status)}`} />
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
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm text-white/70">
                      {formatRelativeTime(item.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Download className="h-12 w-12 text-white/30 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {searchTerm ? "No matching items found" : "No requested items found"}
            </h3>
            <p className="text-white/70">
              {searchTerm 
                ? `No requested items match your search for "${searchTerm}"`
                : "No items have been requested to Overseerr yet."
              }
            </p>
          </div>
        )}

        {/* Pagination */}
        {requested?.pagination && requested.pagination.total_pages > 1 && (
          <div className="mt-6 flex justify-center">
            <Pagination
              currentPage={requested.pagination.page}
              totalPages={requested.pagination.total_pages}
              onPageChange={handlePageChange}
            />
          </div>
        )}

        {/* Pagination Info */}
        {requested?.pagination && (
          <div className="mt-4 text-center text-sm text-white/50">
            Page {requested.pagination.page} of {requested.pagination.total_pages}
          </div>
        )}
      </div>
    </div>
  )
} 
