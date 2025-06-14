"use client"

import { useState, useEffect } from 'react'
import { 
  Settings, 
  Save, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Shield,
  Bell
} from 'lucide-react'

interface SystemHealth {
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

export default function SettingsPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [syncInterval, setSyncInterval] = useState<SyncInterval | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [newInterval, setNewInterval] = useState<number>(24)

  // Fetch system health
  const fetchHealth = async () => {
    try {
      setError(null)
      const response = await fetch('/api/system/health')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setHealth(data)
    } catch (err) {
      console.error('Error fetching health:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch system health')
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

  // Update sync interval
  const handleUpdateInterval = async () => {
    try {
      setSaving(true)
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
    } finally {
      setSaving(false)
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

  // Initial load
  useEffect(() => {
    Promise.all([
      fetchHealth(),
      fetchSyncInterval()
    ])
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-white/10 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">
            Settings
          </h1>
          <p className="text-purple-200/70 titillium-web-light">
            Configure your ListSync installation
          </p>
        </div>
        
        <button
          onClick={() => Promise.all([fetchHealth(), fetchSyncInterval()])}
          className="glass-button px-4 py-2 rounded-lg transition-all duration-200"
        >
          <RefreshCw className="h-4 w-4 text-purple-400" />
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-card p-4 border-red-400/30 bg-red-400/10">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-red-300 titillium-web-regular">{error}</p>
          </div>
        </div>
      )}

      {/* System Health */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-6 w-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white titillium-web-semibold">System Health</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-purple-400" />
            <div>
              <div className="text-white font-medium titillium-web-semibold">Database</div>
              <div className="flex items-center gap-2">
                {health?.database ? (
                  <CheckCircle className="h-4 w-4 text-purple-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                )}
                <span className="text-white/60 text-sm titillium-web-light">
                  {health?.database ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Settings className="h-5 w-5 text-purple-400" />
            <div>
              <div className="text-white font-medium titillium-web-semibold">Process</div>
              <div className="flex items-center gap-2">
                {health?.process ? (
                  <CheckCircle className="h-4 w-4 text-purple-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                )}
                <span className="text-white/60 text-sm titillium-web-light">
                  {health?.process ? 'Running' : 'Stopped'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-gray-400" />
            <div>
              <div className="text-white font-medium titillium-web-semibold">Sync Status</div>
              <div className="text-white/60 text-sm titillium-web-light">
                {health?.sync_status || 'Unknown'}
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-white/20">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-white/80 text-sm font-medium mb-1 titillium-web-semibold">Last Sync</div>
              <div className="text-white/60 text-sm titillium-web-light">
                {formatTime(health?.last_sync || null)}
              </div>
            </div>
            <div>
              <div className="text-white/80 text-sm font-medium mb-1 titillium-web-semibold">Next Sync</div>
              <div className="text-white/60 text-sm titillium-web-light">
                {formatTime(health?.next_sync || null)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sync Configuration */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <RefreshCw className="h-6 w-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white titillium-web-semibold">Sync Configuration</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-white/80 text-sm font-medium mb-2 titillium-web-semibold">
              Current Sync Interval
            </label>
            <div className="space-y-2">
              <div className="text-white text-lg titillium-web-semibold">
                {syncInterval?.interval_hours} hours
              </div>
              <div className="text-sm text-white/60 titillium-web-light">
                Source: {syncInterval?.source || 'Unknown'}
              </div>
              {syncInterval?.last_updated && (
                <div className="text-sm text-white/60 titillium-web-light">
                  Last updated: {formatTime(syncInterval.last_updated)}
                </div>
              )}
            </div>
          </div>
          
          <div>
            <label className="block text-white/80 text-sm font-medium mb-2 titillium-web-semibold">
              Update Sync Interval
            </label>
            <div className="space-y-3">
              <div className="flex gap-3">
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={newInterval}
                  onChange={(e) => setNewInterval(Number(e.target.value))}
                  className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:border-purple-400 focus:outline-none titillium-web-regular"
                />
                <button
                  onClick={handleUpdateInterval}
                  disabled={saving || newInterval === syncInterval?.interval_hours}
                  className="glass-button-primary px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 titillium-web-semibold"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
              <div className="text-sm text-white/60 titillium-web-light">
                Hours between automatic syncs (1-168)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="h-6 w-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white titillium-web-semibold">Notifications</h3>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium titillium-web-semibold">Sync Completion</div>
              <div className="text-white/60 text-sm titillium-web-light">Get notified when sync operations complete</div>
            </div>
            <div className="text-white/60 text-sm">
              Configured via environment
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium titillium-web-semibold">Error Alerts</div>
              <div className="text-white/60 text-sm titillium-web-light">Receive alerts for sync errors and failures</div>
            </div>
            <div className="text-white/60 text-sm">
              Configured via environment
            </div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-purple-500/10 border border-purple-400/30 rounded-lg">
          <div className="flex items-start gap-3">
            <Bell className="h-5 w-5 text-purple-400 mt-0.5" />
            <div>
              <div className="text-purple-300 font-medium text-sm titillium-web-regular">Environment Configuration</div>
              <div className="text-purple-200/80 text-sm mt-1 titillium-web-light">
                Notification settings are configured through environment variables in your ListSync setup.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 