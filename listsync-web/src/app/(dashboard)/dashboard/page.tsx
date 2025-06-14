"use client"

import { DashboardOverview } from "@/components/dashboard/overview"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { SystemStatus } from "@/components/dashboard/system-status"
import { QuickActions } from "@/components/dashboard/quick-actions"
import { useLiveTime } from "@/lib/hooks/use-live-time"
import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"
import { formatRelativeTime, formatFutureTime } from "@/lib/utils"
import { CheckCircle, AlertTriangle, Clock, Wifi, Sun, Sunset, Moon } from "lucide-react"
import { useEffect, useState } from "react"
import { Tooltip } from "@/components/ui/tooltip"

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 18) return "Good afternoon"
  return "Good evening"
}

function getTimeBasedEmoji() {
  const hour = new Date().getHours()
  
  // Morning emojis (5am - 12pm)
  const morningEmojis = ["🌅", "☀️", "🌄", "🦅", "🚜"]
  
  // Afternoon emojis (12pm - 6pm)  
  const afternoonEmojis = ["☀️", "🌞", "🏞️", "🚗", "🏋️"]
  
  // Evening emojis (6pm - 5am)
  const eveningEmojis = ["🌙", "⭐", "🌌", "🦉", "🔥"]
  
  let emojiSet
  if (hour >= 5 && hour < 12) {
    emojiSet = morningEmojis
  } else if (hour >= 12 && hour < 18) {
    emojiSet = afternoonEmojis
  } else {
    emojiSet = eveningEmojis
  }
  
  // Random selection from the appropriate emoji set
  const randomIndex = Math.floor(Math.random() * emojiSet.length)
  return emojiSet[randomIndex]
}

function getTimeBasedIcon() {
  const hour = new Date().getHours()
  
  // Morning (5am - 12pm): Sun icon
  if (hour >= 5 && hour < 12) {
    return Sun
  }
  // Afternoon (12pm - 6pm): Sunset icon  
  else if (hour >= 12 && hour < 18) {
    return Sunset
  }
  // Evening (6pm - 5am): Moon icon
  else {
    return Moon
  }
}

export default function DashboardPage() {
  const { formatted, currentTime } = useLiveTime(1000) // Update every second
  const greeting = getGreeting()
  const [sessionEmoji] = useState(() => getTimeBasedEmoji()) // Set once per session
  const [SessionTimeIcon] = useState(() => getTimeBasedIcon()) // Set once per session
  const [liveNextSync, setLiveNextSync] = useState<string>("")

  // Get system health data
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Get Overseerr status
  const { data: overseerrStatus } = useQuery({
    queryKey: ["overseerr-status"],
    queryFn: () => apiClient.getOverseerrStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Get processed data to check log file status
  const { data: processedData } = useQuery({
    queryKey: ["processed-status"],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/processed?page=1&limit=1`)
      if (!response.ok) throw new Error("Failed to fetch")
      return response.json()
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Get sync interval data
  const { data: syncInterval } = useQuery({
    queryKey: ["sync-interval"],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/sync-interval`)
      if (!response.ok) throw new Error("Failed to fetch")
      return response.json()
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Calculate live next sync time
  useEffect(() => {
    console.log('Health data:', health)
    console.log('Next sync from health:', health?.next_sync)
    console.log('Sync interval data:', syncInterval)
    
    if (health?.next_sync) {
      const formattedTime = formatFutureTime(health.next_sync)
      console.log('Formatted next sync time:', formattedTime)
      setLiveNextSync(formattedTime)
    } else if (health?.last_sync && syncInterval?.interval_hours) {
      // Fallback: calculate next sync manually
      console.log('Calculating next sync manually...')
      console.log('Last sync:', health.last_sync)
      console.log('Interval hours:', syncInterval.interval_hours)
      
      try {
        const lastSyncDate = new Date(health.last_sync)
        const nextSyncDate = new Date(lastSyncDate.getTime() + (syncInterval.interval_hours * 60 * 60 * 1000))
        const formattedTime = formatFutureTime(nextSyncDate)
        console.log('Manually calculated next sync:', nextSyncDate.toISOString())
        console.log('Formatted manual next sync time:', formattedTime)
        setLiveNextSync(formattedTime)
      } catch (error) {
        console.error('Error calculating next sync manually:', error)
        setLiveNextSync("")
      }
    } else {
      console.log('No next_sync data available and cannot calculate manually')
      console.log('Missing data - last_sync:', health?.last_sync, 'interval_hours:', syncInterval?.interval_hours)
      setLiveNextSync("")
    }
  }, [currentTime, health?.next_sync, health?.last_sync, syncInterval?.interval_hours])

  // Calculate system status
  const systemServices = [
    { name: "Overseerr", healthy: overseerrStatus?.isConnected || false },
    { name: "Database", healthy: health?.database || false },
  ]
  
  const healthyServices = systemServices.filter(s => s.healthy).length
  const totalServices = systemServices.length
  const allSystemsOperational = healthyServices === totalServices

  return (
    <div className="space-y-6 max-w-full">
      {/* Ultra-Compact Welcome Bar */}
      <div className="glass-card px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Friendly Greeting */}
          <div className="flex items-center gap-3">
            <span className="text-2xl">{sessionEmoji}</span>
            <div>
              <h1 className="text-lg font-semibold text-white titillium-web-semibold">
                {greeting}!
              </h1>
              <p className="text-xs text-white/60 titillium-web-light">
                Welcome back to ListSync
              </p>
            </div>
          </div>

          {/* Center: Quick Status Indicators */}
          <div className="hidden md:flex items-center gap-6 relative">
            {/* System Health */}
            <Tooltip
              content={
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${health?.database ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>SQL Database: {health?.database ? 'Connected' : 'Disconnected'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${overseerrStatus?.isConnected ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>Overseerr API: {overseerrStatus?.isConnected ? 'Connected' : 'Disconnected'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${processedData?.log_file_exists ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>Log Files: {processedData?.log_file_exists ? 'Accessible' : 'Not Found'}</span>
                  </div>
                </div>
              }
              side="bottom"
              align="center"
            >
              <div className="flex items-center gap-2 cursor-help">
                <div className={`w-2 h-2 rounded-full ${allSystemsOperational ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                <span className="text-sm text-white/70 titillium-web-regular">
                  {allSystemsOperational ? 'Systems OK' : 'Issues'}
                </span>
              </div>
            </Tooltip>

            {/* Next Sync */}
            {liveNextSync && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-400"></div>
                <span className="text-sm text-white/70 titillium-web-regular">
                  Next sync {liveNextSync}
                </span>
              </div>
            )}
          </div>

          {/* Right: Live Time */}
          <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg">
            <SessionTimeIcon className="h-3 w-3 text-purple-400" />
            <span className="text-sm font-medium text-white titillium-web-semibold">
              {formatted.time}
            </span>
          </div>
        </div>

        {/* Mobile Status Row */}
        <div className="md:hidden mt-3 pt-3 border-t border-white/10">
          <div className="flex items-center justify-center gap-6 text-xs relative">
            <Tooltip
              content={
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${health?.database ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>SQL Database: {health?.database ? 'Connected' : 'Disconnected'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${overseerrStatus?.isConnected ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>Overseerr API: {overseerrStatus?.isConnected ? 'Connected' : 'Disconnected'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${processedData?.log_file_exists ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                    <span>Log Files: {processedData?.log_file_exists ? 'Accessible' : 'Not Found'}</span>
                  </div>
                </div>
              }
              side="bottom"
              align="center"
            >
              <div className="flex items-center gap-1 cursor-help">
                <div className={`w-1.5 h-1.5 rounded-full ${allSystemsOperational ? 'bg-emerald-400' : 'bg-red-400'}`}></div>
                <span className="text-white/70">{allSystemsOperational ? 'Systems OK' : 'Issues'}</span>
              </div>
            </Tooltip>
            {liveNextSync && (
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                <span className="text-white/70">Next sync {liveNextSync}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid - Statistics Overview */}
      <div className="grid grid-cols-1 2xl:grid-cols-4 gap-6 min-w-0 items-stretch">
        {/* Statistics Overview - Takes 3 columns on 2xl screens, full width on smaller */}
        <div className="2xl:col-span-3 min-w-0">
          <DashboardOverview />
        </div>
        
        {/* Recent Activity - Takes 1 column on 2xl screens, full width on smaller */}
        <div className="2xl:col-span-1 min-w-0">
          <RecentActivity />
        </div>
      </div>

      {/* Section Divider */}
      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-black px-4 text-white/50 titillium-web-semibold tracking-wider">Quick Actions</span>
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions />

      {/* Section Divider */}
      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-black px-4 text-white/50 titillium-web-semibold tracking-wider">System Health</span>
        </div>
      </div>

      {/* System Status */}
      <SystemStatus />
    </div>
  )
} 
