/**
 * Stats Store - Manages sync statistics
 */

import { defineStore } from 'pinia'
import type { SyncStats } from '~/types'

export const useStatsStore = defineStore('stats', {
  state: () => ({
    syncStats: null as SyncStats | null,
    loading: false,
    error: null as string | null,
    lastFetched: null as Date | null,
  }),

  getters: {
    /**
     * Get total items processed
     */
    totalProcessed: (state) => state.syncStats?.total_processed || 0,

    /**
     * Get successful items count
     */
    successfulItems: (state) => state.syncStats?.successful_items || 0,

    /**
     * Get total requested items
     */
    totalRequested: (state) => state.syncStats?.total_requested || 0,

    /**
     * Get total errors
     */
    totalErrors: (state) => state.syncStats?.total_errors || 0,

    /**
     * Get success rate percentage
     */
    successRate: (state) => state.syncStats?.success_rate || 0,

    /**
     * Get duplicates count
     */
    duplicatesCount: (state) => state.syncStats?.duplicates_in_current_sync || 0,

    /**
     * Get breakdown stats
     */
    breakdown: (state) => state.syncStats?.breakdown || {
      requested: 0,
      available: 0,
      skipped: 0,
      errors: 0,
    },

    /**
     * Check if stats are available
     */
    hasStats: (state) => state.syncStats !== null,

    /**
     * Check if data is stale (older than 30 seconds)
     */
    isStale: (state) => {
      if (!state.lastFetched) return true
      const now = new Date()
      const diff = now.getTime() - state.lastFetched.getTime()
      return diff > 30000 // 30 seconds
    },
  },

  actions: {
    /**
     * Fetch sync statistics
     */
    async fetchStats(force = false) {
      // Skip if not stale and not forced
      if (!force && !this.isStale && this.hasStats) {
        return
      }

      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const stats = await api.getStats()
        
        this.syncStats = stats
        this.lastFetched = new Date()
      } catch (err: any) {
        this.error = err.message || 'Failed to fetch stats'
        console.error('Error fetching stats:', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * Refresh stats (force fetch)
     */
    async refresh() {
      await this.fetchStats(true)
    },

    /**
     * Reset store state
     */
    reset() {
      this.syncStats = null
      this.loading = false
      this.error = null
      this.lastFetched = null
    },

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh(intervalMs = 30000) {
      return setInterval(() => {
        this.fetchStats()
      }, intervalMs)
    },
  },
})

