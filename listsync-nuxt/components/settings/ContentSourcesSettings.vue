<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <ListIcon class="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <h3 class="text-base font-bold titillium-web-semibold">
            Content Sources
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            Configure your list providers and data sources
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="space-y-6">
        <!-- IMDb Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>IMDb Lists</span>
            <Badge variant="secondary" size="sm">IMDb</Badge>
          </label>
          <Input
            v-model="localValue.imdbLists"
            type="text"
            placeholder="top, ls026785255"
            :icon="FilmIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated list IDs (e.g., 'top' or 'ls026785255')
          </p>
        </div>

        <!-- Trakt Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>Trakt Lists</span>
            <Badge variant="primary" size="sm">Trakt</Badge>
          </label>
          <Input
            v-model="localValue.traktLists"
            type="text"
            placeholder="https://app.trakt.tv/users/{user}/lists/{name}"
            :icon="TvIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated Trakt list URLs
          </p>
        </div>

        <!-- Trakt Special Lists -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
              <span>Trakt Special Lists</span>
              <Badge variant="primary" size="sm">Trakt</Badge>
            </label>
            <Input
              v-model="localValue.traktSpecialLists"
              type="text"
              placeholder="trending:movies, popular:shows"
              :icon="TrendingUpIcon"
              @update:model-value="emitUpdate"
            />
            <p class="text-xs text-muted-foreground mt-1">
              Format: type:category (e.g., trending:movies)
            </p>
          </div>

          <div>
            <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
              Items Limit
            </label>
            <Input
              v-model.number="localValue.traktSpecialItemsLimit"
              type="number"
              :min="1"
              :max="100"
              placeholder="20"
              :icon="HashIcon"
              @update:model-value="emitUpdate"
            />
            <p class="text-xs text-muted-foreground mt-1">
              Max items from special lists (1-100)
            </p>
          </div>
        </div>

        <!-- Letterboxd Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>Letterboxd Lists</span>
            <Badge variant="secondary" size="sm">Letterboxd</Badge>
          </label>
          <Input
            v-model="localValue.letterboxdLists"
            type="text"
            placeholder="https://letterboxd.com/{user}/list/{name}/"
            :icon="FilmIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated Letterboxd list URLs
          </p>
        </div>

        <!-- AniList Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>AniList Anime Lists</span>
            <Badge variant="secondary" size="sm">AniList</Badge>
          </label>
          <Input
            v-model="localValue.anilistLists"
            type="text"
            placeholder="https://anilist.co/user/{username}/animelist"
            :icon="SparklesIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Username or full URL. Supports: Planning, Watching, Completed, Paused, Dropped
          </p>
        </div>

        <!-- MDBList Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>MDBList Collections</span>
            <Badge variant="secondary" size="sm">MDBList</Badge>
          </label>
          <Input
            v-model="localValue.mdblistLists"
            type="text"
            placeholder="https://mdblist.com/lists/{user}/{name}"
            :icon="DatabaseIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated MDBList URLs
          </p>
        </div>

        <!-- Steven Lu Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>Steven Lu Lists</span>
            <Badge variant="secondary" size="sm">Steven Lu</Badge>
          </label>
          <Input
            v-model="localValue.stevenluLists"
            type="text"
            placeholder="stevenlu"
            :icon="StarIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Enter 'stevenlu' to enable or leave empty
          </p>
        </div>

        <!-- TMDB Settings -->
        <div class="space-y-4 p-4 rounded-lg bg-blue-500/5 border border-blue-500/20">
          <div class="flex items-center gap-2">
            <FilmIcon class="w-4 h-4 text-blue-400" />
            <span class="text-sm font-bold">TMDB Configuration</span>
            <Badge variant="secondary" size="sm">TMDB</Badge>
          </div>
          
          <div>
            <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
              TMDB API Key
              <span class="text-xs text-muted-foreground ml-2">(Optional but recommended)</span>
            </label>
            <Input
              v-model="localValue.tmdbKey"
              type="password"
              placeholder="Enter your TMDB API key"
              :icon="KeyIcon"
              @update:model-value="emitUpdate"
            />
            <p class="text-xs text-muted-foreground mt-1">
              Recommended for faster processing. Web scraping used if not present.
            </p>
          </div>

          <div>
            <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
              TMDB Lists
            </label>
            <Input
              v-model="localValue.tmdbLists"
              type="text"
              placeholder="https://www.themoviedb.org/list/{id-name}"
              :icon="FilmIcon"
              @update:model-value="emitUpdate"
            />
            <p class="text-xs text-muted-foreground mt-1">
              Comma-separated TMDB list URLs
            </p>
          </div>
        </div>

        <!-- TVDB Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>TVDB Lists</span>
            <Badge variant="secondary" size="sm">TVDB</Badge>
          </label>
          <Input
            v-model="localValue.tvdbLists"
            type="text"
            placeholder="https://www.thetvdb.com/lists/{idorname}"
            :icon="TvIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated TVDB list URLs
          </p>
        </div>

        <!-- SIMKL Lists -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide flex items-center gap-2">
            <span>SIMKL Lists</span>
            <Badge variant="secondary" size="sm">SIMKL</Badge>
          </label>
          <Input
            v-model="localValue.simklLists"
            type="text"
            placeholder="https://simkl.com/{id}/list/{id}/{name}"
            :icon="MonitorIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated SIMKL list URLs
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">List Configuration</p>
            <p class="text-muted-foreground">
              Configure which lists to sync from various platforms. Multiple lists can be separated by commas. Changes require a container restart to take effect.
            </p>
          </div>
        </div>
      </div>

      <!-- Help Box -->
      <div class="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <HelpCircleIcon class="w-5 h-5 text-purple-400 flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-purple-400 mb-2">Supported List Formats</p>
            <div class="text-muted-foreground space-y-1 text-xs">
              <div><strong class="text-foreground">IMDb:</strong> 'top' or list IDs like 'ls026785255'</div>
              <div><strong class="text-foreground">Trakt:</strong> Full URLs or special formats like 'trending:movies'</div>
              <div><strong class="text-foreground">Letterboxd:</strong> Full list URLs</div>
              <div><strong class="text-foreground">AniList:</strong> Username or full animelist URL</div>
              <div><strong class="text-foreground">MDBList:</strong> Full list URLs</div>
              <div><strong class="text-foreground">TMDB:</strong> Full list URLs</div>
              <div><strong class="text-foreground">TVDB:</strong> Full list URLs</div>
              <div><strong class="text-foreground">SIMKL:</strong> Full list URLs</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  List as ListIcon,
  Film as FilmIcon,
  Tv as TvIcon,
  TrendingUp as TrendingUpIcon,
  Hash as HashIcon,
  Sparkles as SparklesIcon,
  Database as DatabaseIcon,
  Star as StarIcon,
  Key as KeyIcon,
  Monitor as MonitorIcon,
  Info as InfoIcon,
  HelpCircle as HelpCircleIcon,
} from 'lucide-vue-next'

interface ContentSourcesSettings {
  imdbLists: string
  traktLists: string
  traktSpecialLists: string
  traktSpecialItemsLimit: number
  letterboxdLists: string
  anilistLists: string
  mdblistLists: string
  stevenluLists: string
  tmdbKey: string
  tmdbLists: string
  tvdbLists: string
  simklLists: string
}

interface Props {
  modelValue: ContentSourcesSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: ContentSourcesSettings]
}>()

const localValue = ref({ ...props.modelValue })

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    localValue.value = { ...newValue }
  },
  { deep: true }
)

// Emit updates
const emitUpdate = () => {
  emit('update:modelValue', { ...localValue.value })
}
</script>

