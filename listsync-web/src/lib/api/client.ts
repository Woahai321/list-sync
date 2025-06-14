import type {
  SyncStats,
  List,
  MediaItem,
  SyncJob,
  Config,
  ConnectionStatus,
  CreateListRequest,
  UpdateConfigRequest,
  ListValidation,
  SyncResult,
  SyncOptions,
  SystemHealth,
  OverseerrStatus,
  DashboardData,
  RecentActivity,
} from "@/lib/types/index"

class ApiClient {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API Error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  // Dashboard & Statistics
  async getDashboardData(): Promise<DashboardData> {
    return this.request<DashboardData>("/dashboard")
  }

  async getStats(): Promise<SyncStats> {
    return this.request<SyncStats>("/stats/sync")
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>("/system/health")
  }

  // Lists Management
  async getLists(): Promise<List[]> {
    return this.request<List[]>("/lists")
  }

  async addList(list: CreateListRequest): Promise<void> {
    return this.request<void>("/lists", {
      method: "POST",
      body: JSON.stringify(list),
    })
  }

  async removeList(listId: string): Promise<void> {
    return this.request<void>(`/lists/${listId}`, {
      method: "DELETE",
    })
  }

  async validateList(url: string): Promise<ListValidation> {
    return this.request<ListValidation>("/lists/validate", {
      method: "POST",
      body: JSON.stringify({ url }),
    })
  }

  // Sync Operations
  async triggerSync(options?: SyncOptions): Promise<SyncJob> {
    return this.request<SyncJob>("/sync/trigger", {
      method: "POST",
      body: JSON.stringify(options || {}),
    })
  }

  async getSyncStatus(): Promise<SyncJob | null> {
    return this.request<SyncJob | null>("/sync/status")
  }

  // Signal-based sync trigger (new implementation)
  async triggerManualSync(): Promise<{
    success: boolean
    message: string
    signals_sent: Array<{
      pid: number
      cmdline: string[]
      status: string
    }>
    errors?: Array<{
      pid: number
      error: string
    }>
    note: string
    timestamp: string
  }> {
    return this.request("/sync/trigger", {
      method: "POST",
    })
  }

  async getSyncProcessStatus(): Promise<{
    processes_found: number
    processes: Array<{
      pid: number
      status: string
      created: string
      cmdline: string[]
      memory_percent?: number
      cpu_percent?: number
      can_signal: boolean
      error?: string
    }>
    can_trigger_sync: boolean
    sync_method: string
    timestamp: string
  }> {
    return this.request("/sync/status")
  }

  async getSyncHistory(limit = 10): Promise<SyncResult[]> {
    return this.request<SyncResult[]>(`/sync/history?limit=${limit}`)
  }

  async cancelSync(jobId: string): Promise<void> {
    return this.request<void>(`/sync/${jobId}/cancel`, {
      method: "POST",
    })
  }

  // Configuration
  async getConfig(): Promise<Config> {
    return this.request<Config>("/config")
  }

  async updateConfig(config: UpdateConfigRequest): Promise<void> {
    return this.request<void>("/config", {
      method: "PUT",
      body: JSON.stringify(config),
    })
  }

  async testConnection(): Promise<ConnectionStatus> {
    return this.request<ConnectionStatus>("/config/test")
  }

  // Media Items
  async getRecentItems(limit = 20): Promise<RecentActivity[]> {
    return this.request<RecentActivity[]>(`/activity/recent?limit=${limit}`)
  }

  async getRecentItemsFromDocker(limit = 20): Promise<RecentActivity[]> {
    return this.request<RecentActivity[]>(`/activity/recent/docker?limit=${limit}`)
  }

  async getRecentItemsWithSource(limit = 20, source: 'database' | 'docker' | 'auto' = 'auto'): Promise<RecentActivity[]> {
    return this.request<RecentActivity[]>(`/activity/recent?limit=${limit}&source=${source}`)
  }

  async searchItems(query: string): Promise<MediaItem[]> {
    return this.request<MediaItem[]>(`/items/search?q=${encodeURIComponent(query)}`)
  }

  // Overseerr Status Check
  async getOverseerrStatus(): Promise<OverseerrStatus> {
    return this.request<OverseerrStatus>("/overseerr/status")
  }

  // Current Time for live updates
  async getCurrentTime(): Promise<{
    current_time: string
    timestamp: number
    formatted: {
      date: string
      time: string
      full: string
    }
  }> {
    return this.request("/system/time")
  }

  // Real-time updates via Server-Sent Events
  createEventSource(endpoint: string): EventSource {
    return new EventSource(`${this.baseUrl}${endpoint}`)
  }

  // Utility methods
  async ping(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>("/ping")
  }
}

export const apiClient = new ApiClient() 