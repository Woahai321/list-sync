"use client"

import { useState, useEffect } from 'react'
import { formatRelativeTime } from '@/lib/utils'
import { 
  List, 
  Plus, 
  Trash2, 
  ExternalLink,
  Clock,
  Copy,
  X,
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Film,
  Tv,
  Database,
  Star,
  TrendingUp,
  Users,
  Bookmark,
  Calendar,
  ArrowRight,
  Search,
  Filter,
  RefreshCw,
  Check,
  Activity,
  Zap,
  BarChart3
} from 'lucide-react'

interface ListItem {
  id: number
  list_type: string
  list_id: string
  list_url?: string
  url?: string
  display_name: string
  item_count: number
  status?: string
  last_synced?: string
}

// Available sources with purple-themed colors
const AVAILABLE_SOURCES = [
  {
    id: 'imdb',
    name: 'IMDb',
    icon: Film,
    description: 'Internet Movie Database lists',
    examples: ['top', 'moviemeter', 'tvmeter', 'ls123456789', 'ur123456789'],
    hasSpecialLists: true,
    specialLists: [
      { id: 'top', name: 'Top 250 Movies', icon: Star },
      { id: 'boxoffice', name: 'Box Office', icon: TrendingUp },
      { id: 'moviemeter', name: 'MovieMeter', icon: Film },
      { id: 'tvmeter', name: 'TVMeter', icon: Tv }
    ]
  },
  {
    id: 'trakt',
    name: 'Trakt',
    icon: Tv,
    description: 'Trakt.tv lists and collections',
    examples: ['12345678', 'https://trakt.tv/users/username/lists/example-list'],
    hasSpecialLists: true,
    specialLists: [
      // Movies
      { id: 'trending:movies', name: 'Trending Movies', icon: TrendingUp },
      { id: 'popular:movies', name: 'Popular Movies', icon: Star },
      { id: 'anticipated:movies', name: 'Anticipated Movies', icon: Calendar },
      { id: 'watched:movies', name: 'Most Watched Movies', icon: Users },
      { id: 'collected:movies', name: 'Most Collected Movies', icon: Bookmark },
      { id: 'boxoffice:movies', name: 'Box Office Movies', icon: TrendingUp },
      { id: 'streaming:movies', name: 'Streaming Movies', icon: Film },
      { id: 'recommendations:movies', name: 'Recommended Movies', icon: Star },
      { id: 'favorited:movies', name: 'Most Favorited Movies', icon: Star },
      
      // TV Shows
      { id: 'trending:shows', name: 'Trending Shows', icon: TrendingUp },
      { id: 'popular:shows', name: 'Popular Shows', icon: Users },
      { id: 'anticipated:shows', name: 'Anticipated Shows', icon: Calendar },
      { id: 'watched:shows', name: 'Most Watched Shows', icon: Users },
      { id: 'collected:shows', name: 'Most Collected Shows', icon: Bookmark },
      { id: 'streaming:shows', name: 'Streaming Shows', icon: Tv },
      { id: 'recommendations:shows', name: 'Recommended Shows', icon: Star },
      { id: 'favorited:shows', name: 'Most Favorited Shows', icon: Star }
    ]
  },
  {
    id: 'letterboxd',
    name: 'Letterboxd',
    icon: Film,
    description: 'Letterboxd user lists',
    examples: ['https://letterboxd.com/user/list/example-list/', 'https://letterboxd.com/user/list/watchlist/']
  },
  {
    id: 'mdblist',
    name: 'MDBList',
    icon: Database,
    description: 'MDBList collections',
    examples: ['https://mdblist.com/lists/username/listname']
  },
  {
    id: 'stevenlu',
    name: 'StevenLu',
    icon: Star,
    description: 'StevenLu curated lists',
    examples: ['stevenlu']
  }
]

// Source info mapping
const getSourceInfo = (listType: string) => {
  const type = listType.toLowerCase()
  
  if (type.includes('imdb')) {
    return { name: 'IMDb', icon: Film }
  }
  if (type.includes('trakt')) {
    return { name: 'Trakt', icon: Tv }
  }
  if (type.includes('letterboxd')) {
    return { name: 'Letterboxd', icon: Film }
  }
  if (type.includes('mdblist')) {
    return { name: 'MDBList', icon: Database }
  }
  if (type.includes('stevenlu')) {
    return { name: 'StevenLu', icon: Star }
  }
  
  return { name: listType.charAt(0).toUpperCase() + listType.slice(1), icon: List }
}

