/**
 * Users Store - Manages Overseerr users
 */

import { defineStore } from 'pinia'
import type { OverseerrUser } from '~/types'

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [] as OverseerrUser[],
    loading: false,
    syncing: false,
    error: null as string | null,
    lastFetched: null as Date | null,
    lastSynced: null as Date | null,
  }),

  getters:  {
    /**
     * Get total user count
     */
    totalUsers: (state) => state.users.length,

    /**
     * Get user by ID
     */
    getUserById: (state) => (userId: string) => {
      return state.users.find(user => user.id === userId)
    },

    /**
     * Check if data is stale (older than 5 minutes)
     */
    isStale: (state) => {
      if (!state.lastFetched) return true
      const now = new Date()
      const diff = now.getTime() - state.lastFetched.getTime()
      return diff > 300000 // 5 minutes
    },
  },

  actions: {
    /**
     * Fetch all users from database
     */
    async fetchUsers(force = false) {
      // Skip if not stale and not forced
      if (!force && !this.isStale && this.users.length > 0) {
        return
      }

      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const response = await api.getOverseerrUsers()
        
        this.users = response.users || []
        this.lastFetched = new Date()
      } catch (err: any) {
        this.error = err.message || 'Failed to fetch users'
        console.error('Error fetching users:', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * Sync users from Overseerr API
     */
    async syncUsers() {
      this.syncing = true
      this.error = null

      try {
        const api = useApiService()
        const response = await api.syncOverseerrUsers()
        
        this.users = response.users || []
        this.lastFetched = new Date()
        this.lastSynced = new Date()
        
        return { success: true, count: response.count }
      } catch (err: any) {
        this.error = err.message || 'Failed to sync users'
        console.error('Error syncing users:', err)
        throw err
      } finally {
        this.syncing = false
      }
    },

    /**
     * Reset store state
     */
    reset() {
      this.users = []
      this.loading = false
      this.syncing = false
      this.error = null
      this.lastFetched = null
      this.lastSynced = null
    },
  },
})

