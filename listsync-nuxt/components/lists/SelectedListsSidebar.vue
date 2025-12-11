<template>
  <div class="flex flex-col h-full bg-black/40 border-l border-purple-500/20 overflow-hidden max-w-full">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-purple-500/20 bg-purple-500/5">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-bold text-foreground">Selected Lists</h3>
        <span 
          :class="[
            'text-sm font-bold px-3 py-1 rounded-full transition-all',
            lists.length > 0 
              ? 'bg-purple-500 text-white' 
              : 'bg-white/10 text-muted-foreground'
          ]"
        >
          {{ lists.length }}
        </span>
      </div>
    </div>

    <!-- Lists -->
    <div class="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-2.5 min-h-0 custom-scrollbar">
      <div v-if="lists.length === 0" class="text-center py-10">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-purple-500/10 flex items-center justify-center">
          <component :is="ListIcon" :size="28" class="text-purple-400/50" />
        </div>
        <p class="text-sm font-medium text-muted-foreground">No lists added yet</p>
        <p class="text-xs text-muted-foreground/60 mt-1">Select a provider to get started</p>
      </div>
      
      <div
        v-for="(list, index) in lists"
        :key="list.id"
        class="group flex items-center gap-2 p-2.5 rounded-xl bg-black/40 border border-purple-500/20 hover:border-purple-500/40 hover:bg-purple-500/5 transition-all overflow-hidden"
      >
        <div :class="['p-1.5 rounded-lg flex-shrink-0', getSourceBg(list.source || list.listType)]">
          <component :is="getSourceIcon(list.source || list.listType)" :size="14" :class="getSourceColor(list.source || list.listType)" />
        </div>
        <div class="flex-1 min-w-0 overflow-hidden">
          <p class="text-xs font-semibold text-foreground truncate">{{ list.displayName }}</p>
          <p class="text-[10px] text-muted-foreground truncate">{{ formatSource(list.source || list.listType) }}</p>
        </div>
        <button
          v-if="!list.isCurrent"
          @click="$emit('remove', index)"
          class="p-1 rounded-lg flex-shrink-0 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all"
          title="Remove"
        >
          <component :is="XIcon" :size="12" />
        </button>
        <span v-else class="text-[9px] text-purple-400 font-bold px-1.5 py-0.5 rounded-md bg-purple-500/20 uppercase tracking-wide flex-shrink-0">
          current
        </span>
      </div>
    </div>

    <!-- Configuration Section -->
    <div class="border-t border-purple-500/20 p-4 space-y-4 bg-black/20">
      <!-- User Selection -->
      <div class="space-y-3">
        <label class="flex items-center gap-2 text-sm font-semibold text-foreground">
          <component :is="UserIcon" :size="16" class="text-purple-400" />
          Request As
        </label>
        
        <!-- User Card with Avatar -->
        <div 
          v-if="selectedUser" 
          class="relative p-3 rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30"
        >
          <div class="flex items-center gap-2.5">
            <!-- Avatar -->
            <div class="relative flex-shrink-0">
              <div class="w-10 h-10 rounded-full overflow-hidden bg-purple-500/20 border-2 border-purple-500/40 shadow-lg shadow-purple-500/20">
                <img
                  :src="getAvatarUrl(selectedUser)"
                  :alt="selectedUser.display_name"
                  class="w-full h-full object-cover"
                  @error="handleImageError"
                />
              </div>
              <div class="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-green-500 border-2 border-background flex items-center justify-center">
                <component :is="CheckIcon" :size="8" class="text-white" />
              </div>
            </div>
            <!-- User Info -->
            <div class="flex-1 min-w-0 overflow-hidden">
              <p class="text-sm font-bold text-foreground truncate">
                {{ selectedUser.display_name }}
              </p>
            </div>
            <!-- Change Button -->
            <button
              type="button"
              @click="showUserDropdown = !showUserDropdown"
              class="px-2 py-0.5 rounded-lg text-[9px] font-bold uppercase tracking-wide bg-white/10 hover:bg-purple-500/30 text-purple-400 hover:text-purple-300 transition-all flex-shrink-0"
            >
              Change
            </button>
          </div>
        </div>
        
        <!-- User Dropdown (expanded) -->
        <div v-if="showUserDropdown || !selectedUser" class="space-y-2">
          <div class="max-h-40 overflow-y-auto space-y-1.5 custom-scrollbar">
            <button
              v-for="user in users"
              :key="user.id"
              type="button"
              :class="[
                'w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all',
                String(user.id) === selectedUserId
                  ? 'bg-purple-500/20 border-2 border-purple-500'
                  : 'bg-black/30 border border-border hover:border-purple-500/40 hover:bg-purple-500/10'
              ]"
              @click="selectUser(String(user.id))"
            >
              <div class="w-9 h-9 rounded-full overflow-hidden bg-purple-500/20 border border-purple-500/30 flex-shrink-0">
                <img
                  :src="getAvatarUrl(user)"
                  :alt="user.display_name"
                  class="w-full h-full object-cover"
                  @error="handleImageError"
                />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-foreground truncate">{{ user.display_name }}</p>
              </div>
              <component 
                v-if="String(user.id) === selectedUserId" 
                :is="CheckCircleIcon" 
                :size="18" 
                class="text-purple-400 flex-shrink-0" 
              />
            </button>
          </div>
        </div>
        
        <p v-if="users.length === 0" class="flex items-center gap-2 text-xs text-amber-400 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <component :is="AlertCircleIcon" :size="14" />
          No users loaded. Default user will be used.
        </p>
      </div>

      <!-- Sync Options -->
      <div class="space-y-3">
        <label class="flex items-center gap-2 text-sm font-semibold text-foreground">
          <component :is="ClockIcon" :size="16" class="text-purple-400" />
          When to Sync
        </label>
        
        <!-- Selected Sync Option Card -->
        <div 
          v-if="selectedSyncOptionData" 
          class="p-3 rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30"
        >
          <div class="flex items-center gap-2.5">
            <!-- Radio indicator -->
            <div class="w-4 h-4 rounded-full border-2 border-purple-500 bg-purple-500 flex items-center justify-center flex-shrink-0">
              <div class="w-1.5 h-1.5 bg-white rounded-full" />
            </div>
            <!-- Option Info -->
            <div class="flex-1 min-w-0 overflow-hidden">
              <p class="text-sm font-bold text-foreground truncate">
                {{ selectedSyncOptionData.label }}
              </p>
            </div>
            <!-- Change Button -->
            <button
              type="button"
              @click="showSyncDropdown = !showSyncDropdown"
              class="px-2 py-0.5 rounded-lg text-[9px] font-bold uppercase tracking-wide bg-white/10 hover:bg-purple-500/30 text-purple-400 hover:text-purple-300 transition-all flex-shrink-0"
            >
              Change
            </button>
          </div>
        </div>
        
        <!-- Sync Options Dropdown (expanded) -->
        <div v-if="showSyncDropdown" class="space-y-2">
          <button
            v-for="option in syncOptions"
            :key="option.value"
            type="button"
            :class="[
              'w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all',
              selectedSyncOption === option.value
                ? 'bg-purple-500/20 border-2 border-purple-500'
                : 'bg-black/30 border border-border hover:border-purple-500/40 hover:bg-purple-500/10'
            ]"
            @click="selectSyncOption(option.value)"
          >
            <div
              :class="[
                'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all',
                selectedSyncOption === option.value
                  ? 'border-purple-500 bg-purple-500'
                  : 'border-muted-foreground/40'
              ]"
            >
              <div v-if="selectedSyncOption === option.value" class="w-2 h-2 bg-white rounded-full" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-foreground truncate">{{ option.label }}</p>
              <p class="text-[10px] text-muted-foreground">{{ option.description }}</p>
            </div>
            <component 
              v-if="selectedSyncOption === option.value" 
              :is="CheckCircleIcon" 
              :size="18" 
              class="text-purple-400 flex-shrink-0" 
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  List as ListIcon,
  X as XIcon,
  User as UserIcon,
  Clock as ClockIcon,
  Check as CheckIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  BookOpen as BookOpenIcon,
  Database as DatabaseIcon,
  Globe as GlobeIcon,
  Heart as HeartIcon,
  Calendar as CalendarIcon,
  Zap as ZapIcon,
  Sparkles as SparklesIcon,
  AlertCircle as AlertCircleIcon,
} from 'lucide-vue-next'

