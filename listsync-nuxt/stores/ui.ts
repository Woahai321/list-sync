/**
 * UI Store - Manages UI state (sidebar, theme, etc.)
 */

import { defineStore } from 'pinia'

const STORAGE_KEY = 'listsync-ui-state'

// Helper to load state from localStorage
function loadPersistedState() {
  if (process.client) {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : {}
    } catch (error) {
      console.error('Error loading persisted UI state:', error)
      return {}
    }
  }
  return {}
}

// Helper to save state to localStorage
function saveState(state: any) {
  if (process.client) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch (error) {
      console.error('Error saving UI state:', error)
    }
  }
}

export const useUIStore = defineStore('ui', {
  state: () => {
    const persisted = loadPersistedState()
    
    return {
      sidebarCollapsed: persisted.sidebarCollapsed ?? false,
      mobileMenuOpen: false, // Don't persist mobile menu state
      theme: persisted.theme ?? 'dark',
    }
  },

  getters: {
    /**
     * Check if sidebar is visible
     */
    isSidebarVisible: (state) => !state.sidebarCollapsed,

    /**
     * Check if mobile menu is visible
     */
    isMobileMenuVisible: (state) => state.mobileMenuOpen,

    /**
     * Check if dark mode is enabled
     */
    isDarkMode: (state) => state.theme === 'dark',
  },

  actions: {
    /**
     * Toggle sidebar collapsed state
     */
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      this.persist()
    },

    /**
     * Set sidebar collapsed state
     */
    setSidebarCollapsed(collapsed: boolean) {
      this.sidebarCollapsed = collapsed
      this.persist()
    },

    /**
     * Toggle mobile menu
     */
    toggleMobileMenu() {
      this.mobileMenuOpen = !this.mobileMenuOpen
    },

    /**
     * Set mobile menu state
     */
    setMobileMenuOpen(open: boolean) {
      this.mobileMenuOpen = open
    },

    /**
     * Close mobile menu
     */
    closeMobileMenu() {
      this.mobileMenuOpen = false
    },

    /**
     * Toggle theme (dark/light)
     */
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      this.applyTheme()
      this.persist()
    },

    /**
     * Set theme
     */
    setTheme(theme: 'dark' | 'light') {
      this.theme = theme
      this.applyTheme()
      this.persist()
    },

    /**
     * Apply theme to document
     */
    applyTheme() {
      if (process.client) {
        if (this.theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      }
    },

    /**
     * Initialize theme on app start
     */
    initTheme() {
      // Check for system preference if no saved theme
      if (process.client && !loadPersistedState().theme) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        this.theme = prefersDark ? 'dark' : 'light'
      }
      
      this.applyTheme()
    },

    /**
     * Persist state to localStorage
     */
    persist() {
      saveState({
        sidebarCollapsed: this.sidebarCollapsed,
        theme: this.theme,
      })
    },

    /**
     * Reset store state
     */
    reset() {
      this.sidebarCollapsed = false
      this.mobileMenuOpen = false
      this.theme = 'dark'
      this.persist()
      this.applyTheme()
    },
  },
})

