/**
 * Sync Store - Manages synchronization state and operations
 */

import { defineStore } from 'pinia'
import type { LiveSyncStatus, SyncInterval } from '~/types'

export const useSyncStore = defineStore('sync', {
  state: () => ({
    // Sync status
    isRunning: false,
    status: 'idle' as string,
    progress: 0,
    currentItem: null as string | null,
    itemsProcessed: 0,
    totalItems: 0,
    
    // Live sync data
    liveSyncStatus: null as LiveSyncStatus | null,
    
    // Timing
    lastSync: null as string | null,
    nextSync: null as string | null,
    
    // Sync interval
    syncInterval: null as SyncInterval | null,
    
    // State
    loading: false,
    error: null as string | null,
    lastFetched: null as Date | null,
  }),

  getters: {
    /**
     * Check if sync can be triggered
     */
    canSync: (state) => !state.isRunning,

    /**
     * Get time until next sync in milliseconds
     */
    timeUntilNextSync: (state) => {
      if (!state.nextSync) return null
      
      const nextSyncDate = new Date(state.nextSync)
      const now = new Date()
      const diff = nextSyncDate.getTime() - now.getTime()
      
      return diff > 0 ? diff : 0
    },

    /**
     * Get formatted time until next sync
     */
    formattedTimeUntilNextSync: (state) => {
      const diff = state.timeUntilNextSync
      if (!diff) return null
      
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      }
      return `${minutes}m`
    },

    /**
     * Get current sync progress percentage
     */
    progressPercentage: (state) => {
      if (state.totalItems === 0) return 0
      return Math.round((state.itemsProcessed / state.totalItems) * 100)
    },

    /**
     * Check if sync is active
     */
    isSyncing: (state) => state.isRunning || state.liveSyncStatus?.is_running,

    /**
     * Get sync interval in hours
     */
    intervalHours: (state) => state.syncInterval?.interval_hours || 24,
  },

  actions: {
    /**
     * Fetch live sync status
     */
    async fetchLiveSyncStatus() {
      try {
        const api = useApiService()
        const status = await api.getLiveSyncStatus()
        
        this.liveSyncStatus = status
        this.isRunning = status.is_running
        this.status = status.status
        
        // Parse progress if available in last_activity
        if (status.last_activity) {
          const progressMatch = status.last_activity.match(/\((\d+)\/(\d+)\)/)
          if (progressMatch) {
            this.itemsProcessed = parseInt(progressMatch[1])
            this.totalItems = parseInt(progressMatch[2])
          }
        }
      } catch (err: any) {
        console.error('Error fetching live sync status:', err)
      }
    },

    /**
     * Fetch sync interval configuration
     */
    async fetchSyncInterval() {
      try {
        const api = useApiService()
        const interval = await api.getSyncInterval()
        
        this.syncInterval = interval
      } catch (err: any) {
        console.error('Error fetching sync interval:', err)
      }
    },

    /**
     * Trigger manual sync
     */
    async triggerSync() {
      if (!this.canSync) {
        throw new Error('Sync already in progress')
      }

      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const response = await api.triggerSync()
        
        this.isRunning = true
        this.status = 'running'
        this.progress = 0
        
        return response
      } catch (err: any) {
        this.error = err.message || 'Failed to trigger sync'
        console.error('Error triggering sync:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Update sync interval
     */
    async updateSyncInterval(intervalHours: number) {
      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const interval = await api.updateSyncInterval(intervalHours)
        
        this.syncInterval = interval
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message || 'Failed to update sync interval'
        console.error('Error updating sync interval:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Set sync timing info
     */
    setSyncTiming(lastSync: string | null, nextSync: string | null) {
      this.lastSync = lastSync
      this.nextSync = nextSync
    },

    /**
     * Start monitoring sync progress
     */
    startMonitoring() {
      // Poll live sync status every 2 seconds
      const intervalId = setInterval(async () => {
        await this.fetchLiveSyncStatus()
        
        // Stop monitoring if sync is no longer running
        if (!this.isRunning && !this.liveSyncStatus?.is_running) {
          clearInterval(intervalId)
        }
      }, 2000)

      return intervalId
    },

    /**
     * Stop sync (if supported by API)
     */
    async stopSync() {
      this.isRunning = false
      this.status = 'stopped'
    },

    /**
     * Reset sync state
     */
    resetSyncState() {
      this.isRunning = false
      this.status = 'idle'
      this.progress = 0
      this.currentItem = null
      this.itemsProcessed = 0
      this.totalItems = 0
    },

    /**
     * Refresh all sync data
     */
    async refresh() {
      await Promise.all([
        this.fetchLiveSyncStatus(),
        this.fetchSyncInterval(),
      ])
    },

    /**
     * Reset store state
     */
    reset() {
      this.isRunning = false
      this.status = 'idle'
      this.progress = 0
      this.currentItem = null
      this.itemsProcessed = 0
      this.totalItems = 0
      this.liveSyncStatus = null
      this.lastSync = null
      this.nextSync = null
      this.syncInterval = null
      this.loading = false
      this.error = null
      this.lastFetched = null
    },
  },
})

