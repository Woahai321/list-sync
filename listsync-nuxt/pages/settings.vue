<template>
  <div class="space-y-8 pb-24 lg:pb-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold flex items-center gap-3">
          Settings
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

    <!-- Settings Sections -->
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

      <!-- Notification Settings -->
      <NotificationSettings
        v-model="settings.notifications"
        @test-notification="testNotification"
      />

      <!-- Theme Settings -->
      <ThemeSettings
        v-model="settings.theme"
      />

      <!-- About Section -->
      <AboutSection />
    </div>

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
} from 'lucide-vue-next'

const { showSuccess, showError, showInfo } = useToast()

// Set page title
useHead({
  title: 'Settings - ListSync',
})

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
  sync: {
    interval: 24,
    automatedMode: true,
    timezone: 'UTC',
  },
  notifications: {
    discordWebhook: '',
    enabled: false,
  },
  theme: {
    mode: 'dark',
    accentColor: 'purple',
    fontSize: 'medium',
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
    const { theme: currentTheme } = useTheme()
    
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
      
      // Load theme from localStorage (managed by useTheme)
      settings.value.theme = {
        mode: currentTheme.value.mode,
        accentColor: currentTheme.value.accentColor,
        fontSize: currentTheme.value.fontSize,
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
      overseerr_url: settings.value.overseerr.url,
      overseerr_api_key: settings.value.overseerr.apiKey,
      overseerr_user_id: settings.value.overseerr.userId,
      overseerr_4k: settings.value.overseerr.enable4k,
      sync_interval: settings.value.sync.interval,
      auto_sync: settings.value.sync.automatedMode,
      timezone: settings.value.sync.timezone,
      discord_webhook: settings.value.notifications.discordWebhook,
      discord_enabled: settings.value.notifications.enabled,
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

