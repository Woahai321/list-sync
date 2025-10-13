/**
 * Theme Management Composable
 * Handles theme switching, accent colors, and font sizes with persistence
 */

interface ThemeConfig {
  mode: 'dark' | 'light'
  accentColor: 'purple' | 'blue' | 'green' | 'red'
  fontSize: 'small' | 'medium' | 'large'
}

const THEME_STORAGE_KEY = 'listsync-theme'

// Default theme
const defaultTheme: ThemeConfig = {
  mode: 'dark',
  accentColor: 'purple',
  fontSize: 'medium',
}

// Reactive theme state
const currentTheme = ref<ThemeConfig>({ ...defaultTheme })

// Accent color mappings for Tailwind classes
const accentColorMap = {
  purple: {
    primary: 'purple',
    primaryHex: '#9d34da',
    classes: {
      bg: 'bg-purple-500',
      text: 'text-purple-500',
      border: 'border-purple-500',
      hover: 'hover:bg-purple-600',
    }
  },
  blue: {
    primary: 'blue',
    primaryHex: '#3b82f6',
    classes: {
      bg: 'bg-blue-500',
      text: 'text-blue-500',
      border: 'border-blue-500',
      hover: 'hover:bg-blue-600',
    }
  },
  green: {
    primary: 'green',
    primaryHex: '#10b981',
    classes: {
      bg: 'bg-green-500',
      text: 'text-green-500',
      border: 'border-green-500',
      hover: 'hover:bg-green-600',
    }
  },
  red: {
    primary: 'red',
    primaryHex: '#ef4444',
    classes: {
      bg: 'bg-red-500',
      text: 'text-red-500',
      border: 'border-red-500',
      hover: 'hover:bg-red-600',
    }
  },
}

// Font size mappings
const fontSizeMap = {
  small: 'text-sm',
  medium: 'text-base',
  large: 'text-lg',
}

