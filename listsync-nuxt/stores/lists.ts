/**
 * Lists Store - Manages media lists
 */

import { defineStore } from 'pinia'
import type { List, CreateListRequest } from '~/types'

export const useListsStore = defineStore('lists', {
  state: () => ({
    lists: [] as List[],
    loading: false,
    error: null as string | null,
    lastFetched: null as Date | null,
    
    // Filters
    searchTerm: '',
    sourceFilter: 'all',
    sortBy: 'last_synced' as 'name' | 'last_synced' | 'item_count',
  }),

  getters: {
    /**
     * Get filtered and sorted lists
     */
    filteredLists: (state) => {
      let filtered = state.lists

      // Apply search filter
      if (state.searchTerm) {
        const search = state.searchTerm.toLowerCase()
        filtered = filtered.filter(
          (list) =>
            list.list_id.toLowerCase().includes(search) ||
            list.list_type.toLowerCase().includes(search) ||
            list.display_name.toLowerCase().includes(search)
        )
      }

      // Apply source filter
      if (state.sourceFilter && state.sourceFilter !== 'all') {
        filtered = filtered.filter(
          (list) => list.list_type.toLowerCase().includes(state.sourceFilter.toLowerCase())
        )
      }

      // Apply sorting
      filtered = [...filtered].sort((a, b) => {
        switch (state.sortBy) {
          case 'name':
            return a.list_id.localeCompare(b.list_id)
          
          case 'item_count':
            return b.item_count - a.item_count
          
          case 'last_synced':
          default:
            if (!a.last_synced && !b.last_synced) return 0
            if (!a.last_synced) return 1
            if (!b.last_synced) return -1
            return new Date(b.last_synced).getTime() - new Date(a.last_synced).getTime()
        }
      })

      return filtered
    },

    /**
     * Get lists grouped by source
     */
    listsBySource: (state) => {
      const grouped: Record<string, List[]> = {}
      
      state.lists.forEach((list) => {
        const source = list.list_type
        if (!grouped[source]) {
          grouped[source] = []
        }
        grouped[source].push(list)
      })

      return grouped
    },

    /**
     * Get total list count
     */
    totalLists: (state) => state.lists.length,

    /**
     * Get total items across all lists
     */
    totalItems: (state) => {
      return state.lists.reduce((sum, list) => sum + list.item_count, 0)
    },

    /**
     * Check if any filters are active
     */
    hasActiveFilters: (state) => {
      return state.searchTerm !== '' || state.sourceFilter !== 'all'
    },

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
     * Fetch all lists
     */
    async fetchLists(force = false) {
      // Skip if not stale and not forced
      if (!force && !this.isStale && this.lists.length > 0) {
        return
      }

      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        const response = await api.getLists()
        
        this.lists = response.lists || []
        this.lastFetched = new Date()
      } catch (err: any) {
        this.error = err.message || 'Failed to fetch lists'
        console.error('Error fetching lists:', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * Add a new list
     */
    async addList(request: CreateListRequest) {
      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        await api.addList(request)
        
        // Refresh lists after adding
        await this.fetchLists(true)
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message || 'Failed to add list'
        console.error('Error adding list:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Delete a list
     */
    async deleteList(listType: string, listId: string) {
      this.loading = true
      this.error = null

      try {
        const api = useApiService()
        await api.deleteList(listType, listId)
        
        // Remove from local state immediately
        this.lists = this.lists.filter(
          (list) => !(list.list_type === listType && list.list_id === listId)
        )
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message || 'Failed to delete list'
        console.error('Error deleting list:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Sync a specific list
     */
    async syncList(listType: string, listId: string) {
      try {
        const api = useApiService()
        await api.triggerSingleListSync(listType, listId)
        
        return { success: true }
      } catch (err: any) {
        console.error('Error syncing list:', err)
        throw err
      }
    },

    /**
     * Set search term
     */
    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    /**
     * Set source filter
     */
    setSourceFilter(source: string) {
      this.sourceFilter = source
    },

    /**
     * Set sort order
     */
    setSortBy(sortBy: 'name' | 'last_synced' | 'item_count') {
      this.sortBy = sortBy
    },

    /**
     * Clear all filters
     */
    clearFilters() {
      this.searchTerm = ''
      this.sourceFilter = 'all'
      this.sortBy = 'last_synced'
    },

    /**
     * Refresh lists (force fetch)
     */
    async refresh() {
      await this.fetchLists(true)
    },

    /**
     * Reset store state
     */
    reset() {
      this.lists = []
      this.loading = false
      this.error = null
      this.lastFetched = null
      this.clearFilters()
    },
  },
})

