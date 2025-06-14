// Core types for ListSync Web UI

export interface SyncStats {
  total_processed: number      // Total items processed after deduplication
  successful_items: number     // requested + already_requested + already_available + skipped
  total_requested: number      // Items actually requested to Overseerr
  total_errors: number         // error + not_found items
  success_rate: number
  duplicates_in_current_sync: number  // Duplicates found within the current sync session
  last_updated: string
  breakdown: {
    requested: number
    available: number
    skipped: number
    errors: number
  }
}

export interface List {
  id: number
  list_type: string
  list_id: string
  display_name: string
  item_count: number | null
}

export interface MediaItem {
  title: string
  mediaType: 'movie' | 'tv'
  year?: number
  imdbId?: string
  overseerrId?: number
  status: 'pending' | 'available' | 'requested' | 'failed'
  lastSynced: string
}

export interface SyncJob {
  id: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  startTime: string
  endTime?: string
  itemsProcessed: number
  totalItems: number
  errors?: string[]
}

export interface Config {
  overseerrUrl: string
  overseerrApiKey: string
  overseerrUserId: string
  syncInterval: number
  automatedMode: boolean
  overseerr4K: boolean
  discordWebhookUrl?: string
}

export interface ConnectionStatus {
  isConnected: boolean
  lastChecked: string
  error?: string
}

export interface CreateListRequest {
  type: 'imdb' | 'trakt' | 'letterboxd' | 'mdblist' | 'stevenlu'
  listId: string
}

export interface UpdateConfigRequest {
  overseerrUrl?: string
  overseerrApiKey?: string
  overseerrUserId?: string
  syncInterval?: number
  automatedMode?: boolean
  overseerr4K?: boolean
  discordWebhookUrl?: string
}

export interface ListValidation {
  isValid: boolean
  itemCount?: number
  error?: string
  previewItems?: Array<{
    title: string
    year?: number
    mediaType: 'movie' | 'tv'
  }>
}

export interface SyncResult {
  id: string
  timestamp: string
  listsProcessed: number
  itemsFound: number
  itemsRequested: number
  itemsSkipped: number
  errors: number
  duration: number
  syncedLists: Array<{
    type: string
    id: string
    itemCount: number
    url?: string
    error?: string
  }>
}

export interface SyncOptions {
  dryRun?: boolean
  is4K?: boolean
  specificLists?: string[]
}

export interface SystemHealth {
  database: boolean
  process: boolean
  sync_status: string
  last_sync?: string
  next_sync?: string
}

export interface OverseerrStatus {
  isConnected: boolean
  version?: string
  updateAvailable?: boolean
  commitsBehind?: number
  restartRequired?: boolean
  error?: string
  lastChecked: string
}

export interface DashboardData {
  stats: SyncStats
  recentActivity: MediaItem[]
  systemHealth: SystemHealth
  activeJobs: SyncJob[]
}

export interface RecentActivity {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  status: string
  last_synced: string
  action: 'synced' | 'requested' | 'available' | 'error' | 'skipped'
} 