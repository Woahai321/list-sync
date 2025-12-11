<template>
  <Card class="glass-card border border-purple-500/30">
    <template #header>
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-foreground">Overseerr Users</h3>
          <p class="text-sm text-muted-foreground mt-1">
            Manage which Overseerr users can request content for each list
          </p>
        </div>
        <Button
          variant="primary"
          :icon="RefreshIcon"
          :loading="usersStore.syncing"
          :disabled="usersStore.loading"
          @click="handleSyncUsers"
        >
          Sync Users
        </Button>
      </div>
    </template>

    <!-- Default User Selection -->
    <div v-if="usersStore.users.length > 0" class="mb-4 p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
      <div class="flex items-start gap-3">
        <component :is="StarIcon" :size="20" class="text-purple-400 flex-shrink-0 mt-0.5" />
        <div class="flex-1">
          <p class="text-sm font-semibold text-purple-400 mb-1">Default User for New Lists</p>
          <p class="text-xs text-muted-foreground mb-3">
            All new lists will request content as this user by default (can be changed per-list)
          </p>
          
          <!-- User Selector Dropdown -->
          <div class="relative">
            <select
              v-model="selectedDefaultUserId"
              @change="handleDefaultUserChange"
              :disabled="isSavingDefaultUser"
              class="w-full pl-14 pr-4 py-3 bg-black/40 border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option
                v-for="user in usersStore.users"
                :key="user.id"
                :value="String(user.id)"
              >
                {{ user.display_name }} (ID: {{ user.id }}){{ user.email ? ` - ${user.email}` : '' }}{{ String(user.id) === '1' ? ' - Admin' : '' }}
              </option>
            </select>
            
            <!-- Avatar overlay on the left -->
            <div class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full overflow-hidden bg-purple-500/20 border-2 border-purple-500/30 pointer-events-none">
              <img
                v-if="selectedUser"
                :src="getAvatarUrl(selectedUser.avatar, selectedUser)"
                :alt="selectedUser.display_name || 'Selected User'"
                class="w-full h-full object-cover"
                @error="handleImageError"
              />
            </div>
            
            <!-- Dropdown arrow -->
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <ChevronDownIcon class="w-4 h-4 text-muted-foreground" />
            </div>
          </div>
          
          <!-- Saving indicator -->
          <div v-if="isSavingDefaultUser" class="flex items-center gap-2 mt-2 text-xs text-purple-400">
            <div class="w-3 h-3 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
            Saving...
          </div>
          
          <!-- Success message -->
          <div v-else-if="defaultUserSaveSuccess" class="flex items-center gap-2 mt-2 text-xs text-green-400">
            <CheckCircleIcon class="w-4 h-4" />
            Default user saved successfully
          </div>
        </div>
      </div>
    </div>

    <!-- Last Synced Info -->
    <div v-if="usersStore.lastSynced" class="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
      <ClockIcon class="w-4 h-4" />
      <span>Last synced: {{ formatDate(usersStore.lastSynced) }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="usersStore.loading && usersStore.users.length === 0" class="flex items-center justify-center py-12">
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mb-4"></div>
        <p class="text-muted-foreground">Loading users...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="usersStore.error" class="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
      <AlertCircleIcon class="w-5 h-5 text-red-400 flex-shrink-0" />
      <div class="flex-1">
        <p class="text-sm font-medium text-red-400">Error loading users</p>
        <p class="text-xs text-red-300/70 mt-1">{{ usersStore.error }}</p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        @click="handleSyncUsers"
      >
        Retry
      </Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="usersStore.users.length === 0" class="text-center py-12">
      <UsersIcon class="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
      <p class="text-muted-foreground mb-4">No users found</p>
      <Button
        variant="primary"
        :icon="RefreshIcon"
        @click="handleSyncUsers"
      >
        Sync Users from Overseerr
      </Button>
    </div>

    <!-- Users Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="user in usersStore.users"
        :key="user.id"
        :data-user-id="user.id"
        :data-user-name="user.display_name"
        class="flex items-center gap-3 p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg hover:border-purple-500/40 transition-colors"
      >
        <!-- Avatar -->
        <div class="flex-shrink-0">
          <div
            class="w-12 h-12 rounded-full overflow-hidden bg-purple-500/20 border-2 border-purple-500/30"
          >
            <img
              :src="getAvatarUrl(user.avatar, user)"
              :alt="user.display_name"
              class="w-full h-full object-cover"
              @error="handleImageError"
            />
          </div>
        </div>

        <!-- User Info -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-foreground truncate">
            {{ user.display_name }}
          </p>
          <p v-if="user.email" class="text-xs text-muted-foreground truncate">
            {{ user.email }}
          </p>
          <p class="text-xs text-purple-400/70 mt-1">
            ID: {{ user.id }}
          </p>
        </div>

        <!-- Admin Badge for User 1 -->
        <div v-if="user.id === '1'" class="flex-shrink-0">
          <span class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-purple-500/20 text-purple-300 rounded-md border border-purple-500/30">
            <ShieldIcon class="w-3 h-3" />
            Admin
          </span>
        </div>
      </div>
    </div>

    <!-- User Count -->
    <div v-if="usersStore.users.length > 0" class="mt-4 pt-4 border-t border-purple-500/20">
      <p class="text-sm text-muted-foreground text-center">
        Total: <span class="font-semibold text-foreground">{{ usersStore.users.length }}</span> user{{ usersStore.users.length !== 1 ? 's' : '' }}
      </p>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Users as UsersIcon,
  User as UserIcon,
  Clock as ClockIcon,
  AlertCircle as AlertCircleIcon,
  Shield as ShieldIcon,
  Star as StarIcon,
  ChevronDown as ChevronDownIcon,
  CheckCircle as CheckCircleIcon,
} from 'lucide-vue-next'
import { useUsersStore } from '~/stores/users'

const { showSuccess, showError } = useToast()
const usersStore = useUsersStore()
const api = useApiService()

// Overseerr base URL for converting relative avatar URLs
const overseerrBaseUrl = ref<string | null>(null)

// Default user ID from config
const defaultUserId = ref<string | null>(null)

// Selected default user ID (for the dropdown)
const selectedDefaultUserId = ref<string>('1')

// Saving state for default user
const isSavingDefaultUser = ref(false)
const defaultUserSaveSuccess = ref(false)

// Computed property to get the default user object (legacy, kept for compatibility)
const defaultUser = computed(() => {
  if (!defaultUserId.value) return null
  return usersStore.users.find(user => String(user.id) === String(defaultUserId.value))
})

// Computed property to get the selected user object for the dropdown
const selectedUser = computed(() => {
  if (!selectedDefaultUserId.value) return null
  return usersStore.users.find(user => String(user.id) === String(selectedDefaultUserId.value))
})

// Fetch Overseerr base URL and default user on mount
onMounted(async () => {
  // Fetch Overseerr config to get base URL and default user
  try {
    const config = await api.getConfig()
    overseerrBaseUrl.value = config.overseerr_url || null
    defaultUserId.value = config.overseerr_user_id || '1'
    selectedDefaultUserId.value = config.overseerr_user_id || '1'
  } catch (error) {
    console.error('Failed to load Overseerr URL from config:', error)
  }
  
  await usersStore.fetchUsers()
  
  // Only auto-sync if no users AND it's been a while since setup
  // (Users should be pre-populated during wizard, so empty state means they need a refresh)
  if (usersStore.users.length === 0 && !usersStore.error) {
    // Check if we should auto-sync (don't spam the API)
    const shouldAutoSync = !usersStore.lastSynced || 
      (new Date().getTime() - new Date(usersStore.lastSynced).getTime() > 60000) // 1 minute
    
    if (shouldAutoSync) {
      await handleSyncUsers()
    }
  }
})

// Sync users from Overseerr
const handleSyncUsers = async () => {
  try {
    const result = await usersStore.syncUsers()
    showSuccess('Users Synced', `Successfully synced ${result.count} user${result.count !== 1 ? 's' : ''} from Overseerr`)
  } catch (error: any) {
    showError('Sync Failed', error.message || 'Failed to sync users from Overseerr')
  }
}

// Handle default user selection change
const handleDefaultUserChange = async () => {
  if (!selectedDefaultUserId.value) return
  
  isSavingDefaultUser.value = true
  defaultUserSaveSuccess.value = false
  
  try {
    // Get current config
    const config = await api.getConfig()
    
    // Update with new default user ID
    await api.updateConfig({
      overseerr_user_id: selectedDefaultUserId.value,
    })
    
    // Update local state
    defaultUserId.value = selectedDefaultUserId.value
    
    // Show success message briefly
    defaultUserSaveSuccess.value = true
    setTimeout(() => {
      defaultUserSaveSuccess.value = false
    }, 3000)
    
    console.log('[UsersManagement] Default user updated to:', selectedDefaultUserId.value)
  } catch (error: any) {
    console.error('Failed to save default user:', error)
    showError('Save Failed', error.message || 'Failed to save default user')
    // Revert selection on error
    selectedDefaultUserId.value = defaultUserId.value || '1'
  } finally {
    isSavingDefaultUser.value = false
  }
}

// Format date for display
const formatDate = (date: Date | string) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString()
}

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

// Convert relative avatar URL to full URL using Overseerr base URL, or use DiceBear as fallback
const getAvatarUrl = (avatar: string | null | undefined, user: { id: string; display_name: string }): string => {
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
    
    // If relative URL and we have base URL, convert to full URL
    if (overseerrBaseUrl.value && avatar.startsWith('/')) {
      const cleanBaseUrl = overseerrBaseUrl.value.replace(/\/$/, '')
      return `${cleanBaseUrl}${avatar}`
    }
  }
  
  // Fallback to DiceBear - prefer display_name or email for better initials, then ID
  const seed = user.display_name || user.email || user.id || 'user'
  return getDiceBearAvatar(seed)
}

// Handle image load errors - fallback to DiceBear if Overseerr avatar fails
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  const userCard = img.closest('[data-user-id]')
  if (userCard) {
    const displayName = userCard.getAttribute('data-user-name')
    const userId = userCard.getAttribute('data-user-id')
    // Prefer display name for better initials, fallback to ID
    const seed = displayName || userId || 'user'
    // Fallback to DiceBear if image fails to load
    img.src = getDiceBearAvatar(seed)
  }
}
</script>

