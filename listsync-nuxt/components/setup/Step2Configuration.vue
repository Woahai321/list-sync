<template>
  <div class="space-y-3 sm:space-y-4" role="region" aria-labelledby="step2-heading">
    <!-- Step Header -->
    <div class="text-center mb-3 sm:mb-4 animate-fade-in">
      <h2 id="step2-heading" class="text-lg sm:text-xl font-bold text-foreground mb-1.5 titillium-web-bold">
        Configure Your Settings
      </h2>
      <p class="text-xs sm:text-sm text-muted-foreground max-w-xl mx-auto">
        Set up Trakt integration, sync schedule, and optional Discord notifications.
      </p>
    </div>

    <!-- Trakt Section -->
    <div class="p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-2.5 sm:space-y-3" role="group" aria-labelledby="trakt-section">
      <div class="flex items-center gap-2 mb-1">
        <component :is="FilmIcon" :size="16" class="text-purple-400" aria-hidden="true" />
        <span id="trakt-section" class="text-xs font-bold text-purple-300 uppercase tracking-wide">Trakt</span>
      </div>
      
      <div>
        <div class="flex items-center gap-1.5 mb-2">
          <label for="trakt-client-id" class="text-xs font-semibold text-foreground">
            Client ID
            <span class="text-red-400 ml-1" aria-label="required">*</span>
          </label>
          <Tooltip content="Your Trakt Client ID. Create a new application at trakt.tv/oauth/applications to get your Client ID.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          id="trakt-client-id"
          v-model="localValue.trakt_client_id"
          type="password"
          placeholder="••••••••••••••••"
          :icon="KeyIcon"
          :disabled="isValidating || isTestingTrakt"
          aria-required="true"
          aria-describedby="trakt-client-id-status trakt-client-id-help"
        />
        <p v-if="errors.trakt_client_id" id="trakt-client-id-status" class="text-xs text-red-400 mt-2 flex items-center gap-1.5 animate-fade-in" role="alert">
          <component :is="AlertCircleIcon" :size="14" aria-hidden="true" />
          {{ errors.trakt_client_id }}
        </p>
        <p v-else-if="traktValidated" id="trakt-client-id-status" class="text-xs text-green-400 mt-2 flex items-center gap-1.5 animate-fade-in" role="status">
          <component :is="CheckCircleIcon" :size="14" aria-hidden="true" />
          <span class="font-medium">Valid Client ID</span>
        </p>
        <a 
          id="trakt-client-id-help"
          href="https://trakt.tv/oauth/applications" 
          target="_blank"
          rel="noopener noreferrer"
          class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-flex items-center gap-1.5 transition-colors"
        >
          Get your Client ID
          <component :is="ExternalLinkIcon" :size="12" aria-hidden="true" />
        </a>
      </div>
    </div>

    <!-- Sync Settings -->
    <div class="p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-2.5 sm:space-y-3">
      <div class="flex items-center gap-2 mb-1">
        <component :is="ClockIcon" :size="16" class="text-purple-400" />
        <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Sync Schedule</span>
      </div>
      
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <div class="flex items-center gap-1.5 mb-2">
            <label class="text-xs font-semibold text-foreground">Interval (hours)</label>
            <Tooltip content="How often to automatically sync your lists. Minimum 1 hour, maximum 168 hours (7 days).">
              <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
            </Tooltip>
          </div>
          <Input
            v-model.number="localValue.sync_interval"
            type="number"
            :min="1"
            :max="168"
            placeholder="24"
            :disabled="isValidating"
          />
        </div>
        
        <div>
          <div class="flex items-center gap-1.5 mb-2">
            <label class="text-xs font-semibold text-foreground">Timezone</label>
            <Tooltip content="Your local timezone for scheduling syncs. This ensures syncs happen at the right time in your location.">
              <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
            </Tooltip>
          </div>
          <select
            v-model="localValue.timezone"
            class="w-full px-3 py-2.5 sm:py-2 h-11 sm:h-10 bg-black/30 border border-purple-500/25 rounded-lg text-base sm:text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all touch-manipulation"
            :disabled="isValidating"
          >
            <option v-for="tz in commonTimezones" :key="tz" :value="tz">
              {{ tz }}
            </option>
          </select>
        </div>
      </div>

      <div class="flex items-center justify-between p-2.5 sm:p-3 rounded-lg bg-purple-500/5 border border-purple-500/10">
        <div class="flex items-center gap-1.5">
          <span class="text-xs font-semibold text-foreground">Auto Sync</span>
          <Tooltip content="Enable automatic syncing of your lists at the configured interval. Disable to sync manually only.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <button
          type="button"
          :class="[
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors touch-manipulation',
            localValue.auto_sync ? 'bg-green-500' : 'bg-purple-500/20'
          ]"
          @click="localValue.auto_sync = !localValue.auto_sync"
        >
          <span
            :class="[
              'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
              localValue.auto_sync ? 'translate-x-5' : 'translate-x-0.5'
            ]"
          />
        </button>
      </div>
    </div>

    <!-- Discord Notifications (Optional) -->
    <div class="p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-2.5 sm:space-y-3">
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-2">
          <component :is="BellIcon" :size="16" class="text-purple-400" />
          <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Discord (Optional)</span>
        </div>
        <button
          type="button"
          class="touch-manipulation"
          :class="[
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            localValue.discord_enabled ? 'bg-green-500' : 'bg-purple-500/20'
          ]"
          @click="localValue.discord_enabled = !localValue.discord_enabled"
        >
          <span
            :class="[
              'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
              localValue.discord_enabled ? 'translate-x-5' : 'translate-x-0.5'
            ]"
          />
        </button>
      </div>
      
      <div v-if="localValue.discord_enabled">
        <div class="flex items-center gap-1.5 mb-2">
          <label class="text-xs font-semibold text-foreground">
            Webhook URL
            <span class="text-red-400 ml-1">*</span>
          </label>
          <Tooltip content="Your Discord webhook URL. Create a webhook in your Discord server settings to get notifications about syncs.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          v-model="localValue.discord_webhook"
          type="url"
          placeholder="https://discord.com/api/webhooks/..."
          :icon="MessageSquareIcon"
          :disabled="isValidating || isTesting"
        />
        <p v-if="errors.discord_webhook" class="text-xs text-red-400 mt-2 flex items-center gap-1.5 animate-fade-in">
          <component :is="AlertCircleIcon" :size="14" />
          {{ errors.discord_webhook }}
        </p>
        <p v-else-if="isTesting" class="text-xs text-purple-400 mt-2 flex items-center gap-1.5">
          <span class="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
          Validating webhook...
        </p>
        <p v-else-if="discordValidated" class="text-xs text-green-400 mt-2 flex items-center gap-1.5 animate-fade-in">
          <component :is="CheckCircleIcon" :size="14" />
          <span class="font-medium">Webhook validated successfully</span>
        </p>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex flex-col sm:flex-row justify-between gap-3 sm:gap-0 pt-3 sm:pt-4 border-t border-purple-500/10">
      <Button
        variant="secondary"
        @click="emit('back')"
        :disabled="isValidating"
        class="w-full sm:w-auto touch-manipulation min-h-[44px] order-2 sm:order-1"
        :aria-label="'Go back to previous step'"
      >
        Back
      </Button>
      
      <div class="relative w-full sm:w-auto order-1 sm:order-2">
        <Button
          variant="primary"
          :loading="isValidating || isTesting || isTestingTrakt"
          :disabled="!canProceed"
          @click="handleNext"
          class="w-full sm:w-auto touch-manipulation min-h-[44px]"
          :aria-label="canProceed ? 'Complete setup' : 'Fill in all required fields to complete setup'"
        >
          {{ (isValidating || isTesting || isTestingTrakt) ? 'Validating...' : 'Complete Setup' }}
        </Button>
        
        <!-- Tooltip for disabled state -->
        <Tooltip 
          v-if="!canProceed && !isValidating && !isTesting && !isTestingTrakt"
          content="Please fill in all required fields to complete setup"
          placement="top"
        >
          <div class="absolute inset-0 cursor-not-allowed" />
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Clock as ClockIcon,
  Bell as BellIcon,
  MessageSquare as MessageSquareIcon,
  Film as FilmIcon,
  Key as KeyIcon,
  CheckCircle as CheckCircleIcon,
  HelpCircle as HelpCircleIcon,
  AlertCircle as AlertCircleIcon,
  ExternalLink as ExternalLinkIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: {
    sync_interval: number
    auto_sync: boolean
    timezone: string
    discord_webhook: string
    discord_enabled: boolean
    trakt_client_id: string
  }
  isValidating: boolean
  errors: Record<string, string>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'next', 'back'])

