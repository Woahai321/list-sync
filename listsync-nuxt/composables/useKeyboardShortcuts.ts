/**
 * Keyboard Shortcuts Composable
 * 
 * Provides global keyboard shortcuts for the application
 */

export const useKeyboardShortcuts = () => {
  const router = useRouter()
  const syncStore = useSyncStore()
  const { showInfo } = useToast()
  
  // State for shortcuts help modal
  const showShortcutsHelp = ref(false)
  
  // Define shortcuts
  const shortcuts = [
    {
      key: 'k',
      ctrl: true,
      description: 'Focus search (when available)',
      action: () => {
        // Try to focus search input if it exists
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement
        if (searchInput) {
          searchInput.focus()
          showInfo('Search focused')
        } else {
          showInfo('No search available on this page')
        }
      },
    },
    {
      key: 's',
      ctrl: true,
      description: 'Trigger sync',
      action: async () => {
        if (!syncStore.isSyncing) {
          try {
            await syncStore.triggerSync()
            showInfo('Sync started')
          } catch (error) {
            console.error('Sync failed:', error)
          }
        }
      },
    },
    {
      key: 'n',
      ctrl: true,
      description: 'Add new list',
      action: () => {
        router.push('/lists?action=add')
      },
    },
    {
      key: 'Escape',
      ctrl: false,
      description: 'Close modals/overlays',
      action: () => {
        // This is handled by individual modal components
        // but we can emit an event for consistency
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      },
    },
    {
      key: '?',
      ctrl: false,
      shift: true,
      description: 'Show keyboard shortcuts',
      action: () => {
        showShortcutsHelp.value = !showShortcutsHelp.value
      },
    },
    {
      key: '/',
      ctrl: false,
      description: 'Focus search',
      action: () => {
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement
        if (searchInput) {
          searchInput.focus()
        }
      },
    },
    {
      key: 'd',
      ctrl: false,
      description: 'Go to Dashboard',
      action: () => {
        router.push('/')
      },
    },
    {
      key: 'l',
      ctrl: false,
      description: 'Go to Lists',
      action: () => {
        router.push('/lists')
      },
    },
    {
      key: 'h',
      ctrl: false,
      description: 'Go to History',
      action: () => {
        router.push('/history')
      },
    },
  ]
  
  // Handle keyboard events
  const handleKeyDown = (event: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs (except Escape)
    const target = event.target as HTMLElement
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
    
    if (isInput && event.key !== 'Escape') {
      return
    }
    
    // Find matching shortcut
    const shortcut = shortcuts.find(s => {
      const keyMatches = s.key === event.key
      const ctrlMatches = s.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey
      const shiftMatches = s.shift ? event.shiftKey : !event.shiftKey
      
      return keyMatches && ctrlMatches && (s.shift === undefined || shiftMatches)
    })
    
    if (shortcut) {
      event.preventDefault()
      shortcut.action()
    }
  }
  
  // Setup and cleanup
  const setup = () => {
    if (process.client) {
      window.addEventListener('keydown', handleKeyDown)
    }
  }
  
  const cleanup = () => {
    if (process.client) {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }
  
  // Auto setup/cleanup with lifecycle hooks
  onMounted(setup)
  onUnmounted(cleanup)
  
  return {
    shortcuts,
    showShortcutsHelp,
    setup,
    cleanup,
  }
}

