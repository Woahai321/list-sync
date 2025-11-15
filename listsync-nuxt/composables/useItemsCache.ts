/**
 * Smart caching and prefetching for enriched items
 * This composable implements a stale-while-revalidate pattern
 * and prefetches data in the background for instant page loads
 */

interface CacheEntry {
  data: any
  timestamp: number
  isStale: boolean
}

// Global cache state (persists across component mounts)
const cache = new Map<string, CacheEntry>()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes fresh
const STALE_TTL = 30 * 60 * 1000 // 30 minutes stale but usable

export function useItemsCache() {
  const api = useApiService()

  /**
   * Get cache key for a specific page
   */
  const getCacheKey = (page: number, limit: number) => {
    return `items_enriched_p${page}_l${limit}`
  }

  /**
   * Check if cached data exists and is usable (fresh or stale)
   */
  const getCached = (page: number, limit: number): CacheEntry | null => {
    const key = getCacheKey(page, limit)
    const entry = cache.get(key)
    
    if (!entry) return null
    
    const now = Date.now()
    const age = now - entry.timestamp
    
    // If completely expired, remove and return null
    if (age > STALE_TTL) {
      cache.delete(key)
      return null
    }
    
    // Mark as stale if beyond fresh TTL
    entry.isStale = age > CACHE_TTL
    
    return entry
  }

  /**
   * Store data in cache
   */
  const setCache = (page: number, limit: number, data: any) => {
    const key = getCacheKey(page, limit)
    cache.set(key, {
      data,
      timestamp: Date.now(),
      isStale: false
    })
  }

  /**
   * Fetch enriched items with smart caching
   * Returns cached data immediately if available, fetches fresh data in background if stale
   */
  const fetchEnrichedItems = async (page: number, limit: number, forceRefresh = false) => {
    const cached = getCached(page, limit)
    
    // If we have fresh cache and not forcing refresh, return it immediately
    if (cached && !cached.isStale && !forceRefresh) {
      console.log(`✨ Using fresh cache for page ${page}`)
      return cached.data
    }
    
    // If we have stale cache, return it but fetch fresh in background
    if (cached && cached.isStale && !forceRefresh) {
      console.log(`⚡ Using stale cache for page ${page}, refreshing in background...`)
      
      // Return stale data immediately
      const staleData = cached.data
      
      // Fetch fresh data in background (don't await)
      api.getEnrichedItems(page, limit)
        .then(freshData => {
          console.log(`✅ Background refresh completed for page ${page}`)
          setCache(page, limit, freshData)
        })
        .catch(err => {
          console.warn(`⚠️  Background refresh failed for page ${page}:`, err)
        })
      
      return staleData
    }
    
    // No cache or force refresh - fetch fresh data
    console.log(`🔄 Fetching fresh data for page ${page}`)
    const freshData = await api.getEnrichedItems(page, limit)
    setCache(page, limit, freshData)
    return freshData
  }

  /**
   * Prefetch multiple pages in the background
   * Call this from dashboard or other pages to warm up the cache
   */
  const prefetchPages = async (pages: number[] = [1], limit = 50) => {
    console.log(`🚀 Prefetching pages: ${pages.join(', ')}`)
    
    const prefetchPromises = pages.map(async (page) => {
      // Only prefetch if not already cached
      const cached = getCached(page, limit)
      if (cached && !cached.isStale) {
        console.log(`⏭️  Skipping page ${page} - already cached`)
        return
      }
      
      try {
        const data = await api.getEnrichedItems(page, limit)
        setCache(page, limit, data)
        console.log(`✅ Prefetched page ${page}`)
      } catch (err) {
        console.warn(`⚠️  Failed to prefetch page ${page}:`, err)
      }
    })
    
    // Don't await - let them run in background
    Promise.all(prefetchPromises)
  }

  /**
   * Clear all cache (useful when data changes significantly)
   */
  const clearCache = () => {
    cache.clear()
    console.log('🗑️  Cache cleared')
  }

  /**
   * Get cache statistics
   */
  const getCacheStats = () => {
    const now = Date.now()
    let fresh = 0
    let stale = 0
    
    cache.forEach(entry => {
      const age = now - entry.timestamp
      if (age < CACHE_TTL) {
        fresh++
      } else if (age < STALE_TTL) {
        stale++
      }
    })
    
    return {
      total: cache.size,
      fresh,
      stale,
      expired: cache.size - fresh - stale
    }
  }

  return {
    fetchEnrichedItems,
    prefetchPages,
    clearCache,
    getCacheStats
  }
}

