<template>
  <div class="space-y-6">
    <div class="text-center mb-6">
      <h2 class="text-2xl font-bold mb-2">Content Sources</h2>
      <p class="text-muted-foreground">
        Add at least one list source to start syncing
      </p>
    </div>

    <!-- General Error -->
    <div v-if="errors.general" class="bg-danger/10 border border-danger/20 rounded-lg p-4">
      <div class="flex items-start gap-2">
        <AlertCircleIcon class="w-5 h-5 text-danger flex-shrink-0" />
        <p class="text-sm text-danger">{{ errors.general }}</p>
      </div>
    </div>

    <div class="space-y-4 max-h-[500px] overflow-y-auto pr-2">
      <!-- IMDb Lists -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          IMDb Lists
          <Badge variant="secondary" size="sm">IMDb</Badge>
        </label>
        <Input
          v-model="localValue.imdb_lists"
          type="text"
          placeholder="top, ls026785255"
          :icon="FilmIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Comma-separated: 'top' or list IDs like 'ls026785255'
        </p>
      </div>

      <!-- Trakt Lists -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          Trakt Lists
          <Badge variant="primary" size="sm">Trakt</Badge>
        </label>
        <Input
          v-model="localValue.trakt_lists"
          type="text"
          placeholder="https://app.trakt.tv/users/{user}/lists/{name}"
          :icon="TvIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Comma-separated Trakt list URLs
        </p>
      </div>

      <!-- Trakt Special Lists -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-bold mb-2 flex items-center gap-2">
            Trakt Special Lists
            <Badge variant="primary" size="sm">Trakt</Badge>
          </label>
          <Input
            v-model="localValue.trakt_special_lists"
            type="text"
            placeholder="trending:movies, popular:shows"
            :icon="TrendingUpIcon"
            :disabled="isValidating"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Format: type:category
          </p>
        </div>
        <div>
          <label class="block text-sm font-bold mb-2">
            Items Limit
          </label>
          <Input
            v-model.number="localValue.trakt_special_items_limit"
            type="number"
            :min="1"
            :max="100"
            placeholder="20"
            :icon="HashIcon"
            :disabled="isValidating"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Max items (1-100)
          </p>
        </div>
      </div>

      <!-- Letterboxd Lists -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          Letterboxd Lists
          <Badge variant="secondary" size="sm">Letterboxd</Badge>
        </label>
        <Input
          v-model="localValue.letterboxd_lists"
          type="text"
          placeholder="https://letterboxd.com/{user}/list/{name}/"
          :icon="FilmIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Comma-separated Letterboxd list URLs
        </p>
      </div>

      <!-- AniList -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          AniList Anime Lists
          <Badge variant="secondary" size="sm">AniList</Badge>
        </label>
        <Input
          v-model="localValue.anilist_lists"
          type="text"
          placeholder="username or https://anilist.co/user/{username}/animelist"
          :icon="SparklesIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Username or full URL (supports: Planning, Watching, Completed)
        </p>
      </div>

      <!-- MDBList -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          MDBList Collections
          <Badge variant="secondary" size="sm">MDBList</Badge>
        </label>
        <Input
          v-model="localValue.mdblist_lists"
          type="text"
          placeholder="https://mdblist.com/lists/{user}/{name}"
          :icon="DatabaseIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Comma-separated MDBList URLs
        </p>
      </div>

      <!-- TMDB (with API key) -->
      <div class="space-y-3 p-4 rounded-lg bg-blue-500/5 border border-blue-500/20">
        <div class="flex items-center gap-2">
          <FilmIcon class="w-4 h-4 text-blue-400" />
          <span class="text-sm font-bold">TMDB Configuration</span>
          <Badge variant="secondary" size="sm">TMDB</Badge>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">
            TMDB API Key (Optional)
          </label>
          <Input
            v-model="localValue.tmdb_key"
            type="password"
            placeholder="Enter TMDB API key for faster processing"
            :icon="KeyIcon"
            :disabled="isValidating"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Recommended for faster processing. Web scraping used if not provided.
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium mb-2">
            TMDB Lists
          </label>
          <Input
            v-model="localValue.tmdb_lists"
            type="text"
            placeholder="https://www.themoviedb.org/list/{id-name}"
            :icon="FilmIcon"
            :disabled="isValidating"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Comma-separated TMDB list URLs
          </p>
        </div>
      </div>

      <!-- Other Sources -->
      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          Steven Lu Lists
          <Badge variant="secondary" size="sm">Steven Lu</Badge>
        </label>
        <Input
          v-model="localValue.stevenlu_lists"
          type="text"
          placeholder="stevenlu"
          :icon="StarIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Enter 'stevenlu' to enable popular movies list
        </p>
      </div>

      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          TVDB Lists
          <Badge variant="secondary" size="sm">TVDB</Badge>
        </label>
        <Input
          v-model="localValue.tvdb_lists"
          type="text"
          placeholder="https://www.thetvdb.com/lists/{idorname}"
          :icon="TvIcon"
          :disabled="isValidating"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Comma-separated TVDB list URLs
        </p>
      </div>

      <div>
        <label class="block text-sm font-bold mb-2 flex items-center gap-2">
          SIMKL Lists
          <Badge variant="secondary" size="sm">SIMKL</Badge>
        </label>
        <Input
          v-model="localValue.simkl_lists"
          type="text"
          placeholder="https://simkl.com/{id}/list/{id}/{name}"
          :icon="MonitorIcon"
          :disabled="isValidating"
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
          <p class="font-medium text-info mb-1">Quick Start Tip</p>
          <p class="text-muted-foreground">
            Start with one or two lists. You can always add more later from the Settings page.
          </p>
        </div>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between pt-4">
      <Button
        variant="ghost"
        size="lg"
        :disabled="isValidating"
        @click="emit('back')"
      >
        <ArrowLeftIcon class="w-4 h-4 mr-2" />
        Back
      </Button>
      <Button
        variant="primary"
        size="lg"
        :loading="isValidating"
        :disabled="!hasAnyList"
        @click="emit('complete')"
      >
        Complete Setup
        <CheckIcon class="w-4 h-4 ml-2" />
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Film as FilmIcon,
  Tv as TvIcon,
  TrendingUp as TrendingUpIcon,
  Hash as HashIcon,
  Sparkles as SparklesIcon,
  Database as DatabaseIcon,
  Key as KeyIcon,
  Star as StarIcon,
  Monitor as MonitorIcon,
  Info as InfoIcon,
  AlertCircle as AlertCircleIcon,
  ArrowLeft as ArrowLeftIcon,
  Check as CheckIcon,
} from 'lucide-vue-next'

interface Step3Data {
  imdb_lists: string
  trakt_lists: string
  trakt_special_lists: string
  trakt_special_items_limit: number
  letterboxd_lists: string
  anilist_lists: string
  mdblist_lists: string
  stevenlu_lists: string
  tmdb_key: string
  tmdb_lists: string
  tvdb_lists: string
  simkl_lists: string
}

interface Props {
  modelValue: Step3Data
  isValidating: boolean
  errors: Record<string, string>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: Step3Data]
  'complete': []
  'back': []
}>()

const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const hasAnyList = computed(() => {
  return !!(
    localValue.value.imdb_lists ||
    localValue.value.trakt_lists ||
    localValue.value.trakt_special_lists ||
    localValue.value.letterboxd_lists ||
    localValue.value.anilist_lists ||
    localValue.value.mdblist_lists ||
    localValue.value.stevenlu_lists ||
    localValue.value.tmdb_lists ||
    localValue.value.tvdb_lists ||
    localValue.value.simkl_lists
  )
})
</script>