export default function ListsPage() {
  const [lists, setLists] = useState<ListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedSource, setSelectedSource] = useState('')
  const [listInput, setListInput] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)
  const [copyingUrl, setCopyingUrl] = useState<string | null>(null)
  const [showPresets, setShowPresets] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState('')
  const [syncOption, setSyncOption] = useState<'schedule' | 'sync-single' | 'sync-all'>('schedule')
  const [syncInProgress, setSyncInProgress] = useState(false)
  const [syncProgress, setSyncProgress] = useState<{
    status: string
    processed: number
    total: number
    currentItem?: string
  } | null>(null)
  const [syncCompleted, setSyncCompleted] = useState<{
    type: 'single' | 'full' | 'scheduled'
    message: string
  } | null>(null)

  // State for multiple list configuration
  const [configuredLists, setConfiguredLists] = useState<Array<{
    source: string
    listId: string
    displayName: string
  }>>([])

  // New state for search and filtering
  const [searchTerm, setSearchTerm] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [sortBy, setSortBy] = useState<'name' | 'last_synced' | 'item_count'>('last_synced')
  const [showFilters, setShowFilters] = useState(false)

  // Available sources for filtering
  const FILTER_SOURCES = [
    { id: 'all', name: 'All Sources' },
    { id: 'imdb', name: 'IMDb' },
    { id: 'trakt', name: 'Trakt' },
    { id: 'letterboxd', name: 'Letterboxd' },
    { id: 'mdblist', name: 'MDBList' },
    { id: 'stevenlu', name: 'StevenLu' }
  ]

  // Sort options
  const SORT_OPTIONS = [
    { id: 'last_synced', name: 'Last Synced' },
    { id: 'name', name: 'Name' },
    { id: 'item_count', name: 'Item Count' }
  ]

  // Get source button styling
  const getSourceButtonStyle = (sourceId: string, isSelected: boolean) => {
    const baseStyle = "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 border-2 hover:scale-105"
    
    if (sourceId === 'all') {
      return `${baseStyle} ${isSelected 
        ? 'bg-purple-500/30 border-purple-400/60 text-purple-200 shadow-lg shadow-purple-500/20' 
        : 'bg-purple-500/10 border-purple-500/30 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400/50'}`
    }
    
    return `${baseStyle} ${isSelected 
      ? 'bg-white/20 border-white/40 text-white shadow-lg shadow-white/10' 
      : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10 hover:border-white/30'}`
  }

  // Get sort button styling
  const getSortButtonStyle = (sortId: string, isSelected: boolean) => {
    const baseStyle = "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 border-2 hover:scale-105"
    
    return `${baseStyle} ${isSelected 
      ? 'bg-indigo-500/30 border-indigo-400/60 text-indigo-200 shadow-lg shadow-indigo-500/20' 
      : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20 hover:border-indigo-400/50'}`
  }

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('')
    setSourceFilter('all')
    setSortBy('last_synced')
  }

  // Handle search
  const handleSearch = () => {
    // Search is handled in real-time via filteredAndSortedLists
  }

  // Fetch lists
  const fetchLists = async () => {
    try {
      setError(null)
      const response = await fetch('/api/lists')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setLists(data.lists || [])
    } catch (err) {
      console.error('Error fetching lists:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch lists')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLists()
  }, [])

  // Enhanced filtering and sorting logic
  const filteredAndSortedLists = lists
    .filter(list => {
      const matchesSearch = list.list_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           list.list_type.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesSource = sourceFilter === 'all' || list.list_type.toLowerCase().includes(sourceFilter.toLowerCase())
      return matchesSearch && matchesSource
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.list_id.localeCompare(b.list_id)
        case 'item_count':
          return b.item_count - a.item_count
        case 'last_synced':
        default:
          if (!a.last_synced && !b.last_synced) return 0
          if (!a.last_synced) return 1
          if (!b.last_synced) return -1
          return new Date(b.last_synced).getTime() - new Date(a.last_synced).getTime()
      }
    })

  const validateListInput = (source: string, input: string) => {
    if (!input.trim()) {
      return 'List ID cannot be empty'
    }

    // Basic validation based on source
    if (source === 'imdb') {
      // Allow preset values from the specialLists array
      const imdbPresets = ['top', 'boxoffice', 'moviemeter', 'tvmeter']
      if (!input.match(/^(ls\d+|https?:\/\/(www\.)?imdb\.com\/.+)$/) && !imdbPresets.includes(input)) {
        return 'IMDb list should be a preset value, "ls123456789", or a valid IMDb URL'
      }
    } else if (source === 'letterboxd') {
      if (!input.match(/^([\w-]+\/list\/[\w-]+|https?:\/\/(www\.)?letterboxd\.com\/.+)$/)) {
        return 'Letterboxd list should be "username/list/listname" or a valid Letterboxd URL'
      }
    }

    return null
  }

  const handleAddList = async () => {
    const finalInput = selectedPreset || listInput
    let finalSource = selectedSource
    
    // Determine the final source type
    if (selectedPreset && (selectedSource === 'trakt' || selectedSource === 'imdb')) {
      finalSource = selectedSource === 'trakt' ? 'trakt_special' : selectedSource
    }
    
    if (!finalSource || !finalInput) {
      setValidationError('Please select a source and provide a list ID')
      return
    }

    const validation = validateListInput(finalSource, finalInput)
    if (validation) {
      setValidationError(validation)
      return
    }

    setAdding(true)
    setValidationError(null)

    try {
      // Get all lists to add (current list + any previously configured)
      const currentList = {
        source: finalSource,
        listId: finalInput,
        displayName: `${finalSource}: ${finalInput}`
      }
      const allListsToAdd = [...configuredLists, currentList]

      // Add all lists
      const addPromises = allListsToAdd.map(list => 
        fetch('/api/lists', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            list_type: list.source,
            list_id: list.listId,
          }),
        })
      )

      const responses = await Promise.all(addPromises)
      
      // Check if all requests succeeded
      for (const response of responses) {
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
        }
      }

      console.log(`Successfully added ${allListsToAdd.length} list(s)`)
      
      // Handle sync options
      if (syncOption === 'sync-all') {
        // Trigger immediate sync of all lists
        try {
          const syncResponse = await fetch('/api/sync/trigger', {
            method: 'POST'
          })
          if (syncResponse.ok) {
            closeModal()
            monitorSyncProgress('full')
            return
          } else {
            console.warn('Failed to trigger full sync')
          }
        } catch (syncErr) {
          console.warn('Failed to trigger full sync:', syncErr)
        }
      } else if (syncOption === 'sync-single') {
        // Trigger sync of just these lists (one by one)
        try {
          closeModal()
          await syncMultipleListsSequentially(allListsToAdd)
          return
        } catch (syncErr) {
          console.warn('Failed to trigger batch sync:', syncErr)
        }
      } else if (syncOption === 'schedule') {
        // Show success feedback for scheduled option
        closeModal()
        setSyncCompleted({
          type: 'scheduled',
          message: `${allListsToAdd.length} list${allListsToAdd.length > 1 ? 's' : ''} added and will be synced during the next scheduled sync cycle.`
        })
        setTimeout(() => setSyncCompleted(null), 5000)
        await fetchLists()
        return
      }
      
      // Close modal and refresh (for schedule option or if sync failed)
      closeModal()
      await fetchLists()
      
    } catch (err) {
      console.error('Error adding lists:', err)
      setValidationError(err instanceof Error ? err.message : 'Failed to add lists')
    } finally {
      setAdding(false)
    }
  }

  // Add another list to the batch
  const addAnotherList = () => {
    const finalInput = selectedPreset || listInput
    let finalSource = selectedSource
    
    // Determine the final source type
    if (selectedPreset && (selectedSource === 'trakt' || selectedSource === 'imdb')) {
      finalSource = selectedSource === 'trakt' ? 'trakt_special' : selectedSource
    }
    
    if (!finalSource || !finalInput) {
      setValidationError('Please select a source and provide a list ID')
      return
    }

    const validation = validateListInput(finalSource, finalInput)
    if (validation) {
      setValidationError(validation)
      return
    }

    // Add current list to configured lists
    const newList = {
      source: finalSource,
      listId: finalInput,
      displayName: `${finalSource}: ${finalInput}`
    }
    setConfiguredLists(prev => [...prev, newList])

    // Reset form and go back to step 1
    setCurrentStep(1)
    setSelectedSource('')
    setListInput('')
    setSelectedPreset('')
    setValidationError(null)
    setShowPresets(false)
  }

  // Sync multiple lists sequentially
  const syncMultipleListsSequentially = async (listsToSync: Array<{source: string, listId: string, displayName: string}>) => {
    setSyncInProgress(true)
    setSyncProgress({ 
      status: `Starting sync of ${listsToSync.length} lists...`, 
      processed: 0, 
      total: listsToSync.length 
    })
    setSyncCompleted(null)

    console.log(`Starting sequential sync of ${listsToSync.length} lists:`, listsToSync.map(l => l.displayName))

    try {
      for (let i = 0; i < listsToSync.length; i++) {
        const list = listsToSync[i]
        
        console.log(`Starting sync ${i + 1}/${listsToSync.length}: ${list.displayName}`)
        
        setSyncProgress({ 
          status: `Syncing list ${i + 1} of ${listsToSync.length}...`, 
          processed: i, 
          total: listsToSync.length,
          currentItem: list.displayName
        })

        // Trigger the sync
        const syncResponse = await fetch('/api/sync/single', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            list_type: list.source,
            list_id: list.listId,
          }),
        })

        if (!syncResponse.ok) {
          const errorText = await syncResponse.text()
          console.error(`Failed to start sync for ${list.displayName}:`, errorText)
          throw new Error(`Failed to start sync for ${list.displayName}`)
        }

        console.log(`Sync triggered for ${list.displayName}, waiting for completion...`)

        // Wait for this specific sync to complete
        await waitForSyncCompletion(list.displayName)
        
        console.log(`Sync completed for ${list.displayName}`)

        // Update progress
        setSyncProgress({ 
          status: `Completed ${i + 1} of ${listsToSync.length} lists`, 
          processed: i + 1, 
          total: listsToSync.length,
          currentItem: list.displayName
        })

        // Wait a bit between syncs to avoid overwhelming the system (except for the last one)
        if (i < listsToSync.length - 1) {
          console.log(`Waiting 3 seconds before next sync...`)
          await new Promise(resolve => setTimeout(resolve, 3000))
        }
      }

      console.log(`All ${listsToSync.length} lists synced successfully!`)

      // Mark as completed
      setSyncProgress({ 
        status: 'All lists synced successfully!', 
        processed: listsToSync.length, 
        total: listsToSync.length 
      })
      
      setSyncCompleted({
        type: 'single',
        message: `Successfully synced ${listsToSync.length} list${listsToSync.length > 1 ? 's' : ''}!`
      })
      
      setTimeout(() => {
        setSyncInProgress(false)
        setSyncProgress(null)
        setSyncCompleted(null)
      }, 3000)
      
      await fetchLists()

    } catch (err) {
      console.error('Error syncing multiple lists:', err)
      setSyncInProgress(false)
      setSyncProgress(null)
      setError(err instanceof Error ? err.message : 'Failed to sync lists')
    }
  }

  // Helper function to wait for a specific sync to complete
  const waitForSyncCompletion = async (listDisplayName: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const maxWaitTime = 5 * 60 * 1000 // 5 minutes max wait
      const startTime = Date.now()
      
      const checkCompletion = async () => {
        try {
          // Check if we've exceeded max wait time
          if (Date.now() - startTime > maxWaitTime) {
            console.warn(`Sync timeout for ${listDisplayName} after 5 minutes`)
            resolve() // Don't reject, just continue to next list
            return
          }

          const response = await fetch('/api/sync/status/live')
          if (response.ok) {
            const status = await response.json()
            
            if (status.last_activity) {
              const activity = status.last_activity
              
              // Check for completion indicators
              if (activity.includes('Single list sync completed:') || 
                  activity.includes('errors') || 
                  activity.includes('requested')) {
                console.log(`Detected completion for sync: ${activity}`)
                resolve()
                return
              }
            }
            
            // If sync is not running and we didn't see completion, assume it's done
            if (!status.is_running) {
              console.log(`Sync appears to have stopped for ${listDisplayName}`)
              resolve()
              return
            }
          }
          
          // Continue polling
          setTimeout(checkCompletion, 2000)
        } catch (err) {
          console.error('Error checking sync completion:', err)
          // Don't reject on polling errors, just continue checking
          setTimeout(checkCompletion, 2000)
        }
      }

      // Start checking after a brief delay
      setTimeout(checkCompletion, 1000)
    })
  }

  const handleDeleteList = async (listType: string, listId: string) => {
    if (!confirm(`Are you sure you want to delete the ${listType} list "${listId}"?`)) {
      return
    }

    try {
      const response = await fetch(`/api/lists/${listType}/${encodeURIComponent(listId)}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Refresh the lists
      await fetchLists()
    } catch (err) {
      console.error('Error deleting list:', err)
      setError(err instanceof Error ? err.message : 'Failed to delete list')
    }
  }

  const handleSyncSingle = async (listId: string) => {
    if (syncInProgress) return
    
    try {
      setSyncInProgress(true)
      const list = lists.find(l => l.list_id === listId)
      if (!list) return
      
      const syncResponse = await fetch('/api/sync/single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          list_type: list.list_type,
          list_id: listId,
        }),
      })
      
      if (syncResponse.ok) {
        // Start monitoring sync progress
        monitorSyncProgress('single')
      } else {
        throw new Error('Failed to start sync')
      }
    } catch (err) {
      console.error('Error syncing list:', err)
      setError(err instanceof Error ? err.message : 'Failed to sync list')
      setSyncInProgress(false)
    }
  }

  const handleCopyUrl = async (url: string, listId: string) => {
    try {
      await navigator.clipboard.writeText(url)
      setCopyingUrl(listId)
      setTimeout(() => setCopyingUrl(null), 2000)
    } catch (err) {
      console.error('Failed to copy URL:', err)
    }
  }

  const nextStep = () => {
    if (currentStep === 1 && selectedSource) {
      setCurrentStep(2)
    } else if (currentStep === 2 && (selectedPreset || listInput.trim())) {
      setCurrentStep(3)
    }
  }

  const prevStep = () => {
    if (currentStep === 3) {
      setCurrentStep(2)
    } else if (currentStep === 2) {
      setCurrentStep(1)
      setListInput('')
      setValidationError(null)
      setSelectedPreset('')
      setShowPresets(false)
    }
  }

  const closeModal = () => {
    setShowModal(false)
    setCurrentStep(1)
    setSelectedSource('')
    setListInput('')
    setValidationError(null)
    setSelectedPreset('')
    setShowPresets(false)
    setSyncOption('schedule')
    setConfiguredLists([]) // Reset configured lists
  }

  const handleSourceSelect = (sourceId: string) => {
    setSelectedSource(sourceId)
    setValidationError(null)
    setSelectedPreset('')
    setCurrentStep(2)
  }

  const handlePresetSelect = (presetId: string) => {
    setSelectedPreset(presetId)
    setListInput('')
    setValidationError(null)
    setShowPresets(false) // Auto-close the dropdown after selection
  }

  // Monitor sync progress
  const monitorSyncProgress = async (syncType: 'single' | 'full') => {
    setSyncInProgress(true)
    setSyncProgress({ status: 'Starting sync...', processed: 0, total: 0 })
    setSyncCompleted(null) // Clear any previous completion state

    const pollProgress = async () => {
      try {
        const response = await fetch('/api/sync/status/live')
        if (response.ok) {
          const status = await response.json()
          
          if (status.is_running) {
            // Parse last activity for progress info
            if (status.last_activity) {
              const activity = status.last_activity
              
              // Check for completion indicators in the log
              if ((syncType === 'single' && activity.includes('Single list sync completed:')) ||
                  (syncType === 'full' && activity.includes('List Sync Summary'))) {
                // Sync completed
                setSyncInProgress(false)
                setSyncProgress(null)
                
                // Parse results from completion message
                let message = 'Sync completed successfully!'
                if (syncType === 'single' && activity.includes('Single list sync completed:')) {
                  // Extract "X requested, Y errors" from the completion message
                  const match = activity.match(/(\d+)\s+requested,\s*(\d+)\s+errors?/)
                  if (match) {
                    const requested = parseInt(match[1])
                    const errors = parseInt(match[2])
                    message = `Single list sync completed: ${requested} item${requested !== 1 ? 's' : ''} requested`
                    if (errors > 0) {
                      message += `, ${errors} error${errors !== 1 ? 's' : ''}`
                    }
                  }
                } else if (syncType === 'full') {
                  message = 'Full sync of all lists completed successfully!'
                }
                
                setSyncCompleted({
                  type: syncType,
                  message
                })
                
                // Auto-hide completion message after 8 seconds
                setTimeout(() => setSyncCompleted(null), 8000)
                
                // Refresh the lists
                await fetchLists()
                return
              }
              
              // Parse progress from normal processing
              if (activity.includes('(') && activity.includes('/') && activity.includes(')')) {
                // Extract progress from strings like "Item Name (5/20)"
                const match = activity.match(/\((\d+)\/(\d+)\)/)
                if (match) {
                  const processed = parseInt(match[1])
                  const total = parseInt(match[2])
                  const itemMatch = activity.match(/^[^:]+:\s*(.+?)\s*\(\d+\/\d+\)/)
                  const currentItem = itemMatch ? itemMatch[1] : undefined
                  
                  setSyncProgress({
                    status: 'Processing items...',
                    processed,
                    total,
                    currentItem
                  })
                }
              } else {
                setSyncProgress({
                  status: activity || 'Sync in progress...',
                  processed: 0,
                  total: 0
                })
              }
            }
            
            // Continue polling
            setTimeout(pollProgress, 2000)
          } else {
            // Sync stopped but we didn't catch the completion message
            // This shouldn't happen with the new completion detection, but just in case
            setSyncInProgress(false)
            setSyncProgress(null)
            setSyncCompleted({
              type: syncType,
              message: 'Sync completed'
            })
            setTimeout(() => setSyncCompleted(null), 5000)
            await fetchLists()
          }
        }
      } catch (err) {
        console.error('Error monitoring sync progress:', err)
        // Continue polling despite errors
        setTimeout(pollProgress, 2000)
      }
    }

    // Start polling
    setTimeout(pollProgress, 1000)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-white/10 rounded-lg w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-white/10 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Enhanced Header Section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
            Media Lists
          </h1>
          <p className="text-white/60 text-lg">
            Manage your synchronized media lists from various sources
          </p>
          {lists.length > 0 && (
            <div className="flex items-center gap-4 text-sm text-white/50">
              <div className="flex items-center gap-1">
                <BarChart3 className="h-4 w-4" />
                <span>{lists.length} total lists</span>
              </div>
              <div className="flex items-center gap-1">
                <Activity className="h-4 w-4" />
                <span>{lists.reduce((sum, list) => sum + list.item_count, 0)} total items</span>
              </div>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchLists()}
            disabled={loading}
            className="glass-button flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-white/10 transition-all duration-200"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          <button
            onClick={() => setShowModal(true)}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-6 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-purple-500/25"
          >
            <Plus className="h-4 w-4" />
            Add List
          </button>
        </div>
      </div>

      {/* Enhanced Search and Filter Controls */}
      {lists.length > 0 && (
        <div className="space-y-4">
          {/* Search */}
          <div className="glass-card p-4">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/50" />
                <input
                  type="text"
                  placeholder="Search lists by name or source..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                    showFilters 
                      ? 'bg-purple-600/30 border border-purple-500/50 text-purple-300' 
                      : 'bg-purple-600/20 border border-purple-500/30 text-purple-300 hover:bg-purple-600/30'
                  }`}
                >
                  <Filter className="h-4 w-4" />
                  Filters
                  {(sourceFilter !== 'all' || sortBy !== 'last_synced') && (
                    <span className="bg-purple-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                      {(sourceFilter !== 'all' ? 1 : 0) + (sortBy !== 'last_synced' ? 1 : 0)}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="glass-card p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white titillium-web-semibold">Filter Options</h3>
                {(sourceFilter !== 'all' || sortBy !== 'last_synced') && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 hover:bg-red-500/30 transition-colors font-medium"
                  >
                    <X className="h-4 w-4" />
                    Clear All Filters
                  </button>
                )}
              </div>
              
              <div className="space-y-8">
                {/* Source Filter */}
                <div>
                  <h4 className="text-lg font-medium text-white/90 mb-4 flex items-center gap-2">
                    <Database className="h-5 w-5 text-purple-400" />
                    Source
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {FILTER_SOURCES.map((source) => (
                      <button
                        key={source.id}
                        onClick={() => setSourceFilter(source.id)}
                        className={getSourceButtonStyle(source.id, sourceFilter === source.id)}
                      >
                        <span className="text-sm font-medium">{source.name}</span>
                        {sourceFilter === source.id && (
                          <div className="w-2 h-2 bg-current rounded-full ml-1"></div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sort Options */}
                <div>
                  <h4 className="text-lg font-medium text-white/90 mb-4 flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-purple-400" />
                    Sort By
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {SORT_OPTIONS.map((option) => (
                      <button
                        key={option.id}
                        onClick={() => setSortBy(option.id as 'name' | 'last_synced' | 'item_count')}
                        className={getSortButtonStyle(option.id, sortBy === option.id)}
                      >
                        <span className="text-sm font-medium">{option.name}</span>
                        {sortBy === option.id && (
                          <div className="w-2 h-2 bg-current rounded-full ml-1"></div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Active Filters Display */}
          {(searchTerm || sourceFilter !== 'all' || sortBy !== 'last_synced') && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-white/60">Active filters:</span>
              {searchTerm && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-xs text-purple-300">
                  Search: "{searchTerm}"
                  <button
                    onClick={() => setSearchTerm('')}
                    className="hover:bg-white/10 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
              {sourceFilter !== 'all' && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 border border-white/20 rounded-full text-xs text-white/70">
                  Source: {FILTER_SOURCES.find(s => s.id === sourceFilter)?.name}
                  <button
                    onClick={() => setSourceFilter('all')}
                    className="hover:bg-white/10 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
              {sortBy !== 'last_synced' && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300">
                  Sort: {SORT_OPTIONS.find(s => s.id === sortBy)?.name}
                  <button
                    onClick={() => setSortBy('last_synced')}
                    className="hover:bg-white/10 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
            </div>
          )}

          {/* Filter Results Summary */}
          {(searchTerm || sourceFilter !== 'all') && (
            <div className="glass-card p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">
                  Showing {filteredAndSortedLists.length} of {lists.length} lists
                  {searchTerm && (
                    <span className="ml-2 text-purple-300">
                      matching &quot;{searchTerm}&quot;
                    </span>
                  )}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="glass-card p-12">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-purple-400" />
            <span className="ml-3 text-lg text-white/60">Loading your lists...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="glass-card p-6 border-red-500/20 bg-red-500/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex-shrink-0 w-4 h-4 bg-red-500 rounded-full mr-3"></div>
              <div>
                <h3 className="text-lg font-medium text-red-400">Error Loading Lists</h3>
                <p className="text-white/60 mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={fetchLists}
              className="glass-button px-4 py-2 text-sm hover:bg-red-500/10 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Lists Content */}
      {!loading && !error && (
        <>
          {filteredAndSortedLists.length === 0 ? (
            <div className="glass-card p-12">
              <div className="text-center max-w-md mx-auto">
                {lists.length === 0 ? (
                  /* Empty state when no lists exist */
                  <>
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                      <List className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-3">No Lists Yet</h3>
                    <p className="text-white/60 mb-8 leading-relaxed">
                      Get started by adding your first media list from IMDb, Trakt, Letterboxd, or other supported sources.
                    </p>
                    <button
                      onClick={() => setShowModal(true)}
                      className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-8 py-3 rounded-lg font-medium transition-all duration-200 inline-flex items-center gap-2 shadow-lg hover:shadow-purple-500/25"
                    >
                      <Plus className="h-5 w-5" />
                      Add Your First List
                    </button>
                  </>
                ) : (
                  /* No results after filtering */
                  <>
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Search className="h-8 w-8 text-purple-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-3">No Results Found</h3>
                    <p className="text-white/60 mb-6 leading-relaxed">
                      No lists match your current search criteria. Try adjusting your filters or search terms.
                    </p>
                    <button
                      onClick={() => {
                        setSearchTerm('')
                        setSourceFilter('all')
                      }}
                      className="glass-button px-6 py-2.5 hover:bg-white/10 transition-colors inline-flex items-center gap-2"
                    >
                      <X className="h-4 w-4" />
                      Clear Filters
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAndSortedLists.map((list) => {
                const sourceInfo = getSourceInfo(list.list_type)
                const IconComponent = sourceInfo.icon
                const isRecentlySync = list.last_synced && 
                  new Date(list.last_synced).getTime() > Date.now() - (24 * 60 * 60 * 1000) // 24 hours
                
                return (
                  <div key={list.id} className="glass-card p-6 hover:bg-white/5 transition-all duration-300 group border border-white/10 hover:border-purple-500/30">
                    {/* Card Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-purple-500/20 to-purple-600/30 rounded-lg flex items-center justify-center border border-purple-500/20">
                          <IconComponent className="h-5 w-5 text-purple-300" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-lg font-semibold text-white truncate group-hover:text-purple-200 transition-colors">
                              {list.list_id}
                            </h3>
                            {isRecentlySync && (
                              <div className="flex-shrink-0 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-purple-300 font-medium">
                              {sourceInfo.name}
                            </span>
                            {list.status && (
                              <span className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                                {list.status}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Stats Section */}
                    <div className="space-y-3 mb-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <BarChart3 className="h-4 w-4 text-white/40" />
                          <span className="text-sm text-white/60">Items</span>
                        </div>
                        <span className="text-lg font-semibold text-white">
                          {list.item_count.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4 text-white/40" />
                          <span className="text-sm text-white/60">Last Sync</span>
                        </div>
                        <span className={`text-sm font-medium ${
                          isRecentlySync ? 'text-green-400' : 'text-white/70'
                        }`}>
                          {list.last_synced ? formatRelativeTime(list.last_synced) : 'Never'}
                        </span>
                      </div>

                      {/* Activity Indicator */}
                      <div className="pt-3 border-t border-white/10">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Activity className="h-4 w-4 text-white/40" />
                            <span className="text-sm text-white/60">Status</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {isRecentlySync ? (
                              <>
                                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                <span className="text-sm text-green-400 font-medium">Active</span>
                              </>
                            ) : (
                              <>
                                <div className="w-2 h-2 bg-white/30 rounded-full"></div>
                                <span className="text-sm text-white/50 font-medium">Inactive</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Actions Section */}
                    <div className="space-y-3">
                      {/* Primary Actions */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSyncSingle(list.list_id)}
                          disabled={syncInProgress}
                          className="flex-1 bg-gradient-to-r from-purple-600/80 to-purple-700/80 hover:from-purple-600 hover:to-purple-700 disabled:from-purple-600/50 disabled:to-purple-700/50 text-white px-4 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 disabled:cursor-not-allowed group"
                        >
                          <Zap className="h-4 w-4 group-hover:scale-110 transition-transform" />
                          <span className="text-sm">Sync</span>
                        </button>
                        
                        <button
                          onClick={() => handleDeleteList(list.list_type, list.list_id)}
                          className="px-4 py-2.5 bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-500/30 text-white/70 hover:text-red-300 rounded-lg transition-all duration-200 flex items-center justify-center group"
                        >
                          <Trash2 className="h-4 w-4 group-hover:scale-110 transition-transform" />
                        </button>
                      </div>

                      {/* Secondary Actions */}
                      <div className="flex gap-2 text-sm">
                        {(list.list_url || list.url) && (
                          <a
                            href={list.list_url || list.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/30 text-white/70 hover:text-purple-300 rounded-lg transition-all duration-200 group"
                          >
                            <ExternalLink className="h-3.5 w-3.5 group-hover:scale-110 transition-transform" />
                            <span>View List</span>
                          </a>
                        )}
                        
                        <button
                          onClick={() => handleCopyUrl(list.list_id, list.list_id)}
                          className="flex items-center justify-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/30 text-white/70 hover:text-purple-300 rounded-lg transition-all duration-200 group"
                        >
                          {copyingUrl === list.list_id ? (
                            <Check className="h-3.5 w-3.5 text-green-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5 group-hover:scale-110 transition-transform" />
                          )}
                          <span className="hidden sm:inline">
                            {copyingUrl === list.list_id ? 'Copied!' : 'Copy ID'}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* Sync Progress Display */}
      {syncInProgress && syncProgress && (
        <div className="glass-card p-6 border-purple-400/30 bg-purple-500/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Sync in Progress
            </h3>
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-purple-400 border-t-transparent"></div>
              <span className="text-purple-200 text-sm">Processing...</span>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-purple-200">{syncProgress.status}</span>
                {syncProgress.total > 0 && (
                  <span className="text-purple-200">
                    {syncProgress.processed} / {syncProgress.total}
                  </span>
                )}
              </div>
              
              {syncProgress.total > 0 && (
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(syncProgress.processed / syncProgress.total) * 100}%` }}
                  ></div>
                </div>
              )}
            </div>
            
            {syncProgress.currentItem && (
              <div className="text-sm text-purple-200/80">
                Currently processing: <span className="text-white">{syncProgress.currentItem}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sync Completion Display */}
      {syncCompleted && (
        <div className="glass-card p-6 border-green-400/30 bg-green-500/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <Check className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  {syncCompleted.type === 'scheduled' ? 'List Added Successfully' : 'Sync Complete'}
                </h3>
                <p className="text-green-200 text-sm">{syncCompleted.message}</p>
              </div>
            </div>
            <button
              onClick={() => setSyncCompleted(null)}
              className="glass-button p-2 rounded-lg transition-all duration-200"
            >
              <X className="w-4 h-4 text-green-400" />
            </button>
          </div>
        </div>
      )}

      {/* Add List Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-card w-full max-w-2xl max-h-[90vh] flex flex-col">
            {/* Modal Header - Fixed */}
            <div className="flex items-center justify-between p-6 border-b border-purple-500/20 flex-shrink-0">
              <div>
                <h2 className="text-xl font-bold text-white titillium-web-bold">
                  {configuredLists.length > 0 ? `Add Lists (${configuredLists.length + 1})` : 'Add New List'}
                </h2>
                <p className="text-purple-200/60 text-sm mt-1 titillium-web-light">
                  Step {currentStep} of 3: {currentStep === 1 ? 'Choose source' : currentStep === 2 ? 'Enter list details' : 'Choose sync options'}
                  {configuredLists.length > 0 && currentStep === 1 && (
                    <span className="ml-2 text-purple-300">• {configuredLists.length} list{configuredLists.length > 1 ? 's' : ''} configured</span>
                  )}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="glass-button p-2 rounded-lg transition-all duration-200"
              >
                <X className="w-5 h-5 text-purple-400" />
              </button>
            </div>

            {/* Modal Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-purple-500/50 hover:scrollbar-thumb-purple-400/70">
              {currentStep === 1 ? (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 titillium-web-semibold">Select List Source</h3>
                  
                  {/* Show configured lists if any */}
                  {configuredLists.length > 0 && (
                    <div className="glass-card p-4 bg-green-500/10 border border-green-500/20 mb-6">
                      <h4 className="text-sm font-medium text-green-300 mb-2 titillium-web-semibold">
                        ✓ {configuredLists.length} List{configuredLists.length > 1 ? 's' : ''} Configured
                      </h4>
                      <div className="space-y-1">
                        {configuredLists.map((list, index) => (
                          <div key={index} className="text-sm text-green-200 titillium-web-regular">
                            • <span className="text-green-300">{list.source}</span>: {list.listId}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="space-y-6">
                    {/* Main 2x2 grid for primary sources */}
                    <div className="grid grid-cols-2 gap-3">
                      {AVAILABLE_SOURCES.slice(0, 4).map((source) => {
                        const IconComponent = source.icon
                        return (
                          <button
                            key={source.id}
                            onClick={() => handleSourceSelect(source.id)}
                            className={`glass-card-hover p-4 text-left transition-all duration-200 ${
                              selectedSource === source.id ? 'ring-2 ring-purple-400' : ''
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <IconComponent className="w-5 h-5 text-purple-400 mt-0.5" />
                              <div>
                                <div className="font-medium text-white titillium-web-semibold">{source.name}</div>
                                <div className="text-sm text-purple-200/60 titillium-web-light">{source.description}</div>
                              </div>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                    
                    {/* StevenLu centered at the bottom */}
                    {AVAILABLE_SOURCES.slice(4).map((source) => {
                      const IconComponent = source.icon
                      return (
                        <div key={source.id} className="flex justify-center">
                          <button
                            onClick={() => handleSourceSelect(source.id)}
                            className={`glass-card-hover p-4 text-left transition-all duration-200 w-80 ${
                              selectedSource === source.id ? 'ring-2 ring-purple-400' : ''
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <IconComponent className="w-5 h-5 text-purple-400 mt-0.5" />
                              <div>
                                <div className="font-medium text-white titillium-web-semibold">{source.name}</div>
                                <div className="text-sm text-purple-200/60 titillium-web-light">{source.description}</div>
                              </div>
                            </div>
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ) : currentStep === 2 ? (
                <div>
                  <div className="flex items-center space-x-2 mb-4">
                    <button
                      onClick={prevStep}
                      className="glass-button p-2 rounded-lg transition-all duration-200"
                    >
                      <ArrowLeft className="w-4 h-4 text-purple-400" />
                    </button>
                    <h3 className="text-lg font-semibold text-white titillium-web-semibold">
                      Enter List Details
                    </h3>
                  </div>

                  {/* Presets Section */}
                  {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.hasSpecialLists && (
                    <div className="mb-6">
                      <button
                        onClick={() => setShowPresets(!showPresets)}
                        className="flex items-center space-x-2 w-full glass-card-hover p-4 rounded-lg transition-all duration-200"
                      >
                        {showPresets ? (
                          <ChevronDown className="w-4 h-4 text-purple-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-purple-400" />
                        )}
                        <span className="text-white titillium-web-semibold">Quick Presets</span>
                        <span className="text-purple-200/60 text-sm titillium-web-light ml-auto">
                          Popular {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.name} lists
                        </span>
                      </button>

                      {showPresets && (
                        <div className="mt-3 space-y-4">
                          {selectedSource === 'trakt' ? (
                            // Special layout for Trakt with grouped categories
                            <div className="space-y-4">
                              <div>
                                <h4 className="text-sm font-medium text-purple-200 mb-2 titillium-web-semibold">Movies</h4>
                                <div className="grid grid-cols-2 gap-2">
                                  {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.specialLists?.filter(preset => preset.id.includes(':movies')).map((preset) => {
                                    const PresetIcon = preset.icon
                                    return (
                                      <button
                                        key={preset.id}
                                        onClick={() => handlePresetSelect(preset.id)}
                                        className={`glass-card-hover p-3 text-left transition-all duration-200 ${
                                          selectedPreset === preset.id ? 'ring-2 ring-purple-400' : ''
                                        }`}
                                      >
                                        <div className="flex items-center space-x-2">
                                          <PresetIcon className="w-4 h-4 text-purple-400" />
                                          <span className="text-xs text-purple-200 titillium-web-regular">{preset.name}</span>
                                        </div>
                                      </button>
                                    )
                                  })}
                                </div>
                              </div>
                              
                              <div>
                                <h4 className="text-sm font-medium text-purple-200 mb-2 titillium-web-semibold">TV Shows</h4>
                                <div className="grid grid-cols-2 gap-2">
                                  {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.specialLists?.filter(preset => preset.id.includes(':shows')).map((preset) => {
                                    const PresetIcon = preset.icon
                                    return (
                                      <button
                                        key={preset.id}
                                        onClick={() => handlePresetSelect(preset.id)}
                                        className={`glass-card-hover p-3 text-left transition-all duration-200 ${
                                          selectedPreset === preset.id ? 'ring-2 ring-purple-400' : ''
                                        }`}
                                      >
                                        <div className="flex items-center space-x-2">
                                          <PresetIcon className="w-4 h-4 text-purple-400" />
                                          <span className="text-xs text-purple-200 titillium-web-regular">{preset.name}</span>
                                        </div>
                                      </button>
                                    )
                                  })}
                                </div>
                              </div>
                            </div>
                          ) : (
                            // Standard grid layout for other sources
                            <div className="grid grid-cols-2 gap-3">
                              {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.specialLists?.map((preset) => {
                                const PresetIcon = preset.icon
                                return (
                                  <button
                                    key={preset.id}
                                    onClick={() => handlePresetSelect(preset.id)}
                                    className={`glass-card-hover p-3 text-left transition-all duration-200 ${
                                      selectedPreset === preset.id ? 'ring-2 ring-purple-400' : ''
                                    }`}
                                  >
                                    <div className="flex items-center space-x-2">
                                      <PresetIcon className="w-4 h-4 text-purple-400" />
                                      <span className="text-sm text-purple-200 titillium-web-regular">{preset.name}</span>
                                    </div>
                                  </button>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Manual Input */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-purple-200 mb-2 titillium-web-semibold">
                        {selectedPreset ? 'Selected Preset' : 'List ID or URL'}
                      </label>
                      {selectedPreset ? (
                        <div className="glass-card p-3 bg-purple-500/10">
                          <div className="text-white titillium-web-regular">{selectedPreset}</div>
                        </div>
                      ) : (
                        <input
                          type="text"
                          value={listInput}
                          onChange={(e) => {
                            setListInput(e.target.value)
                            setValidationError(null)
                          }}
                          className="w-full px-4 py-3 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white placeholder-purple-200/40 focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all titillium-web-regular"
                          placeholder="Enter list ID or URL..."
                        />
                      )}
                      
                      {selectedPreset && (
                        <button
                          onClick={() => {
                            setSelectedPreset('')
                            setShowPresets(false)
                          }}
                          className="mt-2 text-sm text-purple-400 hover:text-purple-300 transition-colors titillium-web-light"
                        >
                          Use custom ID instead
                        </button>
                      )}
                    </div>

                    {!selectedPreset && AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.examples && (
                      <div className="text-sm text-purple-200/60 titillium-web-light">
                        <div className="font-medium mb-1 titillium-web-semibold">Examples:</div>
                        <div className="space-y-1">
                          {AVAILABLE_SOURCES.find(s => s.id === selectedSource)?.examples.map((example, idx) => (
                            <div key={idx} className="font-mono text-purple-300/80">• {example}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {validationError && (
                    <div className="mt-4 glass-card p-3 border-red-500/30 bg-red-500/10">
                      <p className="text-red-400 text-sm titillium-web-regular">{validationError}</p>
                    </div>
                  )}

                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      onClick={closeModal}
                      className="glass-button px-4 py-2 rounded-lg transition-all duration-200 titillium-web-regular"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={nextStep}
                      disabled={!selectedPreset && !listInput.trim()}
                      className="glass-button-primary px-6 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed titillium-web-semibold"
                    >
                      <span>Next</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ) : (
                // Step 3: Sync Options
                <div>
                  <div className="flex items-center space-x-2 mb-4">
                    <button
                      onClick={prevStep}
                      className="glass-button p-2 rounded-lg transition-all duration-200"
                    >
                      <ArrowLeft className="w-4 h-4 text-purple-400" />
                    </button>
                    <h3 className="text-lg font-semibold text-white titillium-web-semibold">
                      Choose Sync Options
                    </h3>
                  </div>

                  {/* List Summary */}
                  <div className="glass-card p-4 bg-purple-500/10 mb-6">
                    <h4 className="text-sm font-medium text-purple-200 mb-3 titillium-web-semibold">
                      {configuredLists.length > 0 ? `Lists to Add (${configuredLists.length + 1}):` : 'List to Add:'}
                    </h4>
                    <div className="space-y-2">
                      {/* Previously configured lists */}
                      {configuredLists.map((list, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                          <div className="text-white titillium-web-regular">
                            <span className="text-purple-300">{list.source}</span> • {list.listId}
                          </div>
                          <button
                            onClick={() => setConfiguredLists(prev => prev.filter((_, i) => i !== index))}
                            className="text-red-400 hover:text-red-300 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                      
                      {/* Current list */}
                      <div className="flex items-center p-2 bg-purple-500/20 rounded-lg border border-purple-400/30">
                        <div className="text-white titillium-web-regular">
                          <span className="text-purple-300">{selectedSource}</span> • {selectedPreset || listInput}
                        </div>
                        <span className="ml-2 text-xs text-purple-300 px-2 py-0.5 bg-purple-500/30 rounded-full">
                          Current
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Sync Options */}
                  <div className="space-y-3 mb-6">
                    <h4 className="text-sm font-medium text-purple-200 titillium-web-semibold">What would you like to do?</h4>
                    
                    <div className="space-y-3">
                      <label className="flex items-start space-x-3 glass-card-hover p-4 rounded-lg cursor-pointer transition-all duration-200">
                        <input
                          type="radio"
                          name="syncOption"
                          value="schedule"
                          checked={syncOption === 'schedule'}
                          onChange={(e) => setSyncOption(e.target.value as any)}
                          className="mt-1 text-purple-500 focus:ring-purple-400"
                        />
                        <div>
                          <div className="text-white font-medium titillium-web-semibold">Add to Schedule</div>
                          <div className="text-purple-200/60 text-sm titillium-web-light">
                            Add {configuredLists.length > 0 ? 'these lists' : 'the list'} and they will be synced during the next scheduled sync cycle.
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start space-x-3 glass-card-hover p-4 rounded-lg cursor-pointer transition-all duration-200">
                        <input
                          type="radio"
                          name="syncOption"
                          value="sync-single"
                          checked={syncOption === 'sync-single'}
                          onChange={(e) => setSyncOption(e.target.value as any)}
                          className="mt-1 text-purple-500 focus:ring-purple-400"
                        />
                        <div>
                          <div className="text-white font-medium titillium-web-semibold">
                            Sync {configuredLists.length > 0 ? 'These Lists' : 'Just This List'} Now
                          </div>
                          <div className="text-purple-200/60 text-sm titillium-web-light">
                            Add {configuredLists.length > 0 ? 'the lists' : 'the list'} and immediately sync {configuredLists.length > 0 ? 'them one by one' : 'only this new list'}. Quick and targeted.
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start space-x-3 glass-card-hover p-4 rounded-lg cursor-pointer transition-all duration-200">
                        <input
                          type="radio"
                          name="syncOption"
                          value="sync-all"
                          checked={syncOption === 'sync-all'}
                          onChange={(e) => setSyncOption(e.target.value as any)}
                          className="mt-1 text-purple-500 focus:ring-purple-400"
                        />
                        <div>
                          <div className="text-white font-medium titillium-web-semibold">Sync All Lists Now (Including New)</div>
                          <div className="text-purple-200/60 text-sm titillium-web-light">
                            Add {configuredLists.length > 0 ? 'the lists' : 'the list'} and trigger a full sync of all your lists. This may take several minutes.
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="flex justify-between mt-6">
                    <button
                      onClick={closeModal}
                      className="glass-button px-4 py-2 rounded-lg transition-all duration-200 titillium-web-regular"
                    >
                      Cancel
                    </button>
                    
                    <div className="flex space-x-3">
                      <button
                        onClick={addAnotherList}
                        disabled={adding}
                        className="glass-button px-4 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed titillium-web-regular border border-purple-500/30 hover:border-purple-400/50"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Add Another List</span>
                      </button>
                      
                      <button
                        onClick={handleAddList}
                        disabled={adding}
                        className="glass-button-primary px-6 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed titillium-web-semibold"
                      >
                        {adding && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                        <span>
                          {adding 
                            ? 'Adding...' 
                            : syncOption === 'sync-single' 
                              ? configuredLists.length > 0 
                                ? `Add & Sync ${configuredLists.length + 1} Lists`
                                : 'Add & Sync This List'
                              : syncOption === 'sync-all'
                                ? 'Add & Sync All Lists'
                                : configuredLists.length > 0
                                  ? `Add ${configuredLists.length + 1} Lists to Schedule`
                                  : 'Add to Schedule'
                          }
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 