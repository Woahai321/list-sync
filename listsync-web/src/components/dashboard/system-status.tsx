"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"
import { CheckCircle, XCircle, Database, Server, Clock, Wifi, AlertTriangle } from "lucide-react"
import { formatRelativeTime, formatFutureTime } from "@/lib/utils"
import { useLiveTime } from "@/lib/hooks/use-live-time"
import { useEffect, useState } from "react"

export function SystemStatus() {
  const { currentTime } = useLiveTime(1000) // Update every second
  const [liveNextSync, setLiveNextSync] = useState<string>("")

  // Get system health data
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Get Overseerr status
  const { data: overseerrStatus, isLoading: overseerrLoading } = useQuery({
    queryKey: ["overseerr-status"],
    queryFn: () => apiClient.getOverseerrStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Calculate live next sync time
  useEffect(() => {
    if (health?.next_sync) {
      setLiveNextSync(formatFutureTime(health.next_sync))
    }
  }, [currentTime, health?.next_sync])

  const isLoading = healthLoading || overseerrLoading

  if (isLoading) {
    return (
      <div className="glass-card p-8">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="bg-white/5 h-24 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const statusItems = [
    {
      title: "Overseerr Connection",
      status: overseerrStatus?.isConnected ? "healthy" : "error",
      description: overseerrStatus?.isConnected ? "Connected" : "Connection failed",
      icon: Server,
      details: overseerrStatus?.isConnected 
        ? `v${overseerrStatus.version || 'Unknown'}${overseerrStatus.updateAvailable ? ' (Update Available)' : ''}` 
        : overseerrStatus?.error || "Check configuration",
      lastChecked: overseerrStatus?.lastChecked,
    },
    {
      title: "Database",
      status: health?.database ? "healthy" : "error", 
      description: health?.database ? "Connected" : "Connection failed",
      icon: Database,
      details: health?.database ? "SQLite operational" : "Database unavailable",
    },
  ]

  const overallHealth = statusItems.every(item => item.status === "healthy")

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-white mb-1 titillium-web-semibold">
            System Health
          </h3>
          <p className="text-sm titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Monitor your ListSync infrastructure
          </p>
        </div>
        
        {/* Overall Status Indicator */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
          overallHealth 
            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
            : 'bg-red-500/20 text-red-400 border border-red-500/30'
        }`}>
          {overallHealth ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertTriangle className="h-4 w-4" />
          )}
          <span className="font-medium titillium-web-semibold">
            {overallHealth ? 'All Systems Operational' : 'Issues Detected'}
          </span>
        </div>
      </div>

      {/* Status Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {statusItems.map((item) => {
          const Icon = item.icon
          const isHealthy = item.status === "healthy"
          
          return (
            <div key={item.title} className={`glass-card p-4 border-l-4 ${
              isHealthy ? 'border-emerald-400' : 'border-red-400'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    isHealthy ? 'bg-emerald-500/20' : 'bg-red-500/20'
                  }`}>
                    <Icon className={`h-5 w-5 ${
                      isHealthy ? 'text-emerald-400' : 'text-red-400'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-white titillium-web-semibold">
                      {item.title}
                    </h4>
                    <p className={`text-sm ${
                      isHealthy ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {item.description}
                    </p>
                  </div>
                </div>
                
                <div className={`w-3 h-3 rounded-full ${
                  isHealthy ? 'bg-emerald-400' : 'bg-red-400'
                }`} />
              </div>
              
              <div className="text-xs text-white/60 titillium-web-light">
                {item.details}
              </div>
              
              {item.lastChecked && (
                <div className="text-xs text-white/50 mt-2 titillium-web-light">
                  Last checked: {formatRelativeTime(item.lastChecked)}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Sync Status */}
      {health?.last_sync && (
        <div className="mt-6 pt-4 border-t border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-purple-400" />
              <span className="text-sm text-white/70 titillium-web-regular">
                Last sync: {formatRelativeTime(health.last_sync)}
              </span>
            </div>
            {liveNextSync && (
              <div className="text-sm text-purple-400 titillium-web-regular">
                Next sync: {liveNextSync}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