interface ListItem {
  id: string
  source?: string
  listId: string
  displayName: string
  listType?: string
  mediaType?: string
  isCurrent?: boolean
}

interface User {
  id: number | string
  display_name: string
  email?: string
  avatar?: string
}

interface Props {
  lists: ListItem[]
  users: User[]
  selectedUserId: string
  selectedSyncOption: 'single' | 'all' | 'schedule'
  overseerrUrl?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  remove: [index: number]
  'update:selected-user-id': [value: string]
  'update:selected-sync-option': [value: 'single' | 'all' | 'schedule']
}>()

const showUserDropdown = ref(false)
const showSyncDropdown = ref(false)

const selectedUser = computed(() => {
  return props.users.find(u => String(u.id) === props.selectedUserId)
})

const selectedSyncOptionData = computed(() => {
  return syncOptions.find(o => o.value === props.selectedSyncOption)
})

const selectUser = (userId: string) => {
  emit('update:selected-user-id', userId)
  showUserDropdown.value = false
}

const selectSyncOption = (value: 'single' | 'all' | 'schedule') => {
  emit('update:selected-sync-option', value)
  showSyncDropdown.value = false
}

const syncOptions = [
  { value: 'single', label: 'Sync immediately', description: 'Start syncing right away' },
  { value: 'all', label: 'Sync all lists', description: 'Sync everything at once' },
  { value: 'schedule', label: 'Next scheduled sync', description: 'Add to the queue' },
] as const

