// Core types for ListSync Nuxt Frontend

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
  list_url?: string
  url?: string
  display_name: string
  item_count: number
  status?: string
  last_synced?: string
  user_id?: string
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
  list_type: 'imdb' | 'trakt' | 'trakt_special' | 'letterboxd' | 'mdblist' | 'stevenlu' | 'tmdb' | 'simkl' | 'tvdb'
  list_id: string
  user_id?: string
}

export interface OverseerrUser {
  id: string
  display_name: string
  email: string
  avatar: string
  last_synced?: string
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

export interface SyncInterval {
  interval_hours: number
  source: string
  last_updated: string | null
}

export interface SyncProcessStatus {
  processes_found: number
  can_trigger_sync: boolean
  sync_method: string
  timestamp: string
  processes?: Array<{
    pid: number
    status: string
    created: string
    cmdline: string[]
    memory_percent?: number
    cpu_percent?: number
    can_signal: boolean
    error?: string
  }>
}

export interface LiveSyncStatus {
  is_running: boolean
  status: string
  sync_type?: 'full' | 'single' | null
  session_id?: string | null
  start_time?: string | null
  duration_seconds?: number | null
  list_type?: string | null
  list_id?: string | null
  pid?: number | null
  timestamp: string
  error?: string
}

export interface ProcessedItem {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  status: string
  last_synced: string
  imdb_id?: string
  tmdb_id?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// API Response types
export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

// Toast notification types
export interface ToastNotification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title: string
  message?: string
  duration?: number
}

// UI State types
export interface UIState {
  sidebarCollapsed: boolean
  mobileMenuOpen: boolean
  theme: 'dark' | 'light'
}

// ==========================================
// Sync History Types
// ==========================================

export interface SyncHistoryList {
  type: string
  id: string
  url: string | null
  item_count: number
}

export interface SyncHistoryItem {
  title: string
  status: 'requested' | 'already_available' | 'already_requested' | 'skipped' | 'not_found' | 'error'
  progress_number: number
  progress_total: number
  timestamp: string
  year: number | null
  media_type: 'movie' | 'tv'
  error_details: string | null
}

export interface SyncHistoryResults {
  requested: number
  already_available: number
  already_requested: number
  skipped: number
  not_found: number
  error: number
}

export interface SyncHistoryError {
  title: string
  error: string
  timestamp: string
}

export interface SyncHistorySession {
  id: string
  type: 'full' | 'single'
  start_timestamp: string
  end_timestamp: string | null
  duration: number | null
  version: string | null
  total_items: number
  processed_items: number
  lists: SyncHistoryList[]
  results: SyncHistoryResults
  items: SyncHistoryItem[]
  errors: SyncHistoryError[]
  not_found_items: string[]
  average_time_ms: number | null
  total_time_seconds: number | null
  status: 'completed' | 'in_progress' | 'failed'
}

export interface SyncHistoryResponse {
  sessions: SyncHistorySession[]
  total: number
  limit: number
  offset: number
}

export interface SyncHistoryStats {
  total_sessions: number
  full_syncs: number
  single_syncs: number
  total_items_processed: number
  total_requested: number
  total_errors: number
  success_rate: number
  avg_items_per_sync: number
  avg_duration_seconds: number | null
  recent_stats: {
    last_24h: number
    last_7d: number
    last_30d: number
  }
  most_synced_lists: Array<{
    list: string
    count: number
  }>
}

export interface EnrichedMediaItem {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  year?: number
  poster_url?: string
  rating?: number
  overview?: string
  genres?: string[]
  status: string
  overseerr_url?: string
  imdb_id?: string
  tmdb_id?: number
  list_name?: string
  last_synced?: string
  list_sources?: Array<{
    list_type: string
    list_id: string
    display_name?: string
  }>
}

export interface FailedItem {
  id: string
  title: string
  description: string
  media_type: 'movie' | 'tv'
  year?: number
  failed_at: string
  error_type: 'not_found' | 'error'
  error_message: string
  retryable: boolean
}

// ==========================================
// Collections Types
// ==========================================

export interface CollectionMovie {
  id: number
  title: string
  original_title?: string
  rating?: number
  voteCount?: number
  releaseDate?: string
  poster_path?: string
  backdrop_path?: string
  overview?: string
  tagline?: string
  runtime?: number
  genres?: string[]
  imdb_id?: string
  popularity?: number
  budget?: number
  revenue?: number
  status?: string
  original_language?: string
  production_countries?: string[]
  spoken_languages?: string[]
}

export interface Collection {
  franchise: string
  popularityScore?: number
  averageRating?: number
  totalMovies?: number
  totalVotes?: number
  highestRatedMovie?: {
    id: number
    title: string
    rating: number
  }
  lowestRatedMovie?: {
    id: number
    title: string
    rating: number
  }
  movieRatings?: CollectionMovie[]
  movieIds?: number[]
  collectionId?: number
  poster_path?: string
  backdrop_path?: string
  overview?: string
  poster_url?: string
}

export interface CollectionsResponse {
  collections: Collection[]
  total: number
  page: number
  total_pages: number
  limit: number
}

export interface CollectionMoviesResponse {
  franchise: string
  movies: CollectionMovie[]
  total: number
}

export interface CollectionPosterResponse {
  poster_url: string | null
  movie_id: number
}

export interface CollectionSyncResponse {
  success: boolean
  franchise: string
  items_processed: number
  results: {
    requested: number
    already_requested: number
    request_failed: number
    errors: string[]
  }
}

export interface FailedItemsResponse {
  items: FailedItem[]
  total: number
  pagination: {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export interface CollectionPosterResponse {
  poster_url: string | null
  movie_id: number
}

export interface CollectionSyncResponse {
  success: boolean
  franchise: string
  items_processed: number
  results: {
    requested: number
    already_requested: number
    request_failed: number
    errors: string[]
  }
}

