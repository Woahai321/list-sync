/**
 * API Service Layer for ListSync
 * Wraps all backend API calls using Nuxt's $fetch
 */

import type {
  SyncStats,
  List,
  SystemHealth,
  OverseerrStatus,
  RecentActivity,
  CreateListRequest,
  SyncInterval,
  SyncProcessStatus,
  LiveSyncStatus,
  PaginatedResponse,
  ProcessedItem,
} from '~/types'

export class ApiService {
  private baseURL: string

  constructor(baseURL: string = '') {
    this.baseURL = baseURL
  }

  /**
   * Generic request wrapper with error handling
   */
  private async request<T>(
    endpoint: string,
    options?: RequestInit & { method?: string; body?: any }
  ): Promise<T> {
    try {
      const url = `${this.baseURL}${endpoint}`
      
      const response = await $fetch<T>(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      return response
    } catch (error: any) {
      console.error(`API Error [${endpoint}]:`, error)
      throw new Error(error?.message || `Failed to fetch ${endpoint}`)
    }
  }

  // ==========================================
  // Dashboard & Statistics
  // ==========================================

  async getStats(): Promise<SyncStats> {
    return this.request<SyncStats>('/stats/sync')
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/system/health')
  }

  async getDataQuality() {
    return this.request('/stats/data-quality')
  }

  async getStatusBreakdown() {
    return this.request('/stats/status-breakdown')
  }

  // ==========================================
  // Lists Management
  // ==========================================

  async getLists(): Promise<{ lists: List[] }> {
    return this.request<{ lists: List[] }>('/lists')
  }

  async addList(list: CreateListRequest): Promise<void> {
    return this.request<void>('/lists', {
      method: 'POST',
      body: list,
    })
  }

  async deleteList(listType: string, listId: string): Promise<void> {
    return this.request<void>(`/lists/${listType}/${encodeURIComponent(listId)}`, {
      method: 'DELETE',
    })
  }

  async validateList(url: string) {
    return this.request('/lists/validate', {
      method: 'POST',
      body: { url },
    })
  }

  // ==========================================
  // Sync Operations
  // ==========================================

  async triggerSync(): Promise<any> {
    return this.request('/sync/trigger', {
      method: 'POST',
    })
  }

  async triggerSingleListSync(listType: string, listId: string): Promise<any> {
    return this.request('/sync/single', {
      method: 'POST',
      body: {
        list_type: listType,
        list_id: listId,
      },
    })
  }

  async getSyncStatus(): Promise<SyncProcessStatus> {
    return this.request<SyncProcessStatus>('/sync/status')
  }

  async getLiveSyncStatus(): Promise<LiveSyncStatus> {
    return this.request<LiveSyncStatus>('/sync/status/live')
  }

  async cancelSync(jobId: string): Promise<void> {
    return this.request<void>(`/sync/${jobId}/cancel`, {
      method: 'POST',
    })
  }

  // ==========================================
  // Sync Interval Configuration
  // ==========================================

  async getSyncInterval(): Promise<SyncInterval> {
    return this.request<SyncInterval>('/sync-interval')
  }

  async updateSyncInterval(intervalHours: number): Promise<SyncInterval> {
    return this.request<SyncInterval>('/sync-interval', {
      method: 'PUT',
      body: { interval_hours: intervalHours },
    })
  }

  async syncIntervalFromEnv() {
    return this.request('/sync-interval/sync-from-env', {
      method: 'POST',
    })
  }

  // ==========================================
  // Activity & History
  // ==========================================

  async getRecentActivity(
    limit: number = 20,
    source: 'database' | 'docker' | 'auto' = 'auto'
  ): Promise<RecentActivity[]> {
    return this.request<RecentActivity[]>(
      `/activity/recent?limit=${limit}&source=${source}`
    )
  }

  async getItems(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<any>> {
    return this.request<PaginatedResponse<any>>(
      `/items?page=${page}&limit=${limit}`
    )
  }

  async getProcessedItems(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<ProcessedItem>> {
    return this.request<PaginatedResponse<ProcessedItem>>(
      `/processed?page=${page}&limit=${limit}`
    )
  }

  async getFailedItems(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<ProcessedItem>> {
    return this.request<PaginatedResponse<ProcessedItem>>(
      `/failures?page=${page}&limit=${limit}`
    )
  }

  async getSuccessfulItems(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<ProcessedItem>> {
    return this.request<PaginatedResponse<ProcessedItem>>(
      `/successful?page=${page}&limit=${limit}`
    )
  }

  async getRequestedItems(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<ProcessedItem>> {
    return this.request<PaginatedResponse<ProcessedItem>>(
      `/requested?page=${page}&limit=${limit}`
    )
  }

  // ==========================================
  // Overseerr Integration
  // ==========================================

  async getOverseerrStatus(): Promise<OverseerrStatus> {
    return this.request<OverseerrStatus>('/overseerr/status')
  }

  async getOverseerrConfig() {
    return this.request('/overseerr/config')
  }

  async testConnection() {
    return this.request('/config/test')
  }

  // ==========================================
  // System & Time
  // ==========================================

  async getCurrentTime(): Promise<{
    current_time: string
    timestamp: number
    formatted: {
      date: string
      time: string
      full: string
    }
  }> {
    return this.request('/system/time')
  }

  async getSystemStatus() {
    return this.request('/system/status')
  }

  async getProcesses() {
    return this.request('/system/processes')
  }

  async getLogInfo() {
    return this.request('/system/logs')
  }

  async testDatabase() {
    return this.request('/system/database/test')
  }

  // ==========================================
  // Timezone
  // ==========================================

  async getSupportedTimezones() {
    return this.request('/timezone/supported')
  }

  async getCurrentTimezone() {
    return this.request('/timezone/current')
  }

  async validateTimezone(timezone: string) {
    return this.request('/timezone/validate', {
      method: 'POST',
      body: { timezone },
    })
  }

  // ==========================================
  // Notifications
  // ==========================================

  async testDiscordNotification(webhookUrl: string): Promise<{ success: boolean; message: string; timestamp: string }> {
    return this.request<{ success: boolean; message: string; timestamp: string }>('/notifications/test', {
      method: 'POST',
      body: JSON.stringify({
        webhook_url: webhookUrl
      })
    })
  }

  // ==========================================
  // Logs
  // ==========================================

  async getLogEntries(
    limit: number = 100,
    level?: string,
    category?: string
  ) {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    if (level) params.append('level', level)
    if (category) params.append('category', category)

    return this.request(`/logs/entries?${params.toString()}`)
  }

  async getLogCategories() {
    return this.request('/logs/categories')
  }

  async getLogStats() {
    return this.request('/logs/stats')
  }

  // ==========================================
  // Analytics
  // ==========================================

  async getAnalytics(timeRange: string = '24h') {
    return this.request(`/analytics?time_range=${timeRange}`)
  }

  async getAnalyticsOverview(timeRange: string = '24h') {
    return this.request(`/analytics/overview?time_range=${timeRange}`)
  }

  async getMediaAdditions(timeRange: string = '24h') {
    return this.request(`/analytics/media-additions?time_range=${timeRange}`)
  }

  async getListFetches(timeRange: string = '24h') {
    return this.request(`/analytics/list-fetches?time_range=${timeRange}`)
  }

  async getMatchingAnalytics(timeRange: string = '24h') {
    return this.request(`/analytics/matching?time_range=${timeRange}`)
  }

  async getSearchFailures(timeRange: string = '24h') {
    return this.request(`/analytics/search-failures?time_range=${timeRange}`)
  }

  async getScrapingPerformance(timeRange: string = '24h') {
    return this.request(`/analytics/scraping-performance?time_range=${timeRange}`)
  }

  async getSourceDistribution(timeRange: string = '24h') {
    return this.request(`/analytics/source-distribution?time_range=${timeRange}`)
  }

  async getSelectorPerformance(timeRange: string = '24h') {
    return this.request(`/analytics/selector-performance?time_range=${timeRange}`)
  }

  async getGenreDistribution(timeRange: string = '24h') {
    return this.request(`/analytics/genre-distribution?time_range=${timeRange}`)
  }

  async getYearDistribution(timeRange: string = '24h') {
    return this.request(`/analytics/year-distribution?time_range=${timeRange}`)
  }

  // ==========================================
  // Sync History
  // ==========================================

  async getSyncHistory(
    limit: number = 50,
    offset: number = 0,
    type?: 'full' | 'single',
    startDate?: string,
    endDate?: string
  ): Promise<import('~/types').SyncHistoryResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    })
    
    if (type) params.append('type', type)
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    return this.request<import('~/types').SyncHistoryResponse>(
      `/sync-history?${params.toString()}`
    )
  }

  async getSyncSession(sessionId: string): Promise<import('~/types').SyncHistorySession> {
    return this.request<import('~/types').SyncHistorySession>(
      `/sync-history/${sessionId}`
    )
  }

  async getSyncHistoryStats(): Promise<import('~/types').SyncHistoryStats> {
    return this.request<import('~/types').SyncHistoryStats>('/sync-history/stats')
  }

  // ==========================================
  // Utility
  // ==========================================

  async ping(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/ping')
  }
}

// Create singleton instance
let apiServiceInstance: ApiService | null = null

/**
 * Get the API service instance
 * Uses Nuxt runtime config for base URL
 */
export function useApiService(): ApiService {
  if (!apiServiceInstance) {
    const config = useRuntimeConfig()
    const baseURL = `${config.public.apiUrl}${config.public.apiBase}`
    apiServiceInstance = new ApiService(baseURL)
  }
  return apiServiceInstance
}

// Export default instance
export const apiService = {
  getInstance: useApiService,
}

