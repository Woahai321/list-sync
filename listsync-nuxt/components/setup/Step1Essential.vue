<template>
  <div class="space-y-5 relative">
    <!-- Validation Status - Compact inline indicators (top right) -->
    <div v-if="(isTestingOverseerr || isTestingTrakt || overseerrValidated || traktValidated) && localValue.overseerr_url && localValue.overseerr_api_key && localValue.trakt_client_id" class="absolute top-0 right-0 flex items-center gap-1.5 sm:gap-2 text-xs z-10 bg-black/50 backdrop-blur-sm px-2 py-1 rounded-lg">
      <div class="flex items-center gap-1">
        <span v-if="isTestingOverseerr" class="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
        <component :is="CheckCircleIcon" v-else-if="overseerrValidated" :size="12" class="text-green-400 flex-shrink-0" />
        <span v-else class="w-3 h-3 rounded-full border-2 border-red-400 flex-shrink-0" />
        <span :class="overseerrValidated ? 'text-green-400' : isTestingOverseerr ? 'text-purple-400' : 'text-red-400'" class="hidden sm:inline text-[10px] sm:text-xs">
          Overseerr
        </span>
      </div>
      <div class="flex items-center gap-1">
        <span v-if="isTestingTrakt" class="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
        <component :is="CheckCircleIcon" v-else-if="traktValidated" :size="12" class="text-green-400 flex-shrink-0" />
        <span v-else class="w-3 h-3 rounded-full border-2 border-red-400 flex-shrink-0" />
        <span :class="traktValidated ? 'text-green-400' : isTestingTrakt ? 'text-purple-400' : 'text-red-400'" class="hidden sm:inline text-[10px] sm:text-xs">
          Trakt
        </span>
      </div>
    </div>
    <!-- Overseerr Section -->
    <div class="p-3 sm:p-4 md:p-5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-3 sm:space-y-4">
      <div class="flex items-center gap-2 mb-1">
        <component :is="ServerIcon" :size="16" class="text-purple-400" />
        <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Overseerr</span>
      </div>
      
      <div>
        <div class="flex items-center gap-1.5 mb-2">
          <label class="text-xs font-semibold text-foreground">URL</label>
          <Tooltip content="The URL where your Overseerr instance is hosted. This is the web address you use to access Overseerr.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          v-model="localValue.overseerr_url"
          type="url"
          placeholder="https://overseerr.example.com"
          :icon="GlobeIcon"
          :disabled="isValidating"
        />
        <p v-if="errors.overseerr_url" class="text-xs text-red-400 mt-2 flex items-center gap-1.5">
          <component :is="AlertCircleIcon" :size="12" />
          {{ errors.overseerr_url }}
        </p>
      </div>

      <div>
        <div class="flex items-center gap-1.5 mb-2">
          <label class="text-xs font-semibold text-foreground">API Key</label>
          <Tooltip content="Your Overseerr API key. You can find this in Overseerr Settings > General > API Key.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          v-model="localValue.overseerr_api_key"
          type="password"
          placeholder="••••••••••••••••"
          :icon="KeyIcon"
          :disabled="isValidating || isTestingOverseerr"
        />
        <p v-if="errors.overseerr_api_key" class="text-xs text-red-400 mt-2 flex items-center gap-1.5">
          <component :is="AlertCircleIcon" :size="12" />
          {{ errors.overseerr_api_key }}
        </p>
        <p v-else-if="overseerrValidated" class="text-xs text-green-400/80 mt-1.5 flex items-center gap-1">
          <component :is="CheckCircleIcon" :size="12" />
          <span>Connected</span>
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <div class="flex items-center gap-1.5 mb-2">
            <label class="text-xs font-semibold text-foreground">User ID</label>
            <Tooltip content="The user ID for requests. Default is 1. You can find user IDs on each user's profile page in Overseerr.">
              <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
            </Tooltip>
          </div>
          <Input
            v-model="localValue.overseerr_user_id"
            type="text"
            placeholder="1"
            :disabled="isValidating"
          />
        </div>
        
        <div class="flex items-end">
          <div class="flex items-center justify-between gap-2 p-2.5 sm:p-3 rounded-lg bg-purple-500/5 border border-purple-500/10 w-full">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-foreground">4K</span>
              <Tooltip content="Enable this if you want requests sent to Overseerr to be 4K requests. Disable for standard quality requests.">
                <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
              </Tooltip>
            </div>
            <button
              type="button"
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors touch-manipulation',
                localValue.overseerr_4k ? 'bg-green-500' : 'bg-purple-500/20'
              ]"
              @click="localValue.overseerr_4k = !localValue.overseerr_4k"
            >
              <span
                :class="[
                  'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
                  localValue.overseerr_4k ? 'translate-x-5' : 'translate-x-0.5'
                ]"
              />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Trakt Section -->
    <div class="p-3 sm:p-4 md:p-5 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-3 sm:space-y-4">
      <div class="flex items-center gap-2 mb-1">
        <component :is="FilmIcon" :size="16" class="text-purple-400" />
        <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Trakt</span>
      </div>
      
      <div>
        <div class="flex items-center gap-1.5 mb-2">
          <label class="text-xs font-semibold text-foreground">Client ID</label>
          <Tooltip content="Your Trakt Client ID. Create a new application at trakt.tv/oauth/applications to get your Client ID.">
            <HelpCircleIcon :size="14" class="text-purple-400/60 hover:text-purple-400 cursor-help transition-colors" />
          </Tooltip>
        </div>
        <Input
          v-model="localValue.trakt_client_id"
          type="password"
          placeholder="••••••••••••••••"
          :icon="KeyIcon"
          :disabled="isValidating || isTestingTrakt"
        />
        <p v-if="errors.trakt_client_id" class="text-xs text-red-400 mt-2 flex items-center gap-1.5">
          <component :is="AlertCircleIcon" :size="12" />
          {{ errors.trakt_client_id }}
        </p>
        <p v-else-if="traktValidated" class="text-xs text-green-400/80 mt-1.5 flex items-center gap-1">
          <component :is="CheckCircleIcon" :size="12" />
          <span>Valid</span>
        </p>
        <a 
          href="https://trakt.tv/oauth/applications" 
          target="_blank"
          class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-flex items-center gap-1.5 transition-colors"
        >
          Get your Client ID
          <component :is="ExternalLinkIcon" :size="12" />
        </a>
      </div>
    </div>


    <!-- Action Button -->
    <div class="flex justify-end pt-4 sm:pt-6 border-t border-purple-500/10">
      <Button
        variant="primary"
        :loading="isValidating || isTestingOverseerr || isTestingTrakt"
        :disabled="!canProceed"
        @click="handleNext"
        class="w-full sm:w-auto touch-manipulation min-h-[44px]"
      >
        {{ (isValidating || isTestingOverseerr || isTestingTrakt) ? 'Validating...' : 'Continue' }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Globe as GlobeIcon,
  Key as KeyIcon,
  Server as ServerIcon,
  Film as FilmIcon,
  CheckCircle as CheckCircleIcon,
  HelpCircle as HelpCircleIcon,
  AlertCircle as AlertCircleIcon,
  ExternalLink as ExternalLinkIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: {
    overseerr_url: string
    overseerr_api_key: string
    overseerr_user_id: string
    overseerr_4k: boolean
    trakt_client_id: string
  }
  isValidating: boolean
  errors: Record<string, string>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'next', 'clearError'])

