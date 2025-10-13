/**
 * Composable for accessing the API service
 * Uses relative URLs to work with Nitro proxy in Docker
 */

export function useApiService() {
  // Use relative URLs - Nitro proxy will handle routing
  // In Docker: /api/* → proxied to internal API server
  // This works for both SSR and client-side
  const baseURL = '/api'

  return {
    // Dashboard & Statistics
    async getStats() {
      return $fetch(`${baseURL}/stats/sync`)
    },

    async getSystemHealth() {
      return $fetch(`${baseURL}/system/health`)
    },

    async getDataQuality() {
      return $fetch(`${baseURL}/stats/data-quality`)
    },

    async getStatusBreakdown() {
      return $fetch(`${baseURL}/stats/status-breakdown`)
    },

    // Lists Management
    async getLists() {
      return $fetch(`${baseURL}/lists`)
    },

    async addList(list: any) {
      return $fetch(`${baseURL}/lists`, {
        method: 'POST',
        body: list,
      })
    },

    async deleteList(listType: string, listId: string) {
      return $fetch(`${baseURL}/lists/${listType}/${encodeURIComponent(listId)}`, {
        method: 'DELETE',
      })
    },

    async validateList(url: string) {
      return $fetch(`${baseURL}/lists/validate`, {
        method: 'POST',
        body: { url },
      })
    },

    // Sync Operations
    async triggerSync() {
      return $fetch(`${baseURL}/sync/trigger`, {
        method: 'POST',
      })
    },

    async syncSingleList(listType: string, listId: string) {
      return $fetch(`${baseURL}/sync/single`, {
        method: 'POST',
        body: {
          list_type: listType,
          list_id: listId,
        },
      })
    },

    async triggerSingleListSync(listType: string, listId: string) {
      return $fetch(`${baseURL}/sync/single`, {
        method: 'POST',
        body: {
          list_type: listType,
          list_id: listId,
        },
      })
    },

    async getSyncStatus() {
      return $fetch(`${baseURL}/sync/status`)
    },

    async getLiveSyncStatus() {
      return $fetch(`${baseURL}/sync/status/live`)
    },

    async cancelSync(jobId: string) {
      return $fetch(`${baseURL}/sync/${jobId}/cancel`, {
        method: 'POST',
      })
    },

    // Sync Interval Configuration
    async getSyncInterval() {
      return $fetch(`${baseURL}/sync-interval`)
    },

    async updateSyncInterval(intervalHours: number) {
      return $fetch(`${baseURL}/sync-interval`, {
        method: 'PUT',
        body: { interval_hours: intervalHours },
      })
    },

    async syncIntervalFromEnv() {
      return $fetch(`${baseURL}/sync-interval/sync-from-env`, {
        method: 'POST',
      })
    },

    // Activity & History
    async getRecentActivity(
      limit: number = 20,
      page: number = 1
    ) {
      return $fetch(`${baseURL}/activity/recent?page=${page}&limit=${limit}&_t=${Date.now()}`)
    },

    async getItems() {
      return $fetch(`${baseURL}/items`)
    },

    async getProcessedItems(page: number = 1, limit: number = 50) {
      return $fetch(`${baseURL}/processed?page=${page}&limit=${limit}&_t=${Date.now()}`)
    },

    async getFailedItems(page: number = 1, limit: number = 50) {
      const response: any = await $fetch(`${baseURL}/failures?page=${page}&limit=${limit}`)
      
      // Transform API response to expected format
      const failures = [
        ...(response.not_found || []).map((item: any) => ({
          id: `not_found_${item.title}_${item.timestamp}`,
          title: item.title,
          description: item.reason || 'Not found in database',
          media_type: item.media_type || 'movie',
          year: item.year,
          failed_at: item.timestamp,
          error_type: 'not_found',
          error_message: item.reason || 'Not found in database',
          retryable: false,
        })),
        ...(response.errors || []).map((item: any) => ({
          id: `error_${item.title}_${item.timestamp}`,
          title: item.title,
          description: item.reason || 'Processing error',
          media_type: item.media_type || 'movie',
          year: item.year,
          failed_at: item.timestamp,
          error_type: 'error',
          error_message: item.reason || 'Processing error occurred',
          retryable: true,
        }))
      ]
      
      return {
        items: failures,
        total: response.total_failures || 0,
        pagination: response.pagination
      }
    },

    async getSuccessfulItems(page: number = 1, limit: number = 50) {
      return $fetch(`${baseURL}/successful?page=${page}&limit=${limit}`)
    },

    async getRequestedItems(page: number = 1, limit: number = 50) {
      return $fetch(`${baseURL}/requested?page=${page}&limit=${limit}`)
    },

    // Overseerr Integration
    async getOverseerrStatus() {
      return $fetch(`${baseURL}/overseerr/status`)
    },

    async getOverseerrConfig() {
      return $fetch(`${baseURL}/overseerr/config`)
    },

    async checkOverseerr() {
      return $fetch(`${baseURL}/overseerr/status`)
    },

    async testConnection() {
      return $fetch(`${baseURL}/config/test`)
    },

    // System & Time
    async getCurrentTime() {
      return $fetch(`${baseURL}/system/time`)
    },

    async getSystemStatus() {
      return $fetch(`${baseURL}/system/status`)
    },

    async getProcesses() {
      return $fetch(`${baseURL}/system/processes`)
    },

    async getLogInfo() {
      return $fetch(`${baseURL}/system/logs`)
    },

    async testDatabase() {
      return $fetch(`${baseURL}/system/database/test`)
    },

    // Timezone
    async getSupportedTimezones() {
      return $fetch(`${baseURL}/timezone/supported`)
    },

    async getCurrentTimezone() {
      return $fetch(`${baseURL}/timezone/current`)
    },

    async validateTimezone(timezone: string) {
      return $fetch(`${baseURL}/timezone/validate`, {
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

      return $fetch(`${baseURL}/logs/entries?${params.toString()}`)
    },

    async getLogCategories() {
      return $fetch(`${baseURL}/logs/categories`)
    },

    async getLogStats() {
      return $fetch(`${baseURL}/logs/stats`)
    },

    // Analytics
    async getAnalytics(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics?time_range=${timeRange}`)
    },

    async getAnalyticsOverview(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/overview?time_range=${timeRange}`)
    },

    async getMediaAdditions(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/media-additions?time_range=${timeRange}`)
    },

    async getListFetches(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/list-fetches?time_range=${timeRange}`)
    },

    async getMatchingAnalytics(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/matching?time_range=${timeRange}`)
    },

    async getSearchFailures(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/search-failures?time_range=${timeRange}`)
    },

    async getScrapingPerformance(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/scraping-performance?time_range=${timeRange}`)
    },

    async getSourceDistribution(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/source-distribution?time_range=${timeRange}`)
    },

    async getSelectorPerformance(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/selector-performance?time_range=${timeRange}`)
    },

    async getGenreDistribution(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/genre-distribution?time_range=${timeRange}`)
    },

    async getYearDistribution(timeRange: string = '24h') {
      return $fetch(`${baseURL}/analytics/year-distribution?time_range=${timeRange}`)
    },

    // Utility
    async ping() {
      return $fetch(`${baseURL}/ping`)
    },

    // Settings
    async getConfig() {
      return $fetch(`${baseURL}/settings/config`)
    },

    async updateConfig(config: any) {
      return $fetch(`${baseURL}/settings/config`, {
        method: 'POST',
        body: config,
      })
    },

    // Notifications
    async testDiscordNotification(webhookUrl: string) {
      return $fetch(`${baseURL}/notifications/test`, {
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
      
      return $fetch(`${baseURL}/sync-history?${params.toString()}`)
    },

    async getSyncSession(sessionId: string) {
      return $fetch(`${baseURL}/sync-history/${sessionId}`)
    },

    async getSyncHistoryStats() {
      return $fetch(`${baseURL}/sync-history/stats`)
    },

    async getSyncSessionRawLogs(sessionId: string) {
      return $fetch(`${baseURL}/sync-history/${sessionId}/raw-logs`)
    },
  }
}