const { showSuccess, showError } = useToast()
const api = useApiService()

const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isTesting = ref(false)
const isTestingTrakt = ref(false)
const discordValidated = ref(false)
const traktValidated = ref(false)

// Reset validation state when values change
watch(() => localValue.value.discord_webhook, () => {
  discordValidated.value = false
})
watch(() => localValue.value.discord_enabled, () => {
  discordValidated.value = false
})
watch(() => localValue.value.trakt_client_id, () => {
  traktValidated.value = false
})

// Common timezones for quick selection
const commonTimezones = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Toronto',
  'America/Vancouver',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Amsterdam',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Hong_Kong',
  'Asia/Singapore',
  'Australia/Sydney',
  'Australia/Melbourne',
  'Pacific/Auckland',
]

// Check if we can proceed (basic validation)
const canProceed = computed(() => {
  // Trakt Client ID is required
  if (!localValue.value.trakt_client_id?.trim()) {
    return false
  }
  
  // Basic validation
  if (localValue.value.sync_interval < 1 || localValue.value.sync_interval > 168) {
    return false
  }
  
  // If Discord is enabled, webhook must be provided
  if (localValue.value.discord_enabled && !localValue.value.discord_webhook?.trim()) {
    return false
  }
  
  return true
})

// Test Trakt Client ID
const testTrakt = async () => {
  if (!localValue.value.trakt_client_id) return false
  
  isTestingTrakt.value = true
  traktValidated.value = false
  
  try {
    const result: any = await api.testTraktClientId({
      trakt_client_id: localValue.value.trakt_client_id,
    })
    
    if (result.valid) {
      traktValidated.value = true
      return true
    } else {
      traktValidated.value = false
      showError('Trakt Validation Failed', result.error || 'Invalid Trakt Client ID')
      return false
    }
  } catch (error: any) {
    traktValidated.value = false
    showError('Trakt Validation Failed', error.message || 'Failed to validate Trakt Client ID')
    return false
  } finally {
    isTestingTrakt.value = false
  }
}

// Test Discord webhook
const testDiscord = async () => {
  if (!localValue.value.discord_webhook) return
  
  isTesting.value = true
  discordValidated.value = false
  
  try {
    await api.testDiscordWebhook(localValue.value.discord_webhook)
    discordValidated.value = true
    return true
  } catch (error: any) {
    discordValidated.value = false
    showError('Discord Webhook Failed', error.message || 'Failed to send test message')
    return false
  } finally {
    isTesting.value = false
  }
}

// Handle next button click - always validate Trakt and Discord if enabled
const handleNext = async () => {
  // Always validate Trakt Client ID
  const traktResult = await testTrakt()
  
  // If Trakt validation failed, don't proceed
  if (!traktResult) {
    return
  }
  
  // If Discord is enabled, always validate webhook
  if (localValue.value.discord_enabled && localValue.value.discord_webhook?.trim()) {
    const discordResult = await testDiscord()
    
    // If validation failed, don't proceed
    if (!discordResult) {
      return
    }
  }
  
  // Only proceed if validation passes
  if (canProceed.value && traktValidated.value && (!localValue.value.discord_enabled || discordValidated.value)) {
    emit('next')
  }
}
</script>
