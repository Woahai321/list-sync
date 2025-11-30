<template>
  <div class="space-y-4 sm:space-y-5">
    <!-- Sync Settings -->
    <div class="p-3 sm:p-4 md:p-5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-3 sm:space-y-4">
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
    <div class="p-3 sm:p-4 md:p-5 rounded-lg bg-gradient-to-br from-blue-600/20 to-blue-500/10 border border-blue-500/25 space-y-3 sm:space-y-4">
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-2">
          <component :is="BellIcon" :size="16" class="text-blue-400" />
          <span class="text-xs font-bold text-blue-300 uppercase tracking-wide">Discord (Optional)</span>
        </div>
        <button
          type="button"
          class="touch-manipulation"
          :class="[
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            localValue.discord_enabled ? 'bg-green-500' : 'bg-blue-500/20'
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
          <label class="text-xs font-semibold text-foreground">Webhook URL</label>
          <Tooltip content="Your Discord webhook URL. Create a webhook in your Discord server settings to get notifications about syncs.">
            <HelpCircleIcon :size="14" class="text-blue-400/60 hover:text-blue-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          v-model="localValue.discord_webhook"
          type="url"
          placeholder="https://discord.com/api/webhooks/..."
          :icon="MessageSquareIcon"
          :disabled="isValidating || isTesting"
        />
        <p v-if="errors.discord_webhook" class="text-xs text-red-400 mt-2 flex items-center gap-1.5">
          <component :is="AlertCircleIcon" :size="12" />
          {{ errors.discord_webhook }}
        </p>
        <p v-else-if="isTesting" class="text-xs text-purple-400/70 mt-2 flex items-center gap-1.5">
          <span class="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
          Validating webhook...
        </p>
        <p v-else-if="discordValidated" class="text-xs text-green-400/80 mt-2 flex items-center gap-1.5">
          <component :is="CheckCircleIcon" :size="14" />
          Webhook validated successfully
        </p>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex flex-col sm:flex-row justify-between gap-3 sm:gap-0 pt-4 sm:pt-6 border-t border-purple-500/10">
      <Button
        variant="secondary"
        @click="emit('back')"
        :disabled="isValidating"
        class="w-full sm:w-auto touch-manipulation min-h-[44px] order-2 sm:order-1"
      >
        Back
      </Button>
      <Button
        variant="primary"
        :loading="isValidating || isTesting"
        :disabled="!canProceed"
        @click="handleNext"
        class="w-full sm:w-auto touch-manipulation min-h-[44px] order-1 sm:order-2"
      >
        {{ (isValidating || isTesting) ? 'Validating...' : 'Complete Setup' }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Clock as ClockIcon,
  Bell as BellIcon,
  MessageSquare as MessageSquareIcon,
  CheckCircle as CheckCircleIcon,
  HelpCircle as HelpCircleIcon,
  AlertCircle as AlertCircleIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: {
    sync_interval: number
    auto_sync: boolean
    timezone: string
    discord_webhook: string
    discord_enabled: boolean
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
const discordValidated = ref(false)

// Reset validation state when values change
watch(() => localValue.value.discord_webhook, () => {
  discordValidated.value = false
})
watch(() => localValue.value.discord_enabled, () => {
  discordValidated.value = false
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

// Handle next button click - always validate Discord if enabled
const handleNext = async () => {
  // If Discord is enabled, always validate webhook
  if (localValue.value.discord_enabled && localValue.value.discord_webhook?.trim()) {
    const discordResult = await testDiscord()
    
    // If validation failed, don't proceed
    if (!discordResult) {
      return
    }
  }
  
  // Only proceed if validation passes
  if (canProceed.value && (!localValue.value.discord_enabled || discordValidated.value)) {
    emit('next')
  }
}
</script>
