// Core analytics data types
export interface AnalyticsOverview {
  total_items: number
  success_rate: number
  avg_processing_time: number
  active_sync: boolean
  total_sync_operations: number
  total_errors: number
  last_sync_time: string
}

// Media addition analytics
export interface MediaAdditionData {
  timestamp: string
  count: number
  type: 'movie' | 'tv'
  source: string
}

// List fetch analytics
export interface ListFetchData {
  timestamp: string
  success_rate: number
  total_attempts: number
  successful_fetches: number
  failed_fetches: number
  source: string
}

// Matching accuracy analytics
export interface MatchingData {
  perfect_matches: number
  partial_matches: number
  failed_matches: number
  average_score: number
  low_confidence_matches: LowConfidenceMatch[]
}

export interface LowConfidenceMatch {
  title: string
  year?: number
  score: number
  original_title?: string
  source: string
  timestamp: string
  needs_review: boolean
}

// Search failure analytics
export interface SearchFailureData {
  title: string
  search_count: number
  last_attempt: string
  sources: string[]
  type: 'movie' | 'tv'
}

// Scraping performance analytics
export interface ScrapingPerformanceData {
  timestamp: string
  items_per_minute: number
  source: string
  total_items: number
  processing_time: number
}

// Source distribution analytics
export interface SourceDistributionData {
  source: string
  items_found: number
  average_items_per_page: number
  total_pages: number
  success_rate: number
}

// Selector performance analytics
export interface SelectorPerformanceData {
  website: string
  selector: string
  success_rate: number
  total_attempts: number
  last_used: string
  status: 'working' | 'failing' | 'deprecated'
}

// Genre and year distribution
export interface GenreDistributionData {
  genre: string
  count: number
  percentage: number
}

export interface YearDistributionData {
  year: number
  count: number
  type: 'movie' | 'tv'
}

// Time-based analytics
export interface TimeSeriesData {
  timestamp: string
  value: number
  label?: string
}

// API response types
export interface AnalyticsResponse {
  overview: AnalyticsOverview
  media_additions: MediaAdditionData[]
  list_fetches: ListFetchData[]
  matching: MatchingData
  search_failures: SearchFailureData[]
  scraping_performance: ScrapingPerformanceData[]
  source_distribution: SourceDistributionData[]
  selector_performance: SelectorPerformanceData[]
  genre_distribution: GenreDistributionData[]
  year_distribution: YearDistributionData[]
}

// Chart data types
export interface ChartDataPoint {
  label: string
  value: number
  color?: string
  metadata?: any
}

export interface LineChartData {
  label: string
  data: TimeSeriesData[]
  color: string
}

// Filter and query types
export interface AnalyticsFilters {
  timeRange: '1h' | '24h' | '7d' | '30d' | 'custom'
  category?: 'all' | 'sync' | 'fetching' | 'matching' | 'scraping'
  source?: string
  mediaType?: 'all' | 'movie' | 'tv'
  startDate?: string
  endDate?: string
}

// Alert and notification types
export interface AnalyticsAlert {
  id: string
  type: 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  source?: string
  count?: number
  resolved: boolean
}

// Performance metrics
export interface PerformanceMetrics {
  avgResponseTime: number
  throughput: number
  errorRate: number
  uptime: number
  memoryUsage?: number
  cpuUsage?: number
} 