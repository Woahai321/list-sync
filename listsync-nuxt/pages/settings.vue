<template>
  <div class="space-y-8 pb-24 lg:pb-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold flex items-center gap-3">
          <span class="bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
            Settings
          </span>
          <!-- Unsaved Changes Indicator -->
          <span 
            v-if="hasUnsavedChanges"
            class="inline-flex items-center gap-2 px-3 py-1 text-sm font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg animate-pulse-slow"
          >
            <span class="w-2 h-2 rounded-full bg-amber-400"></span>
            Unsaved Changes
          </span>
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          Configure your ListSync instance
        </p>
      </div>

      <div class="flex items-center gap-3">
        <Button
          variant="ghost"
          :icon="RefreshIcon"
          size="lg"
          :disabled="isSaving"
          @click="handleReset"
        >
          Reset
        </Button>
        <Button
          variant="primary"
          :icon="SaveIcon"
          size="lg"
          :loading="isSaving"
          :disabled="!hasUnsavedChanges"
          @click="handleSave"
        >
          Save Changes
        </Button>
      </div>
    </div>

    <!-- Settings Tabs -->
    <Card class="glass-card border border-purple-500/30 overflow-hidden">
      <!-- Tab Navigation -->
      <div class="border-b border-purple-500/20 bg-purple-500/5">
        <div class="flex items-center gap-2 overflow-x-auto px-4 py-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap transition-all duration-200 relative"
            :class="[
              activeTab === tab.id
                ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-sm'
                : 'hover:bg-purple-500/10 text-muted-foreground hover:text-purple-300 border border-transparent'
            ]"
            @click="activeTab = tab.id"
          >
            <component :is="tab.icon" class="w-4 h-4 flex-shrink-0" />
            <span class="text-sm font-bold uppercase tracking-wide">{{ tab.label }}</span>
          </button>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="p-6">
        <!-- Core Settings Tab -->
        <div v-if="activeTab === 'core'" class="space-y-6">
          <div class="space-y-6">
            <!-- Overseerr Configuration -->
            <OverseerrConfig
              v-model="settings.overseerr"
              @test-connection="testOverseerrConnection"
            />

            <!-- Sync Settings -->
            <SyncSettings
              v-model="settings.sync"
            />
          </div>
        </div>

        <!-- API Keys Tab -->
        <div v-if="activeTab === 'api-keys'" class="space-y-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Trakt API Settings -->
            <TraktApiSettings
              v-model="settings.traktApi"
            />

            <!-- TMDB API Settings -->
            <TmdbApiSettings
              v-model="settings.tmdbApi"
            />
          </div>
        </div>

        <!-- Integrations Tab -->
        <div v-if="activeTab === 'integrations'" class="space-y-6">
          <!-- Notification Settings -->
          <NotificationSettings
            v-model="settings.notifications"
            @test-notification="testNotification"
          />
        </div>

        <!-- Advanced Tab -->
        <div v-if="activeTab === 'advanced'" class="space-y-6">
          <!-- Service Endpoints -->
          <ServiceEndpointsSettings
            v-model="settings.serviceEndpoints"
          />
        </div>

        <!-- About Tab -->
        <div v-if="activeTab === 'about'">
          <AboutSection />
        </div>
      </div>
    </Card>

    <!-- Save Footer (Sticky on mobile) -->
    <div 
      v-if="hasUnsavedChanges"
      class="fixed bottom-0 left-0 right-0 lg:hidden bg-gradient-to-r from-amber-500/20 to-orange-500/20 backdrop-blur-lg border-t-2 border-amber-500/50 p-4 z-40 shadow-2xl shadow-amber-500/20"
    >
      <div class="flex items-center gap-3">
        <Button
          variant="ghost"
          class="flex-1"
          :disabled="isSaving"
          @click="handleReset"
        >
          Reset
        </Button>
        <Button
          variant="primary"
          class="flex-1"
          :loading="isSaving"
          @click="handleSave"
        >
          Save Changes
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
  Key as KeyIcon,
  Bell as BellIcon,
  Code as CodeIcon,
  Info as InfoIcon,
} from 'lucide-vue-next'

const { showSuccess, showError, showInfo } = useToast()

// Set page title
useHead({
  title: 'Settings - ListSync',
})

// Tab state
const activeTab = ref('core')

// Tab definitions
const tabs = [
  {
    id: 'core',
    label: 'Core',
    icon: SettingsIcon,
    description: 'Overseerr and sync settings',
  },
  {
    id: 'api-keys',
    label: 'API Keys',
    icon: KeyIcon,
    description: 'Trakt and TMDB API keys',
  },
  {
    id: 'integrations',
    label: 'Integrations',
    icon: BellIcon,
    description: 'Discord notifications',
  },
  {
    id: 'advanced',
    label: 'Advanced',
    icon: CodeIcon,
    description: 'Service endpoints and advanced options',
  },
  {
    id: 'about',
    label: 'About',
    icon: InfoIcon,
    description: 'System information',
  },
]

