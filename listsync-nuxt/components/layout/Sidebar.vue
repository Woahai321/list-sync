<template>
  <aside :class="sidebarClasses">
    <!-- Logo / Header -->
    <div class="flex items-center justify-between px-6 py-6 border-b border-purple-500/20">
      <NuxtLink to="/" class="flex items-center gap-3 text-foreground hover:text-purple-400 transition-colors">
        <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-purple-500/20 overflow-hidden">
          <img 
            src="https://s.2ya.me/api/shares/RN2Yziau/files/535b57e0-9c64-410b-a36f-414fba74854b" 
            alt="ListSync Logo" 
            class="w-8 h-8 object-contain"
          />
        </div>
        <span v-if="!uiStore.sidebarCollapsed" class="text-xl font-bold titillium-web-bold">
          ListSync
        </span>
      </NuxtLink>

      <!-- Collapse Toggle (Desktop) -->
      <button
        v-if="!isMobile"
        type="button"
        class="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground"
        @click="uiStore.toggleSidebar"
        :aria-label="uiStore.sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <component :is="uiStore.sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" :size="20" />
      </button>

      <!-- Close Button (Mobile) -->
      <button
        v-if="isMobile"
        type="button"
        class="p-2 rounded-lg hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground lg:hidden"
        @click="uiStore.closeMobileMenu"
        aria-label="Close menu"
      >
        <component :is="XIcon" :size="20" />
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-6 space-y-1 overflow-y-auto custom-scrollbar">
      <NuxtLink
        v-for="item in navigation"
        :key="item.path"
        :to="item.path"
        :class="navItemClasses(item.path)"
        @click="handleNavClick"
      >
        <component :is="item.icon" :size="20" />
        <span v-if="!uiStore.sidebarCollapsed" class="flex-1">
          {{ item.label }}
        </span>
      </NuxtLink>
    </nav>

    <!-- Footer (System Status) -->
    <div class="px-3 py-4 border-t border-purple-500/20">
      <div :class="footerClasses">
        <div class="flex items-center gap-3">
          <div :class="statusDotClass" />
          <div v-if="!uiStore.sidebarCollapsed" class="flex-1 min-w-0">
            <p class="text-sm font-medium text-foreground">System Status</p>
            <p class="text-xs text-muted-foreground truncate">
              {{ systemStore.isHealthy ? 'All systems operational' : 'Issues detected' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard as DashboardIcon,
  List as ListIcon,
  RefreshCw as SyncIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Database as DatabaseIcon,
  FileText as LogsIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  X as XIcon,
} from 'lucide-vue-next'

const route = useRoute()
const uiStore = useUIStore()
const systemStore = useSystemStore()

const isMobile = ref(false)

const navigation = [
  {
    label: 'Dashboard',
    path: '/',
    icon: DashboardIcon,
  },
  {
    label: 'Lists',
    path: '/lists',
    icon: ListIcon,
  },
  {
    label: 'Items',
    path: '/items',
    icon: DatabaseIcon,
  },
  {
    label: 'Sync',
    path: '/sync',
    icon: SyncIcon,
  },
  {
    label: 'Sync History',
    path: '/sync-history',
    icon: HistoryIcon,
  },
  {
    label: 'Live Logs',
    path: '/logs',
    icon: LogsIcon,
  },
  {
    label: 'Settings',
    path: '/settings',
    icon: SettingsIcon,
  },
]

const sidebarClasses = computed(() => {
  const baseClasses = [
    'flex flex-col h-screen',
    'glass-sidebar',
    'transition-all duration-300',
  ]

  // Width classes
  if (uiStore.sidebarCollapsed) {
    baseClasses.push('w-20')
  } else {
    baseClasses.push('w-64')
  }

  // Mobile classes
  if (isMobile.value) {
    baseClasses.push(
      'fixed inset-y-0 left-0 z-40',
      'transform lg:transform-none',
      uiStore.mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
    )
  }

  return baseClasses.join(' ')
})

const navItemClasses = (path: string) => {
  const isActive = route.path === path || (path !== '/' && route.path.startsWith(path))
  
  const baseClasses = [
    'flex items-center gap-3 px-3 py-2.5 rounded-lg',
    'text-sm font-medium',
    'transition-all duration-200',
    'group',
  ]

  if (uiStore.sidebarCollapsed) {
    baseClasses.push('justify-center')
  }

  if (isActive) {
    baseClasses.push(
      'bg-purple-500/20',
      'text-purple-300',
      'border border-purple-500/30'
    )
  } else {
    baseClasses.push(
      'text-muted-foreground',
      'hover:bg-white/5',
      'hover:text-foreground',
      'border border-transparent'
    )
  }

  return baseClasses.join(' ')
}

const footerClasses = computed(() => {
  const baseClasses = [
    'p-3 rounded-lg',
    'bg-black/20',
    'border border-purple-500/10',
  ]

  if (uiStore.sidebarCollapsed) {
    baseClasses.push('flex justify-center')
  }

  return baseClasses.join(' ')
})

const statusDotClass = computed(() => {
  const baseClasses = ['w-2 h-2 rounded-full']
  
  if (systemStore.isHealthy) {
    baseClasses.push('bg-green-500 pulse-glow')
  } else {
    baseClasses.push('bg-red-500 animate-pulse')
  }

  return baseClasses.join(' ')
})

const handleNavClick = () => {
  if (isMobile.value) {
    uiStore.closeMobileMenu()
  }
}

// Check if mobile on mount and resize
const checkMobile = () => {
  if (process.client) {
    isMobile.value = window.innerWidth < 1024
  }
}

onMounted(() => {
  checkMobile()
  if (process.client) {
    window.addEventListener('resize', checkMobile)
    
    // Fetch system health
    systemStore.checkHealth()
  }
})

onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('resize', checkMobile)
  }
})
</script>