export function useTheme() {
  // Load theme from localStorage on client side
  const loadTheme = () => {
    if (process.client) {
      try {
        const stored = localStorage.getItem(THEME_STORAGE_KEY)
        if (stored) {
          const parsed = JSON.parse(stored)
          currentTheme.value = { ...defaultTheme, ...parsed }
        }
      } catch (error) {
        console.error('Error loading theme:', error)
      }
      applyTheme()
    }
  }

  // Save theme to localStorage
  const saveTheme = () => {
    if (process.client) {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(currentTheme.value))
      } catch (error) {
        console.error('Error saving theme:', error)
      }
    }
  }

  // Apply theme to document
  const applyTheme = () => {
    if (!process.client) return

    const html = document.documentElement

    // Apply dark/light mode
    if (currentTheme.value.mode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    // Apply accent color as CSS variables and dynamic styles
    const accentConfig = accentColorMap[currentTheme.value.accentColor]
    
    // Map full color palettes
    const colorPalettes: Record<string, Record<string, string>> = {
      purple: {
        '50': '#faf5ff', '100': '#f3e8ff', '200': '#e9d5ff', '300': '#d8b4fe',
        '400': '#bd73e8', '500': '#9d34da', '600': '#8b2db8', '700': '#7e22ce',
        '800': '#6b21a8', '900': '#581c87', '950': '#3b0764'
      },
      blue: {
        '50': '#eff6ff', '100': '#dbeafe', '200': '#bfdbfe', '300': '#93c5fd',
        '400': '#60a5fa', '500': '#3b82f6', '600': '#2563eb', '700': '#1d4ed8',
        '800': '#1e40af', '900': '#1e3a8a', '950': '#172554'
      },
      green: {
        '50': '#f0fdf4', '100': '#dcfce7', '200': '#bbf7d0', '300': '#86efac',
        '400': '#4ade80', '500': '#22c55e', '600': '#16a34a', '700': '#15803d',
        '800': '#166534', '900': '#14532d', '950': '#052e16'
      },
      red: {
        '50': '#fef2f2', '100': '#fee2e2', '200': '#fecaca', '300': '#fca5a5',
        '400': '#f87171', '500': '#ef4444', '600': '#dc2626', '700': '#b91c1c',
        '800': '#991b1b', '900': '#7f1d1d', '950': '#450a0a'
      }
    }
    
    const palette = colorPalettes[currentTheme.value.accentColor]
    
    // Inject or update dynamic style element
    let styleEl = document.getElementById('theme-dynamic-styles')
    if (!styleEl) {
      styleEl = document.createElement('style')
      styleEl.id = 'theme-dynamic-styles'
      document.head.appendChild(styleEl)
    }
    
    // Generate comprehensive CSS that overrides purple classes with selected color
    styleEl.textContent = `
      :root {
        --color-primary: ${accentConfig.primaryHex};
      }
      
      /* TEXT COLORS */
      .text-purple-300 { color: ${palette['300']} !important; }
      .text-purple-400 { color: ${palette['400']} !important; }
      .text-purple-500 { color: ${palette['500']} !important; }
      .text-purple-600 { color: ${palette['600']} !important; }
      
      /* BACKGROUND COLORS */
      .bg-purple-400 { background-color: ${palette['400']} !important; }
      .bg-purple-500 { background-color: ${palette['500']} !important; }
      .bg-purple-600 { background-color: ${palette['600']} !important; }
      
      /* BACKGROUND WITH OPACITY */
      .bg-purple-500\\/5 { background-color: ${palette['500']}0d !important; }
      .bg-purple-500\\/10 { background-color: ${palette['500']}1a !important; }
      .bg-purple-500\\/20 { background-color: ${palette['500']}33 !important; }
      .bg-purple-500\\/30 { background-color: ${palette['500']}4d !important; }
      
      /* BORDER COLORS */
      .border-purple-500 { border-color: ${palette['500']} !important; }
      .border-purple-600 { border-color: ${palette['600']} !important; }
      
      /* BORDER WITH OPACITY */
      .border-purple-500\\/10 { border-color: ${palette['500']}1a !important; }
      .border-purple-500\\/20 { border-color: ${palette['500']}33 !important; }
      .border-purple-500\\/30 { border-color: ${palette['500']}4d !important; }
      .border-purple-500\\/40 { border-color: ${palette['500']}66 !important; }
      .border-purple-500\\/50 { border-color: ${palette['500']}80 !important; }
      
      /* RING COLORS */
      .ring-purple-500 { --tw-ring-color: ${palette['500']} !important; }
      .ring-2.ring-purple-500 { --tw-ring-color: ${palette['500']} !important; }
      
      /* GRADIENTS */
      .from-purple-400 { --tw-gradient-from: ${palette['400']} !important; }
      .from-purple-500 { --tw-gradient-from: ${palette['500']} !important; }
      .from-purple-600 { --tw-gradient-from: ${palette['600']} !important; }
      .to-purple-500 { --tw-gradient-to: ${palette['500']} !important; }
      .to-purple-600 { --tw-gradient-to: ${palette['600']} !important; }
      .via-purple-500 { --tw-gradient-via: ${palette['500']} !important; }
      
      /* HOVER STATES */
      .hover\\:text-purple-300:hover { color: ${palette['300']} !important; }
      .hover\\:text-purple-400:hover { color: ${palette['400']} !important; }
      .hover\\:bg-purple-500:hover { background-color: ${palette['500']} !important; }
      .hover\\:bg-purple-500\\/10:hover { background-color: ${palette['500']}1a !important; }
      .hover\\:bg-purple-500\\/20:hover { background-color: ${palette['500']}33 !important; }
      .hover\\:border-purple-500:hover { border-color: ${palette['500']} !important; }
      .hover\\:border-purple-500\\/30:hover { border-color: ${palette['500']}4d !important; }
      .hover\\:border-purple-500\\/40:hover { border-color: ${palette['500']}66 !important; }
      .hover\\:border-purple-500\\/50:hover { border-color: ${palette['500']}80 !important; }
      
      /* FOCUS STATES */
      .focus\\:ring-purple-500:focus { --tw-ring-color: ${palette['500']} !important; }
      .focus\\:border-purple-500:focus { border-color: ${palette['500']} !important; }
      
      /* GROUP HOVER STATES */
      .group:hover .group-hover\\:text-purple-300 { color: ${palette['300']} !important; }
      .group:hover .group-hover\\:text-purple-400 { color: ${palette['400']} !important; }
      .group\\/card:hover .group-hover\\/card\\:from-purple-500\\/30 { --tw-gradient-from: ${palette['500']}4d !important; }
      .group\\/card:hover .group-hover\\/card\\:to-purple-600\\/30 { --tw-gradient-to: ${palette['600']}4d !important; }
      
      /* SHADOW COLORS */
      .shadow-purple-500\\/10 { --tw-shadow-color: ${palette['500']}1a !important; }
      .shadow-purple-500\\/20 { --tw-shadow-color: ${palette['500']}33 !important; }
      .shadow-purple-500\\/30 { --tw-shadow-color: ${palette['500']}4d !important; }
      .hover\\:shadow-purple-500\\/10:hover { --tw-shadow-color: ${palette['500']}1a !important; }
      .hover\\:shadow-purple-500\\/20:hover { --tw-shadow-color: ${palette['500']}33 !important; }
    `
    
    html.setAttribute('data-accent', currentTheme.value.accentColor)

    // Apply font size
    html.setAttribute('data-font-size', currentTheme.value.fontSize)
    
    // Apply font size class to root
    html.classList.remove('font-small', 'font-medium', 'font-large')
    html.classList.add(`font-${currentTheme.value.fontSize}`)

    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', accentConfig.primaryHex)
    }
  }

  // Set theme mode
  const setMode = (mode: 'dark' | 'light') => {
    currentTheme.value.mode = mode
    applyTheme()
    saveTheme()
  }

  // Set accent color
  const setAccentColor = (color: 'purple' | 'blue' | 'green' | 'red') => {
    currentTheme.value.accentColor = color
    applyTheme()
    saveTheme()
  }

  // Set font size
  const setFontSize = (size: 'small' | 'medium' | 'large') => {
    currentTheme.value.fontSize = size
    applyTheme()
    saveTheme()
  }

  // Set full theme config
  const setTheme = (theme: Partial<ThemeConfig>) => {
    currentTheme.value = { ...currentTheme.value, ...theme }
    applyTheme()
    saveTheme()
  }

  // Initialize theme on mount
  onMounted(() => {
    loadTheme()
  })

  return {
    // State
    theme: readonly(currentTheme),
    
    // Getters
    isDark: computed(() => currentTheme.value.mode === 'dark'),
    accentColor: computed(() => currentTheme.value.accentColor),
    fontSize: computed(() => currentTheme.value.fontSize),
    accentColorConfig: computed(() => accentColorMap[currentTheme.value.accentColor]),
    
    // Actions
    setMode,
    setAccentColor,
    setFontSize,
    setTheme,
    loadTheme,
  }
}