const { showSuccess, showError } = useToast()
const api = useApiService()

const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Validation state
const isTestingOverseerr = ref(false)
const isTestingTrakt = ref(false)
const overseerrValidated = ref(false)
const traktValidated = ref(false)

// Check if we can proceed (all fields filled)
const canProceed = computed(() => {
  return localValue.value.overseerr_url?.trim() && 
         localValue.value.overseerr_api_key?.trim() &&
         localValue.value.trakt_client_id?.trim()
})

// Reset validation state and clear errors when values change
// IMPORTANT: Reset ALL validation state when ANY input changes to ensure fresh validation
watch(() => localValue.value?.overseerr_url, (newVal, oldVal) => {
  // Only reset if value actually changed (not on initial mount) and localValue exists
  if (localValue.value && newVal !== oldVal) {
    overseerrValidated.value = false
    traktValidated.value = false // Also reset Trakt to ensure fresh validation
    isTestingOverseerr.value = false
    isTestingTrakt.value = false
    // Clear ALL errors for this field
    emit('clearError', 'overseerr_url')
    emit('clearError', 'overseerr_api_key')
    emit('clearError', 'trakt_client_id')
  }
}, { immediate: false })
watch(() => localValue.value?.overseerr_api_key, (newVal, oldVal) => {
  // Only reset if value actually changed (not on initial mount) and localValue exists
  if (localValue.value && newVal !== oldVal) {
    overseerrValidated.value = false
    traktValidated.value = false // Also reset Trakt to ensure fresh validation
    isTestingOverseerr.value = false
    isTestingTrakt.value = false
    // Clear ALL errors for this field
    emit('clearError', 'overseerr_url')
    emit('clearError', 'overseerr_api_key')
    emit('clearError', 'trakt_client_id')
  }
}, { immediate: false })
watch(() => localValue.value?.trakt_client_id, (newVal, oldVal) => {
  // Only reset if value actually changed (not on initial mount) and localValue exists
  if (localValue.value && newVal !== oldVal) {
    overseerrValidated.value = false
    traktValidated.value = false
    isTestingOverseerr.value = false
    isTestingTrakt.value = false
    // Clear ALL errors for this field
    emit('clearError', 'overseerr_url')
    emit('clearError', 'overseerr_api_key')
    emit('clearError', 'trakt_client_id')
  }
}, { immediate: false })

