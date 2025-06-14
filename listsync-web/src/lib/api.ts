import { 
  SystemStatus, 
  SyncStats, 
  RecentActivity, 
  ListSyncItem,
  SyncInterval,
  ProcessInfo,
  LogInfo
} from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4222/api'

// Helper function for API calls
async function apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`)
  }
  
  return response.json()
}

// System Status API
export const systemApi = {
  // Get comprehensive system status
  async getStatus(): Promise<SystemStatus> {
    return apiCall<SystemStatus>('/system/status')
  },

  // Get process information
  async getProcessInfo(): Promise<ProcessInfo[]> {
    return apiCall<ProcessInfo[]>('/system/processes')
  },

  // Get log information and sync timing
  async getLogInfo(): Promise<LogInfo> {
    return apiCall<LogInfo>('/system/logs')
  },

  // Test database connectivity
  async testDatabase(): Promise<{ connected: boolean; error?: string }> {
    return apiCall('/system/database/test')
  },

  // Get system health check
  async getHealthCheck(): Promise<{
    database: boolean
    process: boolean
    sync_status: 'healthy' | 'overdue' | 'unknown'
    last_sync: string | null
    next_sync: string | null
  }> {
    return apiCall('/system/health')
  }
}

// Sync Interval API
export const syncIntervalApi = {
  // Get current sync interval (from database or env)
  async getCurrent(): Promise<SyncInterval> {
    return apiCall<SyncInterval>('/sync-interval')
  },

  // Update sync interval in database
  async update(intervalHours: number): Promise<{ success: boolean; message: string }> {
    return apiCall('/sync-interval', {
      method: 'PUT',
      body: JSON.stringify({ interval_hours: intervalHours })
    })
  },

  // Sync interval from environment to database
  async syncFromEnv(): Promise<{ success: boolean; message: string; interval_hours: number }> {
    return apiCall('/sync-interval/sync-from-env', {
      method: 'POST'
    })
  }
}

// Statistics API with deduplication
export const statsApi = {
  // Get deduplicated sync statistics
  async getSyncStats(): Promise<SyncStats> {
    return apiCall<SyncStats>('/stats/sync')
  },

  // Get raw vs deduplicated counts
  async getDataQuality(): Promise<{
    total_raw_items: number
    total_unique_items: number
    duplicates_found: number
    success_rate: number
    status_breakdown: Record<string, number>
    most_duplicated: Array<[string, number]>
  }> {
    return apiCall('/stats/data-quality')
  },

  // Get success/failure breakdown
  async getStatusBreakdown(): Promise<{
    successful: {
      count: number
      statuses: string[]
    }
    failed: {
      count: number
      statuses: string[]
    }
    other: {
      count: number
      statuses: string[]
    }
  }> {
    return apiCall('/stats/status-breakdown')
  }
}

// Recent Activity API
export const activityApi = {
  // Get recent sync activity (deduplicated)
  async getRecent(limit: number = 10): Promise<RecentActivity[]> {
    return apiCall<RecentActivity[]>(`/activity/recent?limit=${limit}`)
  },

  // Get activity by status
  async getByStatus(status: string, limit: number = 10): Promise<RecentActivity[]> {
    return apiCall<RecentActivity[]>(`/activity/status/${status}?limit=${limit}`)
  },

  // Get activity timeline
  async getTimeline(days: number = 7): Promise<Array<{
    date: string
    successful: number
    failed: number
    total: number
  }>> {
    return apiCall(`/activity/timeline?days=${days}`)
  }
}

// Lists API
export const listsApi = {
  // Get all configured lists
  async getAll(): Promise<Array<{
    id: number
    list_type: string
    list_id: string
    display_name: string
    item_count?: number
  }>> {
    return apiCall('/lists')
  },

  // Add new list
  async add(listType: string, listId: string): Promise<{ success: boolean; message: string }> {
    return apiCall('/lists', {
      method: 'POST',
      body: JSON.stringify({ list_type: listType, list_id: listId })
    })
  },

  // Delete list
  async delete(listType: string, listId: string): Promise<{ success: boolean; message: string }> {
    return apiCall(`/lists/${listType}/${encodeURIComponent(listId)}`, {
      method: 'DELETE'
    })
  }
}

// Sync Control API
export const syncControlApi = {
  // Trigger manual sync
  async triggerSync(): Promise<{ success: boolean; message: string; job_id?: string }> {
    return apiCall('/sync/trigger', {
      method: 'POST'
    })
  },

  // Get sync job status
  async getSyncJobStatus(jobId: string): Promise<{
    status: 'running' | 'completed' | 'failed'
    progress?: number
    message?: string
    started_at: string
    completed_at?: string
  }> {
    return apiCall(`/sync/job/${jobId}`)
  },

  // Stop running sync
  async stopSync(): Promise<{ success: boolean; message: string }> {
    return apiCall('/sync/stop', {
      method: 'POST'
    })
  }
}

// Items API
export const itemsApi = {
  // Get all synced items (deduplicated)
  async getAll(page: number = 1, limit: number = 50): Promise<{
    items: ListSyncItem[]
    total: number
    page: number
    limit: number
    total_pages: number
  }> {
    return apiCall(`/items?page=${page}&limit=${limit}`)
  },

  // Search items
  async search(query: string, page: number = 1, limit: number = 50): Promise<{
    items: ListSyncItem[]
    total: number
    page: number
    limit: number
    total_pages: number
  }> {
    return apiCall(`/items/search?q=${encodeURIComponent(query)}&page=${page}&limit=${limit}`)
  },

  // Get item by ID
  async getById(id: number): Promise<ListSyncItem> {
    return apiCall<ListSyncItem>(`/items/${id}`)
  },

  // Retry failed item
  async retry(id: number): Promise<{ success: boolean; message: string }> {
    return apiCall(`/items/${id}/retry`, {
      method: 'POST'
    })
  }
}

// Export all APIs
export const api = {
  system: systemApi,
  syncInterval: syncIntervalApi,
  stats: statsApi,
  activity: activityApi,
  lists: listsApi,
  syncControl: syncControlApi,
  items: itemsApi
} 