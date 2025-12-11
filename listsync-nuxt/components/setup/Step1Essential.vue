<template>
  <div class="space-y-3 sm:space-y-4 relative" role="region" aria-labelledby="step1-heading">
    <!-- Step Header -->
    <div class="text-center mb-3 sm:mb-4 animate-fade-in">
      <h2 id="step1-heading" class="text-lg sm:text-xl font-bold text-foreground mb-1.5 titillium-web-bold">
        Connect to Overseerr
      </h2>
      <p class="text-xs sm:text-sm text-muted-foreground max-w-xl mx-auto">
        Link your Overseerr instance and select the default user for managing your lists.
      </p>
    </div>

    <!-- Overseerr Section -->
    <div class="p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-2.5 sm:space-y-3" role="group" aria-labelledby="overseerr-section">
      <div class="flex items-center gap-2">
        <component :is="ServerIcon" :size="16" class="text-purple-400" aria-hidden="true" />
        <span id="overseerr-section" class="text-xs font-bold text-purple-300 uppercase tracking-wide">Overseerr</span>
      </div>
      
      <div>
        <label for="overseerr-url" class="text-xs font-semibold text-foreground mb-1.5 block">
          URL
          <span class="text-red-400 ml-1" aria-label="required">*</span>
        </label>
        <Input
          id="overseerr-url"
          v-model="localValue.overseerr_url"
          type="url"
          placeholder="https://overseerr.example.com"
          :icon="GlobeIcon"
          :disabled="isValidating"
          aria-required="true"
          aria-describedby="overseerr-url-error"
        />
        <p v-if="errors.overseerr_url" id="overseerr-url-error" class="text-xs text-red-400 mt-1.5 flex items-center gap-1.5 animate-fade-in" role="alert">
          <component :is="AlertCircleIcon" :size="14" aria-hidden="true" />
          {{ errors.overseerr_url }}
        </p>
      </div>

      <div>
        <label for="overseerr-api-key" class="text-xs font-semibold text-foreground mb-1.5 block">
          API Key
          <span class="text-red-400 ml-1" aria-label="required">*</span>
        </label>
        <Input
          id="overseerr-api-key"
          v-model="localValue.overseerr_api_key"
          type="password"
          placeholder="••••••••••••••••"
          :icon="KeyIcon"
          :disabled="isValidating || isTestingOverseerr"
          aria-required="true"
          aria-describedby="overseerr-api-key-status"
        />
        <p v-if="errors.overseerr_api_key" id="overseerr-api-key-status" class="text-xs text-red-400 mt-1.5 flex items-center gap-1.5 animate-fade-in" role="alert">
          <component :is="AlertCircleIcon" :size="14" aria-hidden="true" />
          {{ errors.overseerr_api_key }}
        </p>
        <p v-else-if="overseerrValidated" id="overseerr-api-key-status" class="text-xs text-green-400 mt-1.5 flex items-center gap-1.5 animate-fade-in" role="status">
          <component :is="CheckCircleIcon" :size="14" aria-hidden="true" />
          <span class="font-medium">Connected & Credentials Saved</span>
        </p>
      </div>
    </div>

    <!-- User Configuration Section -->
    <div class="p-3 sm:p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/25 space-y-2.5 sm:space-y-3" role="group" aria-labelledby="user-section">
      <div class="flex items-center gap-2">
        <component :is="UsersIcon" :size="16" class="text-purple-400" aria-hidden="true" />
        <span id="user-section" class="text-xs font-bold text-purple-300 uppercase tracking-wide">Default User</span>
      </div>
      
      <!-- Sync Users Button -->
      <div v-if="!overseerrValidated && !isFetchingUsers && fetchedUsers.length === 0" class="text-center py-4">
        <Button
          variant="primary"
          :icon="RefreshIcon"
          :loading="isFetchingUsers || isTestingOverseerr"
          @click="handleSyncUsers"
          class="min-w-[220px] shadow-lg shadow-purple-500/20 hover:shadow-purple-500/30 transition-all"
          :aria-label="'Test connection and sync users from Overseerr'"
        >
          {{ (isFetchingUsers || isTestingOverseerr) ? 'Connecting...' : 'Test Connection & Sync Users' }}
        </Button>
        <p class="text-xs text-muted-foreground mt-3">
          Click to verify your credentials and load available users
        </p>
      </div>
      
      <!-- Loading State -->
      <div v-else-if="isFetchingUsers" class="grid grid-cols-3 gap-2 sm:gap-3">
        <div 
          v-for="i in 3" 
          :key="`skeleton-${i}`" 
          class="p-3 rounded-lg border-2 border-purple-500/20 bg-purple-500/5 animate-pulse"
        >
          <div class="flex items-center gap-2 mb-1.5">
            <!-- Avatar skeleton -->
            <div class="w-10 h-10 rounded-full bg-purple-500/20 border-2 border-purple-500/30 flex-shrink-0"></div>
            <div class="flex-1 min-w-0 space-y-2">
              <!-- Name skeleton -->
              <div class="h-3 bg-purple-500/20 rounded w-3/4"></div>
              <!-- ID skeleton -->
              <div class="h-2 bg-purple-500/15 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- User Cards -->
      <div v-else-if="fetchedUsers.length > 0" class="space-y-2">
        <div class="grid grid-cols-3 gap-2 sm:gap-3">
          <button
            v-for="user in paginatedUsers"
            :key="user.id"
            type="button"
            @click="selectedUserId = String(user.id)"
            :class="[
              'p-3 rounded-lg text-left transition-all duration-200 group relative overflow-hidden',
              String(selectedUserId) === String(user.id)
                ? 'border-2 border-green-500 bg-green-500/10 scale-105 shadow-lg shadow-green-500/20'
                : 'border-2 border-purple-500/20 bg-purple-500/5 hover:border-purple-400/40 hover:bg-purple-500/10 hover:scale-105 hover:shadow-lg hover:shadow-purple-500/20'
            ]"
          >
            <!-- Hover effect overlay -->
            <div 
              class="absolute inset-0 bg-gradient-to-br from-purple-400/0 via-purple-400/5 to-purple-400/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              aria-hidden="true"
            />
            
            <!-- Selected indicator -->
            <div
              v-if="String(selectedUserId) === String(user.id)"
              class="absolute top-1 right-1 w-5 h-5 rounded-full bg-green-500 flex items-center justify-center animate-scale-in"
            >
              <component :is="CheckCircleIcon" :size="14" class="text-white" />
            </div>
            
            <div class="flex items-center gap-2 mb-1.5 relative">
              <div 
                :class="[
                  'w-10 h-10 rounded-full overflow-hidden border-2 flex-shrink-0 transition-all duration-200',
                  String(selectedUserId) === String(user.id) 
                    ? 'border-green-500 shadow-md shadow-green-500/30' 
                    : 'border-purple-500/30 group-hover:border-purple-400/50'
                ]"
              >
                <img
                  :src="getAvatarUrl(user)"
                  :alt="user.display_name"
                  class="w-full h-full object-cover"
                  @error="(e) => {
                    const target = e.target as HTMLImageElement
                    target.src = getDiceBearAvatar(user.display_name || user.id)
                  }"
                />
              </div>
              <div class="flex-1 min-w-0">
                <p 
                  :class="[
                    'text-xs sm:text-sm font-semibold truncate leading-tight transition-colors duration-200',
                    String(selectedUserId) === String(user.id) ? 'text-green-300' : 'text-foreground group-hover:text-purple-300'
                  ]"
                >
                  {{ user.display_name }}
                </p>
                <p class="text-[10px] sm:text-xs text-muted-foreground mt-0.5">ID: {{ user.id }}</p>
              </div>
            </div>
          </button>
        </div>
        
        <!-- Pagination -->
        <div v-if="hasMoreUsers" class="flex items-center justify-center gap-3 pt-3 text-xs sm:text-sm">
          <Button
            variant="ghost"
            size="sm"
            :disabled="currentUserPage === 0"
            @click="currentUserPage--"
            class="h-8 sm:h-9 px-3 min-w-[80px] sm:min-w-[90px] transition-all hover:scale-105"
            :aria-label="'Previous page'"
          >
            <component :is="ChevronLeftIcon" :size="16" class="mr-1" />
            Previous
          </Button>
          
          <span class="text-muted-foreground font-medium px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 min-w-[60px] text-center">
            {{ currentUserPage + 1 }} / {{ totalUserPages }}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            :disabled="currentUserPage >= totalUserPages - 1"
            @click="currentUserPage++"
            class="h-8 sm:h-9 px-3 min-w-[80px] sm:min-w-[90px] transition-all hover:scale-105"
            :aria-label="'Next page'"
          >
            Next
            <component :is="ChevronRightIcon" :size="16" class="ml-1" />
          </Button>
        </div>
      </div>
      
      <!-- Error State -->
      <div v-if="usersFetchError" class="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex flex-col items-center gap-3 animate-fade-in">
        <div class="flex items-center gap-2 text-red-400">
          <component :is="AlertCircleIcon" :size="20" class="flex-shrink-0" aria-hidden="true" />
          <p class="text-sm font-medium">{{ usersFetchError }}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          :icon="RefreshIcon"
          @click="handleSyncUsers"
          class="text-xs h-8 px-4"
          aria-label="Retry fetching users"
        >
          Retry
        </Button>
      </div>
      
      <!-- Empty State (no users found) -->
      <div 
        v-else-if="!isFetchingUsers && fetchedUsers.length === 0 && overseerrValidated" 
        class="p-6 rounded-lg bg-purple-500/10 border border-purple-500/20 flex flex-col items-center gap-3 text-center animate-fade-in"
      >
        <component :is="UsersIcon" :size="32" class="text-purple-400/60" aria-hidden="true" />
        <div>
          <p class="text-sm font-medium text-foreground mb-1">No Users Found</p>
          <p class="text-xs text-muted-foreground">
            We couldn't find any users from your Overseerr instance.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          :icon="RefreshIcon"
          @click="handleSyncUsers"
          class="text-xs h-8 px-4"
          aria-label="Retry syncing users"
        >
          Try Again
        </Button>
      </div>
    </div>

    <!-- Action Button -->
    <div class="flex justify-end pt-2 sm:pt-3">
      <div class="relative w-full sm:w-auto">
        <Button
          variant="primary"
          :loading="isValidating || isTestingOverseerr"
          :disabled="!canProceed"
          @click="handleNext"
          class="w-full sm:w-auto"
          :aria-label="canProceed ? 'Continue to next step' : 'Complete all requirements to continue'"
        >
          {{ (isValidating || isTestingOverseerr) ? 'Validating...' : 'Continue' }}
        </Button>
        
        <!-- Tooltip for disabled state -->
        <Tooltip 
          v-if="!canProceed && !isValidating && !isTestingOverseerr"
          content="Please test your connection and select a user to continue"
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
  Globe as GlobeIcon,
  Key as KeyIcon,
  Server as ServerIcon,
  CheckCircle as CheckCircleIcon,
  HelpCircle as HelpCircleIcon,
  AlertCircle as AlertCircleIcon,
  Users as UsersIcon,
  RefreshCw as RefreshIcon,
  Info as InfoIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: {
    overseerr_url: string
    overseerr_api_key: string
    overseerr_user_id: string
  }
  isValidating: boolean
  errors: Record<string, string>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'next', 'clearError'])

const { showSuccess, showError } = useToast()
const api = useApiService()

const localValue = computed({
  get: () => {
    // Ensure we always return a valid object
    if (!props.modelValue) {
      return {
        overseerr_url: '',
        overseerr_api_key: '',
        overseerr_user_id: '1',
      }
    }
    // Ensure all required properties exist
    return {
      overseerr_url: props.modelValue.overseerr_url || '',
      overseerr_api_key: props.modelValue.overseerr_api_key || '',
      overseerr_user_id: props.modelValue.overseerr_user_id || '1',
    }
  },
  set: (value) => {
    if (value) {
      emit('update:modelValue', value)
    }
  }
})

// Validation state
const isTestingOverseerr = ref(false)
const overseerrValidated = ref(false)
const overseerrUserInfo = ref<any>(null)

// Users state
const fetchedUsers = ref<any[]>([])
const selectedUserId = ref('1')
const isFetchingUsers = ref(false)
const usersFetchError = ref('')
const usersPerPage = 3
const currentUserPage = ref(0)

// Paginated users
const paginatedUsers = computed(() => {
  const start = currentUserPage.value * usersPerPage
  const end = start + usersPerPage
  return fetchedUsers.value.slice(start, end)
})

const totalUserPages = computed(() => {
  return Math.ceil(fetchedUsers.value.length / usersPerPage)
})

const hasMoreUsers = computed(() => {
  return fetchedUsers.value.length > usersPerPage
})

// Track if component is mounted to prevent watchers from firing during initialization
const isMounted = ref(false)

// Validation steps tracking
const validationSteps = ref({
  overseerr: {
    connecting: 'idle' as 'idle' | 'loading' | 'success' | 'error',
    fetchingUser: 'idle' as 'idle' | 'loading' | 'success' | 'error',
  }
})

// Mark as mounted after initial setup
onMounted(() => {
  // Small delay to ensure all props are initialized
  nextTick(() => {
    isMounted.value = true
  })
})

// Check if we can fetch users (URL and API key are filled)
const canFetchUsers = computed(() => {
  if (!localValue.value) return false
  const hasUrl = !!(localValue.value.overseerr_url || '').trim()
  const hasApiKey = !!(localValue.value.overseerr_api_key || '').trim()
  return hasUrl && hasApiKey
})

// Check if we can proceed (all fields filled and user selected)
const canProceed = computed(() => {
  // Since credentials are saved during the "Test Connection & Sync Users" step,
  // we just need to verify that:
  // 1. Connection was validated (overseerrValidated = true)
  // 2. Users were fetched
  // 3. A user is selected
  
  const hasValidatedConnection = overseerrValidated.value
  const hasUsers = fetchedUsers.value.length > 0
  const hasSelectedUser = !!(selectedUserId.value || '1').trim()
  
  return hasValidatedConnection && hasUsers && hasSelectedUser
})

// Clean seed string by removing emojis and keeping only letters, numbers, and spaces
const cleanSeedForInitials = (text: string): string => {
  if (!text) return 'User'
  
  // Remove emojis and special characters, keep only letters, numbers, and spaces
  // This regex keeps: a-z, A-Z, 0-9, and spaces
  const cleaned = text.replace(/[^a-zA-Z0-9\s]/g, '').trim()
  
  // If we have cleaned text, use it; otherwise extract first available character
  if (cleaned.length > 0) {
    return cleaned
  }
  
  // If no letters/numbers found, try to extract first character
  const firstChar = text.match(/[a-zA-Z0-9]/)
  return firstChar ? firstChar[0].toUpperCase() : 'User'
}

// Generate DiceBear avatar URL with initials and purple background
const getDiceBearAvatar = (seed: string): string => {
  // Clean the seed to remove emojis and special characters
  const cleanSeed = cleanSeedForInitials(seed)
  const encodedSeed = encodeURIComponent(cleanSeed)
  // Purple color matching the app theme (purple-600: #9333ea)
  const backgroundColor = '9333ea'
  return `https://api.dicebear.com/7.x/initials/svg?seed=${encodedSeed}&backgroundColor=${backgroundColor}`
}

// Get avatar URL - use Overseerr avatar if available, otherwise DiceBear
// Handles both full URLs and relative URLs (converts relative to full using Overseerr base URL)
const getAvatarUrl = (user: any): string => {
  const avatar = user.avatar
  
  // If we have an avatar, try to use it
  if (avatar) {
    // Already proxied through our API cache
    if (avatar.startsWith('/api/images/proxy')) {
      return avatar
    }

    // If already a full URL (starts with http:// or https://), use as-is
    if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
      return avatar
    }
    
    // If relative URL and we have Overseerr URL, convert to full URL
    const overseerrUrl = localValue.value?.overseerr_url
    if (overseerrUrl && avatar.startsWith('/')) {
      const cleanBaseUrl = overseerrUrl.replace(/\/$/, '')
      return `${cleanBaseUrl}${avatar}`
    }
  }
  
  // Fallback to DiceBear - prefer display_name or email for better initials, then username/ID
  const seed = user.display_name || user.displayName || user.email || user.username || user.id || 'user'
  return getDiceBearAvatar(seed)
}

// Fetch users from Overseerr
const fetchOverseerrUsers = async () => {
  if (!localValue.value) {
    console.warn('Cannot fetch users: localValue is not initialized')
    return
  }
  
  isFetchingUsers.value = true
  usersFetchError.value = ''
  
  try {
    console.log('Fetching Overseerr users...')
    const response: any = await api.syncOverseerrUsers()
    
    console.log('Users sync response:', response)
    
    if (response && response.success && response.users && Array.isArray(response.users)) {
      fetchedUsers.value = response.users
      console.log(`Fetched ${response.users.length} users:`, response.users)
      
      // Default to user ID 1 if it exists, otherwise first user
      const hasUserOne = response.users.some((u: any) => String(u.id) === '1')
      if (hasUserOne) {
        selectedUserId.value = '1'
      } else if (response.users.length > 0) {
        selectedUserId.value = String(response.users[0].id)
      }
      
      // Update the form value with selected user
      if (localValue.value) {
        localValue.value.overseerr_user_id = selectedUserId.value
        console.log('Set default user ID:', selectedUserId.value)
      }
    } else {
      console.warn('Invalid response format:', response)
      usersFetchError.value = 'Invalid response from server'
    }
  } catch (error: any) {
    console.error('Failed to fetch users:', error)
    usersFetchError.value = error.message || error.detail || 'Failed to fetch users'
    // Set default user on error
    selectedUserId.value = '1'
    if (localValue.value) {
      localValue.value.overseerr_user_id = '1'
    }
  } finally {
    isFetchingUsers.value = false
  }
}

// Watch selected user to update form value
watch(selectedUserId, (newUserId) => {
  if (localValue.value && newUserId) {
    localValue.value.overseerr_user_id = String(newUserId)
    console.log('User selected, updated form value:', newUserId)
  }
})

// Reset validation steps
const resetValidationSteps = () => {
  validationSteps.value = {
    overseerr: {
      connecting: 'idle',
      fetchingUser: 'idle',
    }
  }
}

// Reset validation state and clear errors when values change
// IMPORTANT: Reset ALL validation state when ANY input changes to ensure fresh validation
watch(() => {
  // Safely access the value with proper null checking
  return localValue.value?.overseerr_url
}, (newVal, oldVal) => {
  // Only reset if component is mounted, value actually changed, and localValue exists
  if (!isMounted.value) return
  if (!localValue.value) return
  if (newVal === oldVal) return
  if (oldVal === undefined) return // Skip initial mount
  
  overseerrValidated.value = false
  fetchedUsers.value = []
  isTestingOverseerr.value = false
  resetValidationSteps()
  
  // Clear errors safely
  if (typeof emit === 'function') {
    nextTick(() => {
      try {
        emit('clearError', 'overseerr_url')
        emit('clearError', 'overseerr_api_key')
      } catch (e) {
        // Silently ignore if handler not ready
        console.debug('clearError handler not ready:', e)
      }
    })
  }
}, { immediate: false })

watch(() => {
  // Safely access the value with proper null checking
  return localValue.value?.overseerr_api_key
}, (newVal, oldVal) => {
  // Only reset if component is mounted, value actually changed, and localValue exists
  if (!isMounted.value) return
  if (!localValue.value) return
  if (newVal === oldVal) return
  if (oldVal === undefined) return // Skip initial mount
  
  overseerrValidated.value = false
  fetchedUsers.value = []
  isTestingOverseerr.value = false
  resetValidationSteps()
  
  // Clear errors safely
  if (typeof emit === 'function') {
    nextTick(() => {
      try {
        emit('clearError', 'overseerr_url')
        emit('clearError', 'overseerr_api_key')
      } catch (e) {
        // Silently ignore if handler not ready
        console.debug('clearError handler not ready:', e)
      }
    })
  }
}, { immediate: false })

// Handle sync users button click
const handleSyncUsers = async () => {
  // Validate fields are filled
  const url = localValue.value?.overseerr_url?.trim() || ''
  const apiKey = localValue.value?.overseerr_api_key?.trim() || ''
  
  if (!url || !apiKey) {
    const missing = []
    if (!url) missing.push('Overseerr URL')
    if (!apiKey) missing.push('API Key')
    showError('Missing Information', `Please enter: ${missing.join(' and ')}`)
    return
  }
  
  // First validate the connection, then fetch users
  const isValid = await testOverseerr()
  
  if (!isValid) {
    showError('Connection Failed', 'Please check your Overseerr URL and API Key')
  }
}

// Test Overseerr connection
const testOverseerr = async () => {
  // Get fresh values directly from the input (don't rely on cached localValue)
  if (!localValue.value) return false
  
  // Safely access properties with fallbacks
  const url = (localValue.value.overseerr_url || '').trim()
  const apiKey = (localValue.value.overseerr_api_key || '').trim()
  const userId = (localValue.value.overseerr_user_id || '1').trim()
  
  // Validate that we have required fields
  if (!url || !apiKey) {
    return false
  }
  
  // Reset state before testing
  isTestingOverseerr.value = true
  overseerrValidated.value = false
  overseerrUserInfo.value = null
  validationSteps.value.overseerr.connecting = 'loading'
  validationSteps.value.overseerr.fetchingUser = 'idle'
  
  try {
    // Use fresh values directly - ensure we're not using stale data
    console.log('Testing Overseerr with URL:', url, 'API Key:', apiKey ? '***' : 'MISSING')
    
    const result: any = await api.testOverseerrConnection({
      overseerr_url: url,
      overseerr_api_key: apiKey,
      overseerr_user_id: userId,
    })
    
    if (result.valid) {
      validationSteps.value.overseerr.connecting = 'success'
      validationSteps.value.overseerr.fetchingUser = 'loading'
      
      // CRITICAL FIX: Save credentials to config BEFORE trying to sync users
      // The sync users endpoint needs these to be in the database
      console.log('Saving credentials to config before syncing users...')
      try {
        await api.updateConfig({
          overseerr_url: url,
          overseerr_api_key: apiKey,
          overseerr_user_id: userId,
        })
        console.log('Credentials saved to config successfully')
      } catch (saveError: any) {
        console.error('Failed to save credentials:', saveError)
        throw new Error('Failed to save credentials: ' + saveError.message)
      }
      
      // Small delay to ensure database write completes
      await new Promise(resolve => setTimeout(resolve, 300))
      
      validationSteps.value.overseerr.fetchingUser = 'success'
      overseerrValidated.value = true
      
      console.log('Overseerr validation successful, now fetching users...')
      
      // Now fetch users - credentials are in database so sync endpoint will work
      await fetchOverseerrUsers()
      
      return true
    } else {
      validationSteps.value.overseerr.connecting = 'error'
      validationSteps.value.overseerr.fetchingUser = 'error'
      overseerrValidated.value = false
      console.error('Overseerr validation failed:', result.error)
      showError('Overseerr Connection Failed', result.error || 'Could not connect to Overseerr')
      return false
    }
  } catch (error: any) {
    validationSteps.value.overseerr.connecting = 'error'
    validationSteps.value.overseerr.fetchingUser = 'error'
    overseerrValidated.value = false
    console.error('Overseerr test error:', error)
    showError('Overseerr Connection Failed', error.message || 'Failed to test Overseerr connection')
    return false
  } finally {
    isTestingOverseerr.value = false
  }
}

// Handle next button click - always validate before proceeding
const handleNext = async () => {
  // Get fresh values directly from inputs to ensure we're using current data
  if (!localValue.value) {
    showError('Error', 'Form data is not available')
    return
  }
  
  // Safely access properties with fallbacks
  const url = (localValue.value.overseerr_url || '').trim()
  const apiKey = (localValue.value.overseerr_api_key || '').trim()
  
  // Clear ALL previous validation errors and state first
  emit('clearError', 'overseerr_url')
  emit('clearError', 'overseerr_api_key')
  
  // Reset ALL validation state before testing
  overseerrValidated.value = false
  overseerrUserInfo.value = null
  isTestingOverseerr.value = false
  resetValidationSteps()
  
  // Validate all required fields are filled
  if (!url || !apiKey) {
    showError('Validation Failed', 'Please fill in all required fields.')
    return
  }
  
  console.log('Starting validation with fresh values:', {
    url,
    apiKey: apiKey ? '***' : 'MISSING'
  })
  
  // Always validate Overseerr when clicking Continue
  // Use fresh values - test function will get them directly from localValue
  const overseerrResult = await testOverseerr()
  
  console.log('Validation results:', { overseerrResult })
  
  // Only proceed if Overseerr is validated
  // The parent component will do a final validation when saving
  if (overseerrResult) {
    // Clear any errors before proceeding
    emit('clearError', 'overseerr_url')
    emit('clearError', 'overseerr_api_key')
    console.log('Validation passed, proceeding to next step')
    
    // No need to wait - user has already selected their default user
    // Proceed immediately
    emit('next')
  } else {
    // Build specific error message
    const errorMsg = 'Overseerr validation failed. Please check your Overseerr URL and API key.'
    console.error('Validation failed:', errorMsg)
    showError('Validation Failed', errorMsg)
  }
}
</script>

<style scoped>
/* Pulse animation for user info card */
@keyframes user-info-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

.user-info-pulse {
  animation: user-info-pulse 1.5s ease-in-out infinite;
}
</style>
