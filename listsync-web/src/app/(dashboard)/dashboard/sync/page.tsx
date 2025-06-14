"use client"

import { useState, useEffect } from 'react'
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Settings,
  Calendar,
  Activity,
  Database
} from 'lucide-react'

interface HealthData {
  database: boolean
  process: boolean
  sync_status: string
  last_sync: string | null
  next_sync: string | null
}

interface SyncInterval {
  interval_hours: number
  source: string
  last_updated: string | null
}

interface SyncProcessStatus {
  processes_found: number
  can_trigger_sync: boolean
  sync_method: string
}

interface LiveSyncStatus {
  is_running: boolean
  status: string
  log_file_found: boolean
  log_file_used?: string
  last_activity?: string | null
  sync_start_count: number
  sync_end_count: number
  error?: string
}

export default function SyncPage() {
  const [healthData, setHealthData] = useState<HealthData | null>(null)
  const [syncProcessStatus, setSyncProcessStatus] = useState<SyncProcessStatus | null>(null)
  const [liveSyncStatus, setLiveSyncStatus] = useState<LiveSyncStatus | null>(null)
  const [syncInterval, setSyncInterval] = useState<SyncInterval | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [triggering, setTriggering] = useState(false)
  const [newInterval, setNewInterval] = useState<number>(24)

  // Fetch live sync status from logs
  const fetchLiveSyncStatus = async () => {
    try {
      const response = await fetch('/api/sync/status/live')
      if (response.ok) {
        const data = await response.json()
        setLiveSyncStatus(data)
        console.log('Live sync status:', data)
      }
    } catch (err) {
      console.error('Error fetching live sync status:', err)
    }
  }

  // Fetch health data (includes last_sync and next_sync)
  const fetchHealthData = async () => {
    try {
      setError(null)
      const response = await fetch('/api/system/health')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setHealthData(data)
    } catch (err) {
      console.error('Error fetching health data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch health data')
    }
  }

  // Fetch sync process status
  const fetchSyncProcessStatus = async () => {
    try {
      const response = await fetch('/api/sync/status')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setSyncProcessStatus(data)
    } catch (err) {
      console.error('Error fetching sync process status:', err)
    }
  }

  // Fetch sync interval
  const fetchSyncInterval = async () => {
    try {
      const response = await fetch('/api/sync-interval')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setSyncInterval(data)
      setNewInterval(data.interval_hours)
    } catch (err) {
      console.error('Error fetching sync interval:', err)
    } finally {
      setLoading(false)
    }
  }

  // Trigger manual sync
  const handleTriggerSync = async () => {
    try {
      setTriggering(true)
      setError(null)
      
      const response = await fetch('/api/sync/trigger', {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // Refresh data after triggering
      await Promise.all([
        fetchHealthData(),
        fetchSyncProcessStatus(),
        fetchLiveSyncStatus()
      ])
      
    } catch (err) {
      console.error('Error triggering sync:', err)
      setError(err instanceof Error ? err.message : 'Failed to trigger sync')
    } finally {
      setTriggering(false)
    }
  }

  // Update sync interval
  const handleUpdateInterval = async () => {
    try {
      setError(null)
      
      const response = await fetch('/api/sync-interval', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interval_hours: newInterval
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      await fetchSyncInterval()
      
    } catch (err) {
      console.error('Error updating sync interval:', err)
      setError(err instanceof Error ? err.message : 'Failed to update sync interval')
    }
  }

  // Format time
  const formatTime = (timeString: string | null) => {
    if (!timeString) return 'Never'
    try {
      return new Date(timeString).toLocaleString()
    } catch {
      return timeString
    }
  }

  // Calculate time until next sync
  const getTimeUntilNextSync = () => {
    if (!healthData?.next_sync) return null
    
    try {
      const nextSync = new Date(healthData.next_sync)
      const now = new Date()
      const diff = nextSync.getTime() - now.getTime()
      
      if (diff <= 0) return 'Overdue'
      
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      } else {
        return `${minutes}m`
      }
    } catch {
      return null
    }
  }

  // Initial load and polling
  useEffect(() => {
    Promise.all([
      fetchHealthData(),
      fetchSyncProcessStatus(),
      fetchSyncInterval(),
      fetchLiveSyncStatus()
    ])

    // Poll status every 10 seconds for more responsive updates
    const interval = setInterval(() => {
      Promise.all([
        fetchHealthData(),
        fetchLiveSyncStatus()
      ])
    }, 10000)
    
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
          <div className="h-32 bg-white/10 rounded-lg"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-white/10 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const canTriggerSync = syncProcessStatus?.can_trigger_sync && !liveSyncStatus?.is_running
  const isRunning = liveSyncStatus?.is_running || false

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">
            Sync Management
          </h1>
          <p className="text-purple-200/70 titillium-web-light">
            Control and monitor your media synchronization
          </p>
          {liveSyncStatus?.log_file_used && (
            <p className="text-purple-200/40 titillium-web-light text-xs mt-1">
              Monitoring: {liveSyncStatus.log_file_used}
            </p>
          )}
        </div>
        
        <button
          onClick={() => {
            fetchHealthData()
            fetchLiveSyncStatus()
          }}
          className="glass-button px-4 py-2 rounded-lg transition-all duration-200"
        >
          <RefreshCw className="h-4 w-4 text-purple-400" />
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-card p-4 border-red-500/30 bg-red-500/10">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-red-300 titillium-web-regular">{error}</p>
          </div>
        </div>
      )}

      {/* Debug Info */}
      {liveSyncStatus && !liveSyncStatus.log_file_found && (
        <div className="glass-card p-4 border-yellow-400/30 bg-yellow-400/10">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            <div>
              <p className="text-yellow-300 titillium-web-regular">Log file not accessible</p>
              <p className="text-yellow-300/60 text-sm titillium-web-light">
                {liveSyncStatus.error || 'Unable to read sync logs for real-time status'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Prominent Start Sync Button */}
      <div className="glass-card p-8 text-center">
        <div className="max-w-md mx-auto space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white titillium-web-bold">
              {isRunning ? 'Sync In Progress' : 'Ready to Sync'}
            </h2>
            <p className="text-purple-200/70 titillium-web-light">
              {isRunning 
                ? 'A sync operation is currently running. Please wait for it to complete.'
                : canTriggerSync 
                  ? 'Start a manual sync to fetch and process your media lists now.'
                  : 'Sync service is not available. Please check the system status.'
              }
            </p>
            {liveSyncStatus?.last_activity && (
              <p className="text-purple-200/40 titillium-web-light text-xs">
                Latest: {liveSyncStatus.last_activity}
              </p>
            )}
          </div>
          
          <button
            onClick={handleTriggerSync}
            disabled={triggering || isRunning || !canTriggerSync}
            className="glass-button-primary w-full px-8 py-4 text-lg font-medium titillium-web-semibold transition-all duration-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <Activity className="h-6 w-6 animate-pulse" />
                Sync Running...
              </>
            ) : triggering ? (
              <>
                <RefreshCw className="h-6 w-6 animate-spin" />
                Starting Sync...
              </>
            ) : (
              <>
                <Play className="h-6 w-6" />
                Start Manual Sync
              </>
            )}
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current Status */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white titillium-web-semibold">Current Status</h3>
            {isRunning ? (
              <Activity className="h-6 w-6 text-green-400 animate-pulse" />
            ) : (
              <Pause className="h-6 w-6 text-gray-400" />
            )}
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {isRunning ? (
                <CheckCircle className="h-4 w-4 text-green-400" />
              ) : (
                <Clock className="h-4 w-4 text-gray-400" />
              )}
              <span className="text-white/80">
                {isRunning ? 'Running' : 'Idle'}
              </span>
            </div>
            
            <div className="text-sm text-white/60">
              Service: {healthData?.process ? 'Online' : 'Offline'}
            </div>
            
            {liveSyncStatus && (
              <div className="text-sm text-white/40">
                Detected: {liveSyncStatus.sync_start_count} starts, {liveSyncStatus.sync_end_count} ends
              </div>
            )}
          </div>
        </div>

        {/* Last Sync */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white titillium-web-semibold">Last Sync</h3>
            <Database className="h-6 w-6 text-blue-400" />
          </div>
          
          <div className="space-y-2">
            <div className="text-white/80">
              {formatTime(healthData?.last_sync || null)}
            </div>
            <div className="text-sm text-white/60">
              Status: {healthData?.sync_status || 'Unknown'}
            </div>
          </div>
        </div>

        {/* Next Sync */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white titillium-web-semibold">Next Sync</h3>
            <Calendar className="h-6 w-6 text-purple-400" />
          </div>
          
          <div className="space-y-2">
            <div className="text-white/80">
              {formatTime(healthData?.next_sync || null)}
            </div>
            {getTimeUntilNextSync() && (
              <div className="text-sm text-white/60">
                In {getTimeUntilNextSync()}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sync Interval Configuration */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="h-6 w-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white titillium-web-semibold">Sync Interval</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-white/80 text-sm font-medium mb-2">
              Current Interval
            </label>
            <div className="space-y-2">
              <div className="text-white">
                {syncInterval?.interval_hours} hours
              </div>
              <div className="text-sm text-white/60">
                Source: {syncInterval?.source || 'Unknown'}
              </div>
              {syncInterval?.last_updated && (
                <div className="text-sm text-white/60">
                  Last updated: {formatTime(syncInterval.last_updated)}
                </div>
              )}
            </div>
          </div>
          
          <div>
            <label className="block text-white/80 text-sm font-medium mb-2">
              Update Interval
            </label>
            <div className="flex gap-3">
              <input
                type="number"
                min="1"
                max="168"
                value={newInterval}
                onChange={(e) => setNewInterval(Number(e.target.value))}
                className="flex-1 px-4 py-2 glass-card rounded-lg text-white bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
              />
              <button
                onClick={handleUpdateInterval}
                disabled={newInterval === syncInterval?.interval_hours}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                Update
              </button>
            </div>
            <div className="text-sm text-white/60 mt-1">
              Hours between automatic syncs (1-168)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 