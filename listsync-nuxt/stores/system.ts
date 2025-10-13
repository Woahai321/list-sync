/**
 * System Store - Manages system health and Overseerr status
 */

import { defineStore } from 'pinia'
import type { SystemHealth, OverseerrStatus } from '~/types'

export const useSystemStore = defineStore('system', {
  state: () => ({
    health: null as SystemHealth | null,
    overseerrStatus: null as OverseerrStatus | null,
    loading: false,
    error: null as string | null,
    lastFetched: null as Date | null,
  }),

  getters: {
    /**
     * Check if system is healthy
     */
    isHealthy: (state) => {
      if (!state.health) return false
      return state.health.database && state.health.process
    },

    /**
     * Check if Overseerr is connected
     */
    isOverseerrConnected: (state) => {
      return state.overseerrStatus?.isConnected || false
    },

    /**
     * Get all services status
     */
    servicesStatus: (state) => {
      return {
        database: state.health?.database || false,
        process: state.health?.process || false,
        overseerr: state.overseerrStatus?.isConnected || false,
      }
    },

    /**
     * Count healthy services
     */
    healthyServicesCount: (state) => {
      const services = state.servicesStatus
      return Object.values(services).filter(Boolean).length
    },

    /**
     * Get total services count
     */
    totalServicesCount: () => 3, // database, process, overseerr

    /**
     * Get overall health percentage
     */
    healthPercentage: (state) => {
      const count = state.healthyServicesCount
      const total = state.totalServicesCount
      return Math.round((count / total) * 100)
    },

    /**
     * Get last sync time
     */
    lastSyncTime: (state) => state.health?.last_sync || null,

    /**
     * Get next sync time
     */
    nextSyncTime: (state) => state.health?.next_sync || null,

    /**
     * Get sync status
     */
    syncStatus: (state) => state.health?.sync_status || 'unknown',

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
     * Fetch system health
     */
    async checkHealth(force = false) {
      // Skip if not stale and not forced
      if (!force && !this.isStale && this.health) {
        return
      }

      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const health = await api.getSystemHealth()
        
        this.health = health
        this.lastFetched = new Date()
      } catch (err: any) {
        this.error = err.message || 'Failed to fetch system health'
        console.error('Error fetching system health:', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch Overseerr status
     */
    async checkOverseerr(force = false) {
      // Skip if not stale and not forced
      if (!force && !this.isStale && this.overseerrStatus) {
        return
      }

      try {
        const api = useApiService()
        const status = await api.getOverseerrStatus()
        
        this.overseerrStatus = status
      } catch (err: any) {
        console.error('Error fetching Overseerr status:', err)
        // Don't set error for Overseerr - it's optional
      }
    },

    /**
     * Refresh all system data
     */
    async refresh() {
      await Promise.all([
        this.checkHealth(true),
        this.checkOverseerr(true),
      ])
    },

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh(intervalMs = 30000) {
      return setInterval(() => {
        this.checkHealth()
        this.checkOverseerr()
      }, intervalMs)
    },

    /**
     * Reset store state
     */
    reset() {
      this.health = null
      this.overseerrStatus = null
      this.loading = false
      this.error = null
      this.lastFetched = null
    },
  },
})

