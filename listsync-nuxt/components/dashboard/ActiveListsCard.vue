<template>
  <Card variant="default" class="overflow-hidden relative group/card cursor-pointer" @click="$router.push('/lists')">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-5">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <component :is="ListIcon" :size="18" class="text-purple-400" />
          <span class="text-[10px] font-semibold text-purple-300 uppercase tracking-wide">Active Lists</span>
        </div>
        <div class="px-3 py-1 rounded-full bg-purple-400/20 border border-purple-400/30">
          <span class="text-xs font-semibold text-purple-200">{{ lists.length }} Lists</span>
        </div>
      </div>

      <!-- Lists Grid -->
      <div v-if="lists.length > 0" class="grid grid-cols-1 gap-3">
        <div
          v-for="list in lists"
          :key="list.id"
          class="p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-400/5 border border-purple-500/20 hover:border-purple-400/40 transition-all"
        >
          <div class="flex items-center justify-between gap-3">
            <!-- Provider Icon & Name -->
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div class="w-10 h-10 rounded-lg bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                <component :is="getProviderIcon(list.list_type)" :size="20" class="text-purple-300" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-foreground truncate">
                  {{ list.display_name || formatListName(list.list_type, list.list_id) }}
                </p>
                <p class="text-xs text-muted-foreground">
                  {{ formatProviderName(list.list_type) }}
                </p>
              </div>
            </div>

            <!-- Stats -->
            <div class="flex items-center gap-4 flex-shrink-0">
              <!-- Item Count -->
              <div v-if="list.item_count > 0" class="text-right">
                <p class="text-lg font-bold text-foreground tabular-nums">{{ formatNumber(list.item_count) }}</p>
                <p class="text-[10px] text-muted-foreground uppercase">Items</p>
              </div>

              <!-- Last Synced -->
              <div class="text-right min-w-[80px]">
                <p class="text-xs font-medium text-purple-300">
                  <ClientOnly>
                    <TimeAgo v-if="list.last_synced" :timestamp="list.last_synced" />
                    <span v-else class="text-muted-foreground">Never</span>
                    <template #fallback>
                      <span class="opacity-50">...</span>
                    </template>
                  </ClientOnly>
                </p>
                <p class="text-[10px] text-muted-foreground uppercase">Last Synced</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <component :is="ListIcon" :size="32" class="mx-auto text-purple-500/30 mb-2" />
        <p class="text-sm text-muted-foreground">No lists configured</p>
        <p class="text-xs text-muted-foreground mt-1">Click to add your first list</p>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  List as ListIcon,
  Film as ImdbIcon,
  Star as TraktIcon,
  Mail as LetterboxdIcon,
  Database as MdblistIcon,
  Globe as StevenluIcon,
  Clapperboard as TmdbIcon,
  Tv2 as SimklIcon,
  TvMinimal as TvdbIcon,
  Sparkles as AnilistIcon,
} from 'lucide-vue-next'
import type { List } from '~/types'

interface Props {
  lists: List[]
}

defineProps<Props>()

// Format number with commas
const formatNumber = (num: number) => {
  return new Intl.NumberFormat().format(num)
}

// Get provider icon based on list type
const getProviderIcon = (listType: string) => {
  const iconMap: Record<string, any> = {
    'imdb': ImdbIcon,
    'trakt': TraktIcon,
    'trakt_special': TraktIcon,
    'letterboxd': LetterboxdIcon,
    'mdblist': MdblistIcon,
    'stevenlu': StevenluIcon,
    'tmdb': TmdbIcon,
    'simkl': SimklIcon,
    'tvdb': TvdbIcon,
    'anilist': AnilistIcon,
  }
  return iconMap[listType] || ListIcon
}

// Format provider name
const formatProviderName = (listType: string) => {
  const nameMap: Record<string, string> = {
    'imdb': 'IMDb',
    'trakt': 'Trakt',
    'trakt_special': 'Trakt',
    'letterboxd': 'Letterboxd',
    'mdblist': 'MDBList',
    'stevenlu': 'StevenLu',
    'tmdb': 'TMDb',
    'simkl': 'Simkl',
    'tvdb': 'TVDB',
    'anilist': 'AniList',
  }
  return nameMap[listType] || listType.toUpperCase()
}

// Format list name from type and ID
const formatListName = (listType: string, listId: string) => {
  // Try to make it human readable
  return listId.replace(/_/g, ' ').replace(/-/g, ' ').split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ')
}
</script>