// State
const isSaving = ref(false)
const hasUnsavedChanges = ref(false)
const settings = ref({
  overseerr: {
    url: '',
    apiKey: '',
    userId: '',
    enable4k: false,
  },
  traktApi: {
    clientId: '',
  },
  tmdbApi: {
    apiKey: '',
  },
  sync: {
    interval: 24,
    automatedMode: true,
    timezone: 'UTC',
  },
  notifications: {
    discordWebhook: '',
    enabled: false,
  },
  serviceEndpoints: {
    frontendDomain: '',
    backendDomain: '',
    nuxtPublicApiUrl: '',
  },
})

// Watch for changes to settings
watch(settings, () => {
  hasUnsavedChanges.value = true
}, { deep: true })

// Load settings on mount
const loadSettings = async () => {
  try {
    const api = useApiService()
    
    // Fetch both config and sync interval
    const [config, syncIntervalData] = await Promise.all([
      api.getConfig(),
      api.getSyncInterval()
    ])
    
    // Map API response to settings
    if (config) {
      settings.value.overseerr = {
        url: config.overseerr_url || '',
        apiKey: config.overseerr_api_key || '',
        userId: config.overseerr_user_id || '',
        enable4k: config.overseerr_4k || false,
      }
      
      settings.value.traktApi = {
        clientId: config.trakt_client_id || '',
      }
      
      settings.value.tmdbApi = {
        apiKey: config.tmdb_key || '',
      }
      
      // Use database sync interval if available, otherwise use environment
      settings.value.sync = {
        interval: syncIntervalData?.interval_hours || config.sync_interval || 24,
        automatedMode: config.auto_sync || true,
        timezone: config.timezone || 'UTC',
      }
      
      settings.value.notifications = {
        discordWebhook: config.discord_webhook || '',
        enabled: config.discord_enabled || false,
      }
      
      settings.value.serviceEndpoints = {
        frontendDomain: config.frontend_domain || 'http://localhost:3222',
        backendDomain: config.backend_domain || 'http://localhost:4222',
        nuxtPublicApiUrl: config.nuxt_public_api_url || 'http://localhost:4222',
      }
    }
    
    // Reset unsaved changes flag after loading
    await nextTick()
    hasUnsavedChanges.value = false
  } catch (error) {
    console.error('Error loading settings:', error)
  }
}

// Save settings
const handleSave = async () => {
  isSaving.value = true
  try {
    const api = useApiService()
    
    // Update sync interval in database (this is the active config)
    await api.updateSyncInterval(settings.value.sync.interval)
    
    // Prepare payload for other settings
    const payload = {
      // Overseerr Configuration
      overseerr_url: settings.value.overseerr.url,
      overseerr_api_key: settings.value.overseerr.apiKey,
      overseerr_user_id: settings.value.overseerr.userId,
      overseerr_4k: settings.value.overseerr.enable4k,
      
      // Trakt API
      trakt_client_id: settings.value.traktApi.clientId,
      
      // TMDB API
      tmdb_key: settings.value.tmdbApi.apiKey,
      
      // Sync Settings
      sync_interval: settings.value.sync.interval,
      auto_sync: settings.value.sync.automatedMode,
      timezone: settings.value.sync.timezone,
      
      // Notifications
      discord_webhook: settings.value.notifications.discordWebhook,
      discord_enabled: settings.value.notifications.enabled,
      
      // Service Endpoints
      frontend_domain: settings.value.serviceEndpoints.frontendDomain,
      backend_domain: settings.value.serviceEndpoints.backendDomain,
      nuxt_public_api_url: settings.value.serviceEndpoints.nuxtPublicApiUrl,
    }
    
    await api.updateConfig(payload)
    hasUnsavedChanges.value = false
    showSuccess('Settings Saved', 'Sync interval updated in database. Other settings require container restart.')
  } catch (error: any) {
    showError('Save Failed', error.message)
  } finally {
    isSaving.value = false
  }
}

// Reset settings
const handleReset = () => {
  loadSettings()
  showInfo('Settings Reset', 'Settings have been reloaded')
}

// Test Overseerr connection
const testOverseerrConnection = async () => {
  try {
    const api = useApiService()
    const status = await api.checkOverseerr()
    
    if (status.isConnected) {
      showSuccess('Connection Successful', 'Overseerr is connected and working')
    } else {
      showError('Connection Failed', status.error || 'Unable to connect to Overseerr')
    }
  } catch (error: any) {
    showError('Connection Failed', error.message)
  }
}

// Test notification
const testNotification = async () => {
  try {
    // Validate webhook URL
    if (!settings.value.notifications.discordWebhook || !settings.value.notifications.discordWebhook.trim()) {
      showError('Webhook URL Required', 'Please enter a Discord webhook URL before testing')
      return
    }
    
    showInfo('Sending Test', 'Sending test notification...')
    
    const api = useApiService()
    // Pass the webhook URL from the form to the test endpoint
    await api.testDiscordNotification(settings.value.notifications.discordWebhook)
    
    showSuccess('Test Sent', 'Check your Discord channel for the test notification')
  } catch (error: any) {
    showError('Test Failed', error.message || 'Unable to send test notification')
  }
}

// Load settings on mount
onMounted(() => {
  loadSettings()
})
</script>
