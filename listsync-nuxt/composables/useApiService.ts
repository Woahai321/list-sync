/**
 * Composable for accessing the API service
 * Uses relative URLs to work with Nitro proxy in Docker
 */

import type { FailedItemsResponse, FailedItem } from '~/types'

export function useApiService() {
  // Use relative URLs - Nitro proxy will handle routing
  // In Docker: /api/* → proxied to internal API server
  // This works for both SSR and client-side
  const baseURL = '/api'

  // Error wrapper for consistent error handling
  const handleApiError = (error: any, endpoint: string): never => {
    console.error(`API Error [${endpoint}]:`, error)
    
    // Extract error message from various error formats
    let errorMessage = 'An unexpected error occurred'
    let errorCode: string | undefined
    
    if (error?.data?.detail) {
      // FastAPI error format: { detail: "message" }
      errorMessage = error.data.detail
    } else if (error?.data?.error) {
      // Custom error format: { error: "message" }
      errorMessage = error.data.error
      errorCode = error.data.error_code
    } else if (error?.data?.message) {
      // Generic error format: { message: "message" }
      errorMessage = error.data.message
    } else if (error?.message) {
      // Standard Error object
      errorMessage = error.message
    } else if (typeof error === 'string') {
      errorMessage = error
    }
    
    // Create enhanced error with consistent format
    const enhancedError: any = new Error(errorMessage)
    enhancedError.statusCode = error?.statusCode || error?.status || 500
    enhancedError.code = errorCode || error?.code
    enhancedError.endpoint = endpoint
    enhancedError.originalError = error
    
    throw enhancedError
  }

  // Wrapper function for API calls with error handling
  const apiCall = async <T>(endpoint: string, options?: any): Promise<T> => {
    try {
      return await $fetch<T>(endpoint, options)
    } catch (error: any) {
      return handleApiError(error, endpoint)
    }
  }

  return {
    // Dashboard & Statistics
    async getStats() {
      return apiCall(`${baseURL}/stats/sync`)
    },

    async getSystemHealth() {
      return apiCall(`${baseURL}/system/health`)
    },

    async getDataQuality() {
      return apiCall(`${baseURL}/stats/data-quality`)
    },

    async getStatusBreakdown() {
      return apiCall(`${baseURL}/stats/status-breakdown`)
    },

    // Lists Management
    async getLists() {
      return apiCall(`${baseURL}/lists`)
    },

    async addList(list: any) {
      return apiCall(`${baseURL}/lists`, {
        method: 'POST',
        body: list,
      })
    },

    async deleteList(listType: string, listId: string) {
      return apiCall(`${baseURL}/lists/${listType}/${encodeURIComponent(listId)}`, {
        method: 'DELETE',
      })
    },

    async validateList(url: string) {
      return apiCall(`${baseURL}/lists/validate`, {
        method: 'POST',
        body: { url },
      })
    },

    // Sync Operations
    async triggerSync() {
      return apiCall(`${baseURL}/sync/trigger`, {
        method: 'POST',
      })
    },

    async syncSingleList(listType: string, listId: string) {
      return apiCall(`${baseURL}/sync/single`, {
        method: 'POST',
        body: {
          list_type: listType,
          list_id: listId,
        },
      })
    },

    async triggerSingleListSync(listType: string, listId: string) {
      return apiCall(`${baseURL}/sync/single`, {
        method: 'POST',
        body: {
          list_type: listType,
          list_id: listId,
        },
      })
    },

    async getSyncStatus() {
      return apiCall(`${baseURL}/sync/status`)
    },

    async getLiveSyncStatus() {
      return apiCall(`${baseURL}/sync/status/live`)
    },

    async cancelSync(jobId: string) {
      return apiCall(`${baseURL}/sync/${jobId}/cancel`, {
        method: 'POST',
      })
    },

    // Sync Interval Configuration
    async getSyncInterval() {
      return apiCall(`${baseURL}/sync-interval`)
    },

    async updateSyncInterval(intervalHours: number) {
      return apiCall(`${baseURL}/sync-interval`, {
        method: 'PUT',
        body: { interval_hours: intervalHours },
      })
    },

    async syncIntervalFromEnv() {
      return apiCall(`${baseURL}/sync-interval/sync-from-env`, {
        method: 'POST',
      })
    },

    // Activity & History
    async getRecentActivity(
      limit: number = 20,
      page: number = 1
    ) {
      return apiCall(`${baseURL}/activity/recent?page=${page}&limit=${limit}&_t=${Date.now()}`)
    },

    async getItems() {
      return apiCall(`${baseURL}/items`)
    },

    async getEnrichedItems(page: number = 1, limit: number = 50) {
      return apiCall(`${baseURL}/items/enriched?page=${page}&limit=${limit}`)
    },

    async getProcessedItems(page: number = 1, limit: number = 50) {
      return apiCall(`${baseURL}/processed?page=${page}&limit=${limit}&_t=${Date.now()}`)
    },

    async getFailedItems(page: number = 1, limit: number = 50): Promise<FailedItemsResponse> {
      const response: any = await apiCall(`${baseURL}/failures?page=${page}&limit=${limit}`)
      
      // Transform API response to expected format
      const failures: FailedItem[] = [
        ...(response.not_found || []).map((item: any) => ({
          id: `not_found_${item.title}_${item.timestamp}`,
          title: item.title,
          description: item.reason || 'Not found in database',
          media_type: (item.media_type || 'movie') as 'movie' | 'tv',
          year: item.year,
          failed_at: item.timestamp,
          error_type: 'not_found' as const,
          error_message: item.reason || 'Not found in database',
          retryable: false,
        })),
        ...(response.errors || []).map((item: any) => ({
          id: `error_${item.title}_${item.timestamp}`,
          title: item.title,
          description: item.reason || 'Processing error',
          media_type: (item.media_type || 'movie') as 'movie' | 'tv',
          year: item.year,
          failed_at: item.timestamp,
          error_type: 'error' as const,
          error_message: item.reason || 'Processing error occurred',
          retryable: true,
        }))
      ]
      
      return {
        items: failures,
        total: response.total_failures || 0,
        pagination: response.pagination || {
          page,
          limit,
          total_items: response.total_failures || 0,
          total_pages: 0,
          has_next: false,
          has_prev: false,
        }
      }
    },

    async getSuccessfulItems(page: number = 1, limit: number = 50) {
      return apiCall(`${baseURL}/successful?page=${page}&limit=${limit}`)
    },

    async getRequestedItems(page: number = 1, limit: number = 50) {
      return apiCall(`${baseURL}/requested?page=${page}&limit=${limit}`)
    },

    // Overseerr Integration
    async getOverseerrStatus() {
      return apiCall(`${baseURL}/overseerr/status`)
    },

    async getOverseerrConfig() {
      return apiCall(`${baseURL}/overseerr/config`)
    },

    async checkOverseerr() {
      return apiCall(`${baseURL}/overseerr/status`)
    },

    async testConnection() {
      return apiCall(`${baseURL}/config/test`)
    },

    // System & Time
    async getCurrentTime() {
      return apiCall(`${baseURL}/system/time`)
    },

    async getSystemStatus() {
      return apiCall(`${baseURL}/system/status`)
    },

    async getProcesses() {
      return apiCall(`${baseURL}/system/processes`)
    },

    async getLogInfo() {
      return apiCall(`${baseURL}/system/logs`)
    },

    async testDatabase() {
      return apiCall(`${baseURL}/system/database/test`)
    },

    // Timezone
    async getSupportedTimezones() {
      return apiCall(`${baseURL}/timezone/supported`)
    },

    async getCurrentTimezone() {
      return apiCall(`${baseURL}/timezone/current`)
    },

    async validateTimezone(timezone: string) {
      return apiCall(`${baseURL}/timezone/validate`, {
        method: 'POST',
        body: { timezone },
      })
    },

    // Logs
    async getLogEntries(
      limit: number = 100,
      level?: string,
      category?: string
    ) {
      const params = new URLSearchParams()
      params.append('limit', limit.toString())
      if (level) params.append('level', level)
      if (category) params.append('category', category)

      return apiCall(`${baseURL}/logs/entries?${params.toString()}`)
    },

    async getLogCategories() {
      return apiCall(`${baseURL}/logs/categories`)
    },

    async getLogStats() {
      return apiCall(`${baseURL}/logs/stats`)
    },

    // Analytics
    async getAnalytics(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics?time_range=${timeRange}`)
    },

    async getAnalyticsOverview(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/overview?time_range=${timeRange}`)
    },

    async getMediaAdditions(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/media-additions?time_range=${timeRange}`)
    },

    async getListFetches(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/list-fetches?time_range=${timeRange}`)
    },

    async getMatchingAnalytics(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/matching?time_range=${timeRange}`)
    },

    async getSearchFailures(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/search-failures?time_range=${timeRange}`)
    },

    async getScrapingPerformance(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/scraping-performance?time_range=${timeRange}`)
    },

    async getSourceDistribution(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/source-distribution?time_range=${timeRange}`)
    },

    async getSelectorPerformance(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/selector-performance?time_range=${timeRange}`)
    },

    async getGenreDistribution(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/genre-distribution?time_range=${timeRange}`)
    },

    async getYearDistribution(timeRange: string = '24h') {
      return apiCall(`${baseURL}/analytics/year-distribution?time_range=${timeRange}`)
    },

    // Utility
    async ping() {
      return apiCall(`${baseURL}/ping`)
    },

    // Settings
    async getConfig() {
      return apiCall(`${baseURL}/settings/config`)
    },

    async updateConfig(config: any) {
      return apiCall(`${baseURL}/settings/config`, {
        method: 'POST',
        body: config,
      })
    },

    // Notifications
    async testDiscordNotification(webhookUrl: string) {
      return apiCall(`${baseURL}/notifications/test`, {
        method: 'POST',
        body: {
          webhook_url: webhookUrl
        }
      })
    },

    // Alias for consistency with setup wizard
    async testDiscordWebhook(webhookUrl: string) {
      return apiCall(`${baseURL}/notifications/test`, {
        method: 'POST',
        body: {
          webhook_url: webhookUrl
        }
      })
    },

    // Sync History
    async getSyncHistory(
      limit: number = 50,
      offset: number = 0,
      type?: 'full' | 'single',
      startDate?: string,
      endDate?: string
    ) {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      })
      
      if (type) params.append('type', type)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      return apiCall(`${baseURL}/sync-history?${params.toString()}`)
    },

    async getSyncSession(sessionId: string) {
      return apiCall(`${baseURL}/sync-history/${sessionId}`)
    },

    async getSyncHistoryStats() {
      return apiCall(`${baseURL}/sync-history/stats`)
    },

    async getSyncSessionRawLogs(sessionId: string) {
      return apiCall(`${baseURL}/sync-history/${sessionId}/raw-logs`)
    },

    // Setup Wizard
    async checkSetupStatus() {
      return apiCall(`${baseURL}/setup/status`)
    },

    async migrateFromEnv() {
      return apiCall(`${baseURL}/setup/migrate-from-env`, {
        method: 'POST',
      })
    },

    async saveStepEssential(data: any) {
      return apiCall(`${baseURL}/setup/step1/essential`, {
        method: 'POST',
        body: data,
      })
    },

    async saveStepConfiguration(data: any) {
      return apiCall(`${baseURL}/setup/step2/configuration`, {
        method: 'POST',
        body: data,
      })
    },

    async saveStepContentSources(data: any) {
      return apiCall(`${baseURL}/setup/step3/content-sources`, {
        method: 'POST',
        body: data,
      })
    },

    async completeSetup() {
      return apiCall(`${baseURL}/setup/complete`, {
        method: 'POST',
      })
    },

    // Setup Wizard - Individual Validation Tests
    async testOverseerrConnection(data: { overseerr_url: string; overseerr_api_key: string }) {
      return apiCall(`${baseURL}/setup/test/overseerr`, {
        method: 'POST',
        body: data,
      })
    },

    async testTraktClientId(data: { trakt_client_id: string }) {
      return apiCall(`${baseURL}/setup/test/trakt`, {
        method: 'POST',
        body: data,
      })
    },

    // Collections
    async getCollections(
      page: number = 1,
      limit: number = 50,
      search: string = '',
      sort: string = 'popularity'
    ) {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        search,
        sort,
      })
      return apiCall(`${baseURL}/collections?${params.toString()}`)
    },

    async getPopularCollections() {
      return apiCall(`${baseURL}/collections/popular`)
    },

    async getRandomCollections(count: number = 5) {
      return apiCall(`${baseURL}/collections/random?count=${count}`)
    },

    async getSyncedCollectionsInfo() {
      return apiCall(`${baseURL}/collections/synced`)
    },

    async getCollectionDetails(franchiseName: string) {
      const encoded = encodeURIComponent(franchiseName)
      return apiCall(`${baseURL}/collections/${encoded}`)
    },

    async getCollectionMovies(franchiseName: string) {
      const encoded = encodeURIComponent(franchiseName)
      return apiCall(`${baseURL}/collections/${encoded}/movies`)
    },

    async getCollectionPoster(franchiseName: string) {
      const encoded = encodeURIComponent(franchiseName)
      return apiCall(`${baseURL}/collections/${encoded}/poster`)
    },

    async getCollectionPostersBatch(franchiseNames: string[]) {
      return apiCall(`${baseURL}/collections/posters/batch`, {
        method: 'POST',
        body: JSON.stringify({ franchise_names: franchiseNames }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    },

    async requestSingleMedia(tmdbId: number, mediaType: string = 'movie', is4k?: boolean) {
      return apiCall(`${baseURL}/media/request`, {
        method: 'POST',
        body: JSON.stringify({ 
          tmdb_id: tmdbId,
          media_type: mediaType,
          is_4k: is4k
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    },

    async syncCollection(franchiseName: string) {
      const encoded = encodeURIComponent(franchiseName)
      return apiCall(`${baseURL}/collections/${encoded}/sync`, {
        method: 'POST',
      })
    },
  }
}