// Clean seed for DiceBear initials (remove emojis and special characters)
const cleanSeedForInitials = (seed: string): string => {
  const cleaned = seed.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim()
  const firstChar = cleaned.match(/[a-zA-Z0-9]/)
  return firstChar ? firstChar[0].toUpperCase() : 'User'
}

// Generate DiceBear avatar URL
const generateDiceBearAvatar = (seed: string): string => {
  const cleanSeed = cleanSeedForInitials(seed)
  const encodedSeed = encodeURIComponent(cleanSeed)
  return `https://api.dicebear.com/7.x/initials/svg?seed=${encodedSeed}&backgroundColor=9333ea`
}

// Get avatar URL - use Overseerr avatar if available, otherwise DiceBear
const getAvatarUrl = (user: User): string => {
  const avatar = user.avatar
  
  if (avatar) {
    // Already proxied through our API cache
    if (avatar.startsWith('/api/images/proxy')) {
      return avatar
    }

    // If already a full URL, use as-is
    if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
      return avatar
    }
    
    // If relative URL and we have Overseerr URL, convert to full URL
    if (props.overseerrUrl && avatar.startsWith('/')) {
      const cleanBaseUrl = props.overseerrUrl.replace(/\/$/, '')
      return `${cleanBaseUrl}${avatar}`
    }
  }
  
  // Fallback to DiceBear
  const seed = user.display_name || user.email || String(user.id) || 'user'
  return generateDiceBearAvatar(seed)
}

// Handle image load errors - fallback to DiceBear
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  const seed = img.alt || 'user'
  img.src = generateDiceBearAvatar(seed)
}

const sourceConfig: Record<string, { icon: any; color: string; bg: string; label: string }> = {
  imdb: { icon: StarIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'IMDb' },
  trakt: { icon: TrendingUpIcon, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Trakt' },
  trakt_special: { icon: ZapIcon, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Trakt Special' },
  letterboxd: { icon: BookOpenIcon, color: 'text-pink-400', bg: 'bg-pink-500/20', label: 'Letterboxd' },
  mdblist: { icon: DatabaseIcon, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'MDBList' },
  stevenlu: { icon: HeartIcon, color: 'text-red-400', bg: 'bg-red-500/20', label: 'Steven Lu' },
  tmdb: { icon: GlobeIcon, color: 'text-cyan-400', bg: 'bg-cyan-500/20', label: 'TMDB' },
  tvdb: { icon: CalendarIcon, color: 'text-indigo-400', bg: 'bg-indigo-500/20', label: 'TVDB' },
  anilist: { icon: SparklesIcon, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'AniList' },
}

const getSourceIcon = (source: string) => {
  return sourceConfig[source]?.icon || DatabaseIcon
}

const getSourceColor = (source: string) => {
  return sourceConfig[source]?.color || 'text-gray-400'
}

const getSourceBg = (source: string) => {
  return sourceConfig[source]?.bg || 'bg-gray-500/20'
}

const formatSource = (source: string) => {
  return sourceConfig[source]?.label || source
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}
</style>
