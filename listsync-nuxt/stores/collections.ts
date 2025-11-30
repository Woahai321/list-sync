/**
 * Collections Store - Manages movie collections
 */

import { defineStore } from 'pinia'
import type { Collection, CollectionsResponse, CollectionMoviesResponse, CollectionPosterResponse, CollectionSyncResponse } from '~/types'

export const useCollectionsStore = defineStore('collections', {
  state: () => ({
    collections: [] as Collection[],
    popularCollections: [] as Collection[],
    selectedCollection: null as Collection | null,
    loading: false,
    syncing: false,
    error: null as string | null,
    
    // Pagination
    currentPage: 1,
    totalPages: 1,
    total: 0,
    
    // Filters
    searchTerm: '',
    sortBy: 'total_votes' as 'popularity' | 'rating' | 'movie_count' | 'name' | 'total_votes',
    
    // Poster cache - prevents re-fetching already loaded posters
    posterCache: new Map<string, string | null>() as Map<string, string | null>,
  }),

  getters: {
    /**
     * Get filtered collections
     */
    filteredCollections: (state) => {
      let filtered = state.collections

      // Apply search filter
      if (state.searchTerm) {
        const search = state.searchTerm.toLowerCase()
        filtered = filtered.filter(
          (collection) =>
            collection.franchise.toLowerCase().includes(search)
        )
      }

      return filtered
    },
  },

  actions: {
    /**
     * Fetch popular collections (top 20)
     * Optimized: Show collections immediately, load posters in background
     */
    async fetchPopular() {
      this.loading = true
      this.error = null
      
      try {
        const api = useApiService()
        const response = await api.getPopularCollections()
        
        if (response && response.collections) {
          // Show collections immediately with cached posters if available
          this.popularCollections = response.collections.map(collection => ({
            ...collection,
            poster_url: this.posterCache.get(collection.franchise) || null
          }))
          
          // Load posters in background (non-blocking) - only for uncached ones
          const batchSize = 5 // Smaller batches for popular collections
          const collections = response.collections
          
          // Load posters in batches without blocking
          for (let i = 0; i < collections.length; i += batchSize) {
            const batch = collections.slice(i, i + batchSize)
            
            // Process batch in background
            Promise.all(
              batch.map(async (collection, batchIdx) => {
                // Skip if already cached
                if (this.posterCache.has(collection.franchise)) {
                  return
                }
                
                try {
                  const posterResponse = await api.getCollectionPoster(collection.franchise)
                  const posterUrl = posterResponse?.poster_url || null
                  
                  // Cache the poster
                  this.posterCache.set(collection.franchise, posterUrl)
                  
                  // Find and update the collection
                  const collectionIndex = this.popularCollections.findIndex(c => c.franchise === collection.franchise)
                  
                  if (collectionIndex !== -1) {
                    // Create new array to trigger reactivity
                    const updatedCollections = [...this.popularCollections]
                    updatedCollections[collectionIndex] = {
                      ...updatedCollections[collectionIndex],
                      poster_url: posterUrl
                    }
                    this.popularCollections = updatedCollections
                  }
                } catch (error) {
                  console.warn(`Failed to fetch poster for ${collection.franchise}:`, error)
                  this.posterCache.set(collection.franchise, null)
                }
              })
            ).catch(err => {
              console.warn(`Error loading poster batch:`, err)
            })
            
            // Small delay between batches
            if (i + batchSize < collections.length) {
              await new Promise(resolve => setTimeout(resolve, 100))
            }
          }
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch popular collections'
        console.error('Error fetching popular collections:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch all collections with pagination
     * Optimized: Returns collections immediately, loads posters in background with proper reactivity
     */
    async fetchAll(page: number = 1, limit: number = 50, search: string = '', sort: string = 'total_votes', append: boolean = false) {
      this.loading = true
      this.error = null
      this.currentPage = page
      this.searchTerm = search
      this.sortBy = sort as 'popularity' | 'rating' | 'movie_count' | 'name' | 'total_votes'
      
      try {
        const api = useApiService()
        const response: CollectionsResponse = await api.getCollections(page, limit, search, sort)
        
        if (response) {
          // First, add collections WITH cached posters if available
          const collectionsWithCachedPosters = response.collections.map(collection => ({
            ...collection,
            poster_url: this.posterCache.get(collection.franchise) || null
          }))
          
          // Append or replace based on append flag
          if (append && page > 1) {
            // Remove duplicates by franchise name
            const existingFranchises = new Set(this.collections.map(c => c.franchise))
            const newCollections = collectionsWithCachedPosters.filter(c => !existingFranchises.has(c.franchise))
            this.collections = [...this.collections, ...newCollections]
          } else {
            this.collections = collectionsWithCachedPosters
          }
          
          this.total = response.total
          this.totalPages = response.total_pages
          
          // Load posters in batches ONLY for uncached collections
          const batchSize = 10
          const collectionsToLoad = response.collections.filter(c => !this.posterCache.has(c.franchise))
          
          // If all are cached, we're done!
          if (collectionsToLoad.length === 0) {
            this.loading = false
            return
          }
          
          // Create a map of franchise to index for quick lookup
          const franchiseToIndex = new Map<string, number>()
          this.collections.forEach((c, idx) => {
            franchiseToIndex.set(c.franchise, idx)
          })
          
          // Load posters in batches (non-blocking, fire and forget)
          for (let i = 0; i < collectionsToLoad.length; i += batchSize) {
            const batch = collectionsToLoad.slice(i, i + batchSize)
            
            // Load batch of posters in parallel (don't await - let them load in background)
            Promise.all(
              batch.map(async (collection) => {
                try {
                  const posterResponse = await api.getCollectionPoster(collection.franchise)
                  const posterUrl = posterResponse?.poster_url || null
                  
                  // Cache the poster
                  this.posterCache.set(collection.franchise, posterUrl)
                  
                  // Find the collection in the current array
                  const collectionIndex = franchiseToIndex.get(collection.franchise)
                  
                  if (collectionIndex !== undefined && collectionIndex >= 0 && collectionIndex < this.collections.length) {
                    // Update using Vue's reactivity - create new object and array
                    const updatedCollection = {
                      ...this.collections[collectionIndex],
                      poster_url: posterUrl
                    }
                    
                    // Create new array to trigger reactivity
                    const updatedCollections = [...this.collections]
                    updatedCollections[collectionIndex] = updatedCollection
                    this.collections = updatedCollections
                    
                    // Update the map for future lookups
                    franchiseToIndex.set(collection.franchise, collectionIndex)
                  }
                } catch (error) {
                  console.warn(`Failed to fetch poster for ${collection.franchise}:`, error)
                  this.posterCache.set(collection.franchise, null)
                }
              })
            ).catch(err => {
              console.warn(`Error loading poster batch ${Math.floor(i / batchSize) + 1}:`, err)
            })
            
            // Small delay between batches to avoid overwhelming the API
            if (i + batchSize < collectionsToLoad.length) {
              await new Promise(resolve => setTimeout(resolve, 50))
            }
          }
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch collections'
        console.error('Error fetching collections:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch collection details
     */
    async fetchCollectionDetails(franchiseName: string) {
      this.loading = true
      this.error = null
      
      try {
        const api = useApiService()
        const collection = await api.getCollectionDetails(franchiseName)
        
        if (collection) {
          // Fetch poster
          try {
            const posterResponse = await api.getCollectionPoster(franchiseName)
            this.selectedCollection = {
              ...collection,
              poster_url: posterResponse?.poster_url || null
            }
          } catch (error) {
            console.warn(`Failed to fetch poster for ${franchiseName}:`, error)
            this.selectedCollection = {
              ...collection,
              poster_url: null
            }
          }
        }
      } catch (error: any) {
        this.error = error.message || 'Failed to fetch collection details'
        console.error('Error fetching collection details:', error)
        this.selectedCollection = null
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch collection poster
     */
    async fetchCollectionPoster(franchiseName: string): Promise<string | null> {
      try {
        const api = useApiService()
        const response: CollectionPosterResponse = await api.getCollectionPoster(franchiseName)
        return response?.poster_url || null
      } catch (error) {
        console.warn(`Failed to fetch poster for ${franchiseName}:`, error)
        return null
      }
    },

    /**
     * Sync collection to Overseerr - uses same flow as list syncs
     */
    async syncCollection(franchiseName: string) {
      this.syncing = true
      this.error = null
      
      try {
        const api = useApiService()
        // Use the same endpoint as list syncs - treats collection as a list
        await api.triggerSingleListSync('collections', franchiseName)
        
        // Refresh popular collections if this one is in the list
        const isPopular = this.popularCollections.some(c => c.franchise === franchiseName)
        if (isPopular) {
          await this.fetchPopular()
        }
        
        return { success: true }
      } catch (error: any) {
        this.error = error.message || 'Failed to sync collection'
        console.error('Error syncing collection:', error)
        throw error
      } finally {
        this.syncing = false
      }
    },

    /**
     * Clear selected collection
     */
    clearSelected() {
      this.selectedCollection = null
    },
  },
})

