"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"
import { formatRelativeTime } from "@/lib/utils"
import { BarChart3, CheckCircle, Download, AlertTriangle, TrendingUp, Activity } from "lucide-react"
import { AnimatedCounter } from "@/components/ui/animated-counter"
import Link from "next/link"

export function DashboardOverview() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: () => apiClient.getStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch duplicate data
  const { data: dataQuality } = useQuery({
    queryKey: ["data-quality"],
    queryFn: async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/stats/data-quality`)
        if (!response.ok) return null
        return response.json()
      } catch {
        return null
      }
    },
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <div className="glass-card p-8 w-full">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white/5 h-48 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const totalProcessed = stats?.total_processed || 0
  const successfulItems = stats?.successful_items || 0
  const totalRequested = stats?.total_requested || 0
  const totalErrors = stats?.total_errors || 0
  const successRate = stats?.success_rate || 0
  const duplicatesFound = stats?.duplicates_in_current_sync || 0

  // Format large numbers
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const statCards = [
    {
      title: "Total Items",
      value: totalProcessed,
      icon: BarChart3,
      color: "#9d34da",
      bgGradient: "from-purple-500/20 to-purple-600/20",
      borderColor: "border-purple-500/30",
      description: "Total processed",
      showDuplicates: true,
      clickable: true,
      href: "/dashboard/processed"
    },
    {
      title: "Successful Items",
      value: successfulItems,
      icon: CheckCircle,
      color: "#a855f7",
      bgGradient: "from-purple-400/20 to-purple-500/20",
      borderColor: "border-purple-400/30",
      description: "Successfully processed",
      clickable: true,
      href: "/dashboard/successful"
    },
    {
      title: "Total Requested",
      value: totalRequested,
      icon: Download,
      color: "#8b5cf6",
      bgGradient: "from-purple-500/20 to-purple-600/20",
      borderColor: "border-purple-500/30",
      description: "Items requested",
      clickable: true,
      href: "/dashboard/requested"
    },
    {
      title: "Errors/Not Found",
      value: totalErrors,
      icon: AlertTriangle,
      color: "rgb(239, 68, 68)",
      bgGradient: "from-red-500/20 to-red-600/20",
      borderColor: "border-red-500/30",
      description: "Items that failed",
      clickable: true,
      href: "/dashboard/failures"
    },
  ]

  return (
    <div className="glass-card p-6 w-full flex flex-col h-full">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div className="min-w-0 flex-1">
          <h3 className="text-2xl font-bold text-white mb-2 titillium-web-bold">
            Sync Statistics
          </h3>
          <p className="text-base titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Overview of your media synchronization performance
          </p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 glass-card flex-shrink-0">
          <TrendingUp className="h-5 w-5" style={{ color: '#9d34da' }} />
          <div className="text-right">
            <div className="text-lg font-bold text-white titillium-web-semibold">
              <AnimatedCounter value={successRate} suffix="%" />
            </div>
            <div className="text-xs titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Success Rate</div>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex flex-col">
        {/* Main Statistics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full mb-8">
          {statCards.map((stat, index) => {
            const isClickable = stat.clickable || false
            const baseClassName = `glass-card-hover p-8 group min-h-[220px] flex flex-col justify-between min-w-0 bg-gradient-to-br ${stat.bgGradient} border ${stat.borderColor} hover:border-opacity-50 transition-all duration-300`
            const clickableClassName = isClickable ? 'cursor-pointer hover:scale-105 hover:shadow-lg' : ''
            const fullClassName = `${baseClassName} ${clickableClassName}`
            
            const cardContent = (
              <>
                {/* Header with icon */}
                <div className="flex items-center justify-between mb-6">
                  <div className={`p-4 rounded-xl bg-gradient-to-br ${stat.bgGradient} border ${stat.borderColor}`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="text-right">
                    <div className="text-xs titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                      {stat.description}
                    </div>
                  </div>
                </div>
                
                {/* Main value */}
                <div className="space-y-3 flex-1 flex flex-col justify-center">
                  <div className="text-4xl font-bold text-white titillium-web-bold">
                    <AnimatedCounter 
                      value={stat.value} 
                      duration={800 + index * 200}
                      formatter={formatNumber}
                    />
                  </div>
                  <div className="text-base font-medium titillium-web-semibold" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                    {stat.title}
                  </div>
                  
                  {/* Show duplicates for Total Items Processed */}
                  {stat.showDuplicates && duplicatesFound > 0 && (
                    <div className="text-sm titillium-web-light text-red-400">
                      -{duplicatesFound} duplicates
                    </div>
                  )}
                  
                  {/* Percentage of total */}
                  {totalProcessed > 0 && stat.title !== "Total Items" && (
                    <div className="text-sm titillium-web-light" style={{ color: 'rgba(157, 52, 218, 0.8)' }}>
                      <AnimatedCounter 
                        value={(stat.value / totalProcessed) * 100} 
                        suffix="% of total" 
                        duration={1000 + index * 200}
                      />
                    </div>
                  )}
                </div>
              </>
            )

            if (isClickable && stat.href) {
              return (
                <Link key={stat.title} href={stat.href}>
                  <div className={fullClassName}>
                    {cardContent}
                  </div>
                </Link>
              )
            }

            return (
              <div key={stat.title} className={fullClassName}>
                {cardContent}
              </div>
            )
          })}
        </div>

        {/* Success Rate Summary Bar */}
        <div className="glass-card p-6 bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/20 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-6 w-6" style={{ color: '#9d34da' }} />
              <span className="text-xl font-semibold text-white titillium-web-semibold">Overall Success Rate</span>
            </div>
            <div className="text-3xl font-bold text-white titillium-web-bold">
              <AnimatedCounter value={successRate} suffix="%" />
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-white/10 rounded-full h-4 overflow-hidden mb-3">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${successRate}%` }}
            />
          </div>
          
          <div className="flex justify-between text-sm mt-3 titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            <span>{formatNumber(successfulItems)} successful</span>
            <span>{formatNumber(totalErrors)} errors</span>
          </div>
        </div>

        {/* Last Sync Info */}
        {stats?.last_updated && (
          <div className="mt-auto pt-4 border-t border-white/10">
            <div className="flex items-center gap-3 text-sm titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              <Activity className="h-4 w-4" style={{ color: '#9d34da' }} />
              <span>Last updated: {formatRelativeTime(stats.last_updated)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 