// Test Overseerr connection
const testOverseerr = async () => {
  // Get fresh values directly from the input (don't rely on cached localValue)
  const url = localValue.value.overseerr_url?.trim()
  const apiKey = localValue.value.overseerr_api_key?.trim()
  
  // Validate that we have required fields
  if (!url || !apiKey) {
    return false
  }
  
  // Reset state before testing
  isTestingOverseerr.value = true
  overseerrValidated.value = false
  
  try {
    // Use fresh values directly - ensure we're not using stale data
    console.log('Testing Overseerr with URL:', url, 'API Key:', apiKey ? '***' : 'MISSING')
    const result: any = await api.testOverseerrConnection({
      overseerr_url: url,
      overseerr_api_key: apiKey,
    })
    
    if (result.valid) {
      overseerrValidated.value = true
      console.log('Overseerr validation successful')
      return true
    } else {
      overseerrValidated.value = false
      console.error('Overseerr validation failed:', result.error)
      showError('Overseerr Connection Failed', result.error || 'Could not connect to Overseerr')
      return false
    }
  } catch (error: any) {
    overseerrValidated.value = false
    console.error('Overseerr test error:', error)
    showError('Overseerr Connection Failed', error.message || 'Failed to test Overseerr connection')
    return false
  } finally {
    isTestingOverseerr.value = false
  }
}

// Test Trakt Client ID
const testTrakt = async () => {
  // Get fresh value directly from the input (don't rely on cached localValue)
  const traktId = localValue.value.trakt_client_id?.trim()
  
  // Validate that we have required fields
  if (!traktId) {
    return false
  }
  
  // Reset state before testing
  isTestingTrakt.value = true
  traktValidated.value = false
  
  try {
    // Use fresh value directly - ensure we're not using stale data
    console.log('Testing Trakt with Client ID:', traktId ? '***' : 'MISSING')
    const result: any = await api.testTraktClientId({
      trakt_client_id: traktId,
    })
    
    if (result.valid) {
      traktValidated.value = true
      console.log('Trakt validation successful')
      return true
    } else {
      traktValidated.value = false
      console.error('Trakt validation failed:', result.error)
      showError('Trakt Validation Failed', result.error || 'Invalid Trakt Client ID')
      return false
    }
  } catch (error: any) {
    traktValidated.value = false
    console.error('Trakt test error:', error)
    showError('Trakt Validation Failed', error.message || 'Failed to validate Trakt Client ID')
    return false
  } finally {
    isTestingTrakt.value = false
  }
}

// Handle next button click - always validate before proceeding
const handleNext = async () => {
  // Get fresh values directly from inputs to ensure we're using current data
  const url = localValue.value.overseerr_url?.trim()
  const apiKey = localValue.value.overseerr_api_key?.trim()
  const traktId = localValue.value.trakt_client_id?.trim()
  
  // Clear ALL previous validation errors and state first
  emit('clearError', 'overseerr_url')
  emit('clearError', 'overseerr_api_key')
  emit('clearError', 'trakt_client_id')
  
  // Reset ALL validation state before testing
  overseerrValidated.value = false
  traktValidated.value = false
  isTestingOverseerr.value = false
  isTestingTrakt.value = false
  
  // Validate all required fields are filled
  if (!url || !apiKey || !traktId) {
    showError('Validation Failed', 'Please fill in all required fields.')
    return
  }
  
  console.log('Starting validation with fresh values:', {
    url,
    apiKey: apiKey ? '***' : 'MISSING',
    traktId: traktId ? '***' : 'MISSING'
  })
  
  // Always validate both APIs when clicking Continue
  // Use fresh values - test functions will get them directly from localValue
  const overseerrResult = await testOverseerr()
  const traktResult = await testTrakt()
  
  console.log('Validation results:', { overseerrResult, traktResult })
  
  // Only proceed if both are validated
  // The parent component will do a final validation when saving
  if (overseerrResult && traktResult) {
    // Clear any errors before proceeding
    emit('clearError', 'overseerr_url')
    emit('clearError', 'overseerr_api_key')
    emit('clearError', 'trakt_client_id')
    console.log('Both validations passed, proceeding to save')
    emit('next')
  } else {
    // Build specific error message
    let errorMsg = 'Please check your API credentials and try again.'
    if (!overseerrResult && !traktResult) {
      errorMsg = 'Both Overseerr and Trakt validations failed. Please check your credentials.'
    } else if (!overseerrResult) {
      errorMsg = 'Overseerr validation failed. Please check your Overseerr URL and API key.'
    } else if (!traktResult) {
      errorMsg = 'Trakt validation failed. Please check your Trakt Client ID.'
    }
    console.error('Validation failed:', errorMsg)
    showError('Validation Failed', errorMsg)
  }
}
</script>
