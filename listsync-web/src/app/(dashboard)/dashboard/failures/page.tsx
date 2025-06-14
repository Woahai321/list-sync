"use client"

import { useQuery } from "@tanstack/react-query"
import { formatRelativeTime } from "@/lib/utils"
import { AlertTriangle, Clock, ArrowLeft, Search, X } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { Pagination } from "@/components/ui/pagination"
import { CustomSelect } from "@/components/ui/custom-select"

interface FailureItem {
  name: string
  timestamp: string | null
  item_number?: number | null
  total_items?: number | null
  sync_session?: string | null
  error_details?: string | null
}

interface FailuresData {
  not_found: FailureItem[]
  errors: FailureItem[]
  total_failures: number
  last_sync_time: string | null
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

export default function FailuresPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedType, setSelectedType] = useState<"all" | "not_found" | "errors">("all")
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  const { data: failures, isLoading, error } = useQuery<FailuresData>({
    queryKey: ["failures", currentPage],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/failures?page=${currentPage}&limit=${pageSize}`)
      if (!response.ok) {
        throw new Error("Failed to fetch failures")
      }
      return response.json()
    },
    refetchInterval: 5000, // Real-time updates every 5 seconds
  })

  // Combine and filter items based on search and type (client-side filtering on paginated results)
  const allFailures = [
    ...(failures?.not_found.map(item => ({ ...item, type: "not_found" as const })) || []),
    ...(failures?.errors.map(item => ({ ...item, type: "error" as const })) || [])
  ]

  const filteredItems = allFailures.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === "all" || 
      (selectedType === "not_found" && item.type === "not_found") ||
      (selectedType === "errors" && item.type === "error")
    return matchesSearch && matchesType
  })

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    // Reset filters when changing pages to avoid confusion
    setSearchTerm("")
    setSelectedType("all")
  }

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-full">
        <div className="glass-card p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-white/10 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-white/10 rounded w-1/2 mb-8"></div>
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
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
            <h2 className="text-xl font-semibold text-white mb-2">Error Loading Failures</h2>
            <p className="text-white/70">Failed to load failure data. Please try again.</p>
          </div>
        </div>
      </div>
    )
  }

  if (!failures?.log_file_exists) {
    return (
      <div className="space-y-6 max-w-full">
        <div className="glass-card p-8">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No Log File Found</h2>
            <p className="text-white/70">The log file could not be found. Please ensure ListSync has been run at least once.</p>
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
                Failures & Errors
              </h1>
              <p className="text-white/70 titillium-web-light">
                Items that failed to process or were not found
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 glass-card">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              <span className="text-white font-medium">
                {failures?.total_failures || 0} Total Failures
              </span>
            </div>
            {failures?.last_sync_time && (
              <div className="flex items-center gap-2 px-3 py-2 glass-card">
                <Clock className="h-4 w-4 text-purple-400" />
                <span className="text-white font-medium">
                  Last sync: {formatRelativeTime(failures.last_sync_time)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col lg:flex-row gap-4 mb-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/50" />
            <input
              type="text"
              placeholder="Search failed items..."
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

          {/* Type Filter */}
          <CustomSelect
            value={selectedType}
            onChange={(value) => setSelectedType(value as "all" | "not_found" | "errors")}
            options={[
              { value: "all", label: `All (${allFailures.length})` },
              { value: "not_found", label: `Not Found (${failures?.not_found.length || 0})` },
              { value: "errors", label: `Errors (${failures?.errors.length || 0})` }
            ]}
            className="min-w-[140px]"
          />
        </div>

        {/* Results Summary */}
        <div className="text-sm text-white/60 mb-4">
          Showing {filteredItems.length} of {failures?.pagination?.total_items || 0} failed items
          {searchTerm && ` matching "${searchTerm}"`}
          {failures?.pagination && (
            <span className="ml-2">
              (Page {failures.pagination.page} of {failures.pagination.total_pages})
            </span>
          )}
        </div>
      </div>

      {/* Failure Items */}
      <div className="glass-card p-6">
        {filteredItems.length > 0 ? (
          <div className="space-y-4">
            {filteredItems.map((item, index) => (
              <div
                key={`${item.name}-${index}`}
                className={`p-4 rounded-lg border bg-white/5 hover:bg-white/10 transition-colors ${
                  item.type === "not_found" ? "border-orange-400" : "border-red-400"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className={`p-2 rounded-lg border bg-white/5 ${
                      item.type === "not_found" ? "border-orange-400" : "border-red-400"
                    }`}>
                      <AlertTriangle className={`h-5 w-5 ${
                        item.type === "not_found" ? "text-orange-400" : "text-red-400"
                      }`} />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white truncate titillium-web-semibold">
                        {item.name}
                      </h3>
                      <div className="flex items-center gap-4 mt-1">
                        <span className={`text-sm font-medium ${
                          item.type === "not_found" ? "text-orange-400" : "text-red-400"
                        }`}>
                          {item.type === "not_found" ? "Not Found" : "Error"}
                        </span>
                        {item.item_number && item.total_items && (
                          <span className="text-xs text-white/50">
                            Item {item.item_number} of {item.total_items}
                          </span>
                        )}
                        {item.sync_session && (
                          <span className="text-xs text-white/50">
                            Session: {item.sync_session}
                          </span>
                        )}
                      </div>
                      {item.error_details && (
                        <div className="text-sm text-red-300 bg-red-500/10 p-2 rounded mt-2">
                          {item.error_details}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    {item.timestamp && (
                      <div className="text-sm text-white/70">
                        {formatRelativeTime(item.timestamp)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <AlertTriangle className="h-12 w-12 text-white/30 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {searchTerm ? "No matching failures found" : "No failures found"}
            </h3>
            <p className="text-white/70">
              {searchTerm 
                ? `No failures match your search for "${searchTerm}"`
                : "Great! No items have failed processing."
              }
            </p>
          </div>
        )}

        {/* Pagination */}
        {failures?.pagination && failures.pagination.total_pages > 1 && (
          <div className="mt-6 flex justify-center">
            <Pagination
              currentPage={failures.pagination.page}
              totalPages={failures.pagination.total_pages}
              onPageChange={handlePageChange}
            />
          </div>
        )}

        {/* Pagination Info */}
        {failures?.pagination && (
          <div className="mt-4 text-center text-sm text-white/50">
            Page {failures.pagination.page} of {failures.pagination.total_pages}
          </div>
        )}
      </div>
    </div>
  )
} 
