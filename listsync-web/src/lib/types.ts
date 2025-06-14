export interface SyncInterval {
  interval_hours: number
  source: 'database' | 'environment' | 'default'
  last_updated?: string
}

export interface ProcessInfo {
  pid: number
  status: string
  created: string
  cmdline: string[]
  memory_percent?: number
  cpu_percent?: number
}

export interface LogInfo {
  last_sync_start?: string
  last_sync_complete?: string
  sync_interval_hours?: number
  next_sync_time?: string
  sync_status: 'healthy' | 'overdue' | 'unknown' | 'scheduled'
  recent_errors: string[]
  log_file_size: number
  log_last_modified: string
}

export interface SystemStatus {
  database: {
    connected: boolean
    file_exists: boolean
    file_size: number
    last_modified: string
    error?: string
  }
  process: {
    running: boolean
    processes: ProcessInfo[]
    error?: string
  }
  sync: {
    status: 'healthy' | 'overdue' | 'unknown' | 'scheduled'
    last_sync?: string
    next_sync?: string
    interval_hours?: number
    error?: string
  }
  logs: LogInfo
  overall_health: 'healthy' | 'warning' | 'error'
}

export interface ListSyncItem {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  imdb_id?: string
  overseerr_id?: number
  status: 'already_available' | 'already_requested' | 'available' | 'requested' | 'not_found' | 'error'
  last_synced: string
  list_sources?: string[]
}

export interface RecentActivity {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  status: string
  last_synced: string
  action: 'synced' | 'requested' | 'available' | 'error'
}

export interface SyncStats {
  total_items: number
  successful_items: number
  failed_items: number
  success_rate: number
  last_updated: string
} 