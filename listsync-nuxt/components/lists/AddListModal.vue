<template>
  <Modal
    v-model="isOpen"
    title="Add New List"
    size="lg"
    @close="handleClose"
  >
    <div class="space-y-6">
      <!-- Progress Indicator -->
      <div class="flex items-center justify-center gap-2">
        <div
          v-for="step in 4"
          :key="step"
          :class="[
            'h-2 rounded-full transition-all',
            step === currentStep ? 'w-8 bg-purple-500' : step < currentStep ? 'w-6 bg-purple-500/50' : 'w-6 bg-white/10'
          ]"
        />
      </div>

      <!-- Step 1: Choose Sources -->
      <div v-if="currentStep === 1" class="space-y-6">
        <div class="text-center space-y-2">
          <p class="text-sm text-muted-foreground">
            Select the sources for your lists
          </p>
          <p class="text-xs text-muted-foreground">
            You can select multiple providers to add lists from
          </p>
        </div>

        <!-- Selected Providers Display -->
        <div v-if="selectedProviders.length > 0" class="space-y-3">
          <p class="text-sm font-medium text-foreground">Selected Providers ({{ selectedProviders.length }})</p>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="provider in selectedProviders"
              :key="provider"
              class="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/20 border border-purple-500/40"
            >
              <component :is="getSourceIcon(provider)" :size="16" :class="getSourceColor(provider).color" />
              <span class="text-sm font-medium text-foreground">{{ formatListSource(provider) }}</span>
              <button
                @click="removeProvider(provider)"
                class="p-1 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
              >
                <component :is="TrashIcon" :size="12" />
              </button>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <button
            v-for="source in paginatedSources"
            :key="source.value"
            :class="getSourceButtonClass(source.value)"
            @click="selectSource(source.value)"
          >
            <div class="flex flex-col items-center gap-3">
              <div :class="[
                'p-3 rounded-xl transition-all duration-300',
                source.bgColor,
                selectedProviders.includes(source.value) ? source.borderColor : 'border border-transparent'
              ]">
                <component :is="source.icon" :size="28" :class="source.color" />
              </div>
              <div class="text-center">
                <span class="font-semibold text-foreground block">{{ source.label }}</span>
                <span class="text-xs text-muted-foreground mt-1">{{ source.description }}</span>
              </div>
            </div>
          </button>
        </div>

        <!-- Pagination Controls -->
        <div v-if="totalPages > 1" class="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            :icon="ChevronLeftIcon"
            :disabled="currentPage === 1"
            @click="currentPage = Math.max(1, currentPage - 1)"
          >
            Previous
          </Button>

          <div class="flex items-center gap-2">
            <button
              v-for="page in totalPages"
              :key="page"
              :class="[
                'w-8 h-8 rounded-full text-sm font-medium transition-all',
                page === currentPage
                  ? 'bg-purple-500 text-white'
                  : 'bg-white/10 text-muted-foreground hover:bg-white/20'
              ]"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
          </div>

          <Button
            variant="ghost"
            size="sm"
            :icon="ChevronRightIcon"
            :disabled="currentPage === totalPages"
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
          >
            Next
          </Button>
        </div>
      </div>

      <!-- Step 2: Enter Details -->
      <div v-else-if="currentStep === 2" class="space-y-4">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="p-1 rounded hover:bg-white/5 transition-colors"
              @click="currentStep = 1"
            >
              <component :is="ChevronLeftIcon" :size="20" />
            </button>
            <Badge :variant="'primary'" size="sm">
              <component :is="getSourceIcon(selectedSource)" :size="12" />
              {{ formatListSource(selectedSource) }}
            </Badge>
          </div>
          <div class="text-xs text-muted-foreground">
            {{ selectedProviders.indexOf(currentProvider) + 1 }} of {{ selectedProviders.length }}
          </div>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Trakt Special Button Grid -->
          <div v-if="isTraktSpecial" class="space-y-4">
            <!-- List Type Buttons -->
            <div>
              <label class="block text-sm font-medium text-foreground mb-3">
                Choose List Type
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="type in traktSpecialTypes"
                  :key="type.value"
                  type="button"
                  :class="[
                    'p-3 rounded-lg border-2 text-sm font-medium transition-all',
                    selectedTraktType === type.value
                      ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                      : 'border-border bg-black/20 text-foreground hover:border-purple-500/50'
                  ]"
                  @click="handleTraktTypeSelect(type.value)"
                >
                  {{ type.label }}
                </button>
              </div>
            </div>

            <!-- Media Type Buttons -->
            <div v-if="selectedTraktType">
              <label class="block text-sm font-medium text-foreground mb-3">
                Choose Media Type
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="media in traktMediaTypes"
                  :key="media.value"
                  type="button"
                  :class="[
                    'p-3 rounded-lg border-2 text-sm font-medium transition-all',
                    selectedTraktMedia === media.value
                      ? 'border-green-500 bg-green-500/20 text-green-300'
                      : 'border-border bg-black/20 text-foreground hover:border-green-500/50'
                  ]"
                  @click="handleTraktMediaSelect(media.value)"
                >
                  {{ media.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- IMDb Presets -->
          <div v-else-if="selectedSource === 'imdb'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-foreground mb-3">
                Choose IMDb List or Enter Custom ID
              </label>
              
              <!-- Preset Buttons -->
              <div class="grid grid-cols-2 gap-2 mb-4">
                <button
                  v-for="preset in imdbPresets"
                  :key="preset.value"
                  type="button"
                  :class="[
                    'p-3 rounded-lg border-2 text-sm font-medium transition-all',
                    listId === preset.value
                      ? 'border-yellow-500 bg-yellow-500/20 text-yellow-300'
                      : 'border-border bg-black/20 text-foreground hover:border-yellow-500/50'
                  ]"
                  @click="handleImdbPresetSelect(preset.value)"
                >
                  {{ preset.label }}
                </button>
              </div>
              
              <!-- Divider -->
              <div class="relative my-4">
                <div class="absolute inset-0 flex items-center">
                  <div class="w-full border-t border-border"></div>
                </div>
                <div class="relative flex justify-center text-xs uppercase">
                  <span class="bg-background px-2 text-muted-foreground">Or enter custom</span>
                </div>
              </div>
              
              <!-- Custom Input -->
              <Input
                v-model="listId"
                label="Custom IMDb List ID"
                placeholder="e.g., ls0000000 or tt1234567"
                :error="error"
                @blur="validateInput"
              />
            </div>
          </div>

          <!-- Steven Lu Button -->
          <div v-else-if="selectedSource === 'stevenlu'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-foreground mb-3">
                Steven Lu's Movie Collection
              </label>
              
              <button
                type="button"
                :class="[
                  'w-full p-4 rounded-lg border-2 text-sm font-medium transition-all',
                  listId === 'stevenlu'
                    ? 'border-green-500 bg-green-500/20 text-green-300'
                    : 'border-border bg-black/20 text-foreground hover:border-green-500/50'
                ]"
                @click="handleStevenLuSelect"
              >
                <div class="flex items-center justify-center gap-2">
                  <DatabaseIcon :size="20" />
                  <span>Sync Steven Lu's Movie List</span>
                </div>
              </button>
            </div>
          </div>

          <!-- Regular List ID / URL Input -->
          <Input
            v-else
            v-model="listId"
            :label="`${formatListSource(selectedSource)} List ${isUrlRequired ? 'URL' : 'ID'}`"
            :placeholder="getPlaceholder(selectedSource)"
            :error="error"
            required
            @blur="validateInput"
          />

          <!-- Helper Text -->
          <div class="flex items-start gap-2 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
            <component :is="InfoIcon" :size="16" class="text-purple-400 flex-shrink-0 mt-0.5" />
            <p class="text-xs text-muted-foreground">
              {{ getHelperText(selectedSource) }}
            </p>
          </div>
        </form>
      </div>

      <!-- Step 3: Sync Options -->
      <div v-if="currentStep === 3" class="space-y-4">
        <div class="text-center space-y-2">
          <p class="text-sm font-medium text-foreground">
            List ready to be added!
          </p>
          <p class="text-xs text-muted-foreground">
            Choose how you want to sync this list
          </p>
        </div>

        <!-- Sync Options -->
        <div class="space-y-3">
          <!-- Option 1: Just Add (Scheduled) -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'schedule'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'schedule'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'schedule'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'schedule'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Add to Next Scheduled Sync</p>
                <p class="text-xs text-muted-foreground mt-1">
                  List will be synced automatically during the next scheduled sync interval
                </p>
              </div>
            </div>
          </button>

          <!-- Option 2: Sync This One Now -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'single'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'single'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'single'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'single'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Sync This List Now</p>
                <p class="text-xs text-muted-foreground mt-1">
                  Immediately sync only this new list
                </p>
              </div>
            </div>
          </button>

          <!-- Option 3: Sync All Now -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'all'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'all'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'all'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'all'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Sync All Lists Now</p>
                <p class="text-xs text-muted-foreground mt-1">
                  Immediately sync all configured lists including this new one
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Step 4: Summary & Schedule -->
      <div v-if="currentStep === 4" class="space-y-6">
        <div class="text-center space-y-2">
          <p class="text-sm font-medium text-foreground">
            {{ listsToAdd.length }} List{{ listsToAdd.length > 1 ? 's' : '' }} Ready to Add
          </p>
          <p class="text-xs text-muted-foreground">
            Choose how you want to sync these lists
          </p>
        </div>

        <!-- Lists Summary -->
        <div class="space-y-3 max-h-60 overflow-y-auto">
          <div
            v-for="(list, index) in listsToAdd"
            :key="list.id"
            class="flex items-center justify-between p-4 rounded-lg bg-black/20 border border-border"
          >
            <div class="flex items-center gap-3">
              <div :class="[
                'p-2 rounded-lg',
                getSourceColor(list.source).bgColor
              ]">
                <component :is="getSourceIcon(list.source)" :size="16" :class="getSourceColor(list.source).color" />
              </div>
              <div>
                <p class="font-medium text-foreground">{{ list.displayName }}</p>
                <p class="text-xs text-muted-foreground">{{ formatListSource(list.source) }}</p>
              </div>
            </div>
            <button
              @click="removeListFromBatch(index)"
              class="p-1 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
              title="Remove from batch"
            >
              <component :is="TrashIcon" :size="16" />
            </button>
          </div>
        </div>

        <!-- Add More Lists Button -->
        <div class="text-center">
          <Button
            variant="ghost"
            :icon="PlusIcon"
            @click="addAnotherList"
          >
            Add Another List
          </Button>
        </div>

        <!-- Sync Options -->
        <div class="space-y-3">
          <!-- Option 1: Just Add (Scheduled) -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'schedule'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'schedule'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'schedule'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'schedule'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Add to Next Scheduled Sync</p>
                <p class="text-xs text-muted-foreground mt-1">
                  Lists will be synced automatically during the next scheduled sync interval
                </p>
              </div>
            </div>
          </button>

          <!-- Option 2: Sync These Lists Now -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'single'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'single'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'single'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'single'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Sync These Lists Now</p>
                <p class="text-xs text-muted-foreground mt-1">
                  Immediately sync only these {{ listsToAdd.length }} new lists
                </p>
              </div>
            </div>
          </button>

          <!-- Option 3: Sync All Now -->
          <button
            type="button"
            :class="[
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedSyncOption === 'all'
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-border bg-black/20 hover:border-purple-500/50'
            ]"
            @click="selectedSyncOption = 'all'"
          >
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0 mt-1">
                <div
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    selectedSyncOption === 'all'
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-border'
                  ]"
                >
                  <div v-if="selectedSyncOption === 'all'" class="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
              <div class="flex-1">
                <p class="font-medium text-foreground">Sync All Lists Now</p>
                <p class="text-xs text-muted-foreground mt-1">
                  Immediately sync all configured lists including these {{ listsToAdd.length }} new ones
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <Button
          variant="ghost"
          @click="handleClose"
        >
          Cancel
        </Button>

        <div class="flex items-center gap-2">
          <Button
            v-if="currentStep > 1 && currentStep < 4"
            variant="secondary"
            :disabled="loading"
            @click="currentStep--"
          >
            Back
          </Button>

          <Button
            v-if="currentStep === 1"
            variant="secondary"
            :disabled="loading"
            @click="handleClose"
          >
            Cancel
          </Button>

          <Button
            v-if="currentStep === 1"
            variant="primary"
            :disabled="selectedProviders.length === 0"
            @click="startAddingLists"
          >
            Continue with {{ selectedProviders.length }} Provider{{ selectedProviders.length > 1 ? 's' : '' }}
          </Button>

          <Button
            v-if="currentStep === 2"
            variant="primary"
            :disabled="!canProceed"
            :loading="loading"
            @click="addListToBatch"
          >
            {{ selectedProviders.indexOf(currentProvider) < selectedProviders.length - 1 ? 'Add List & Next' : 'Add List & Finish' }}
          </Button>

          <Button
            v-if="currentStep === 2"
            variant="ghost"
            :disabled="!canProceed"
            :loading="loading"
            @click="proceedToSchedule"
          >
            Skip This Provider
          </Button>

          <Button
            v-if="currentStep === 3"
            variant="primary"
            :disabled="!canProceed"
            :loading="loading"
            @click="handleNext"
          >
            Add List & {{ getSyncButtonText() }}
          </Button>

          <Button
            v-if="currentStep === 4"
            variant="primary"
            :disabled="listsToAdd.length === 0"
            :loading="loading"
            @click="handleSubmitMultiple"
          >
            Add {{ listsToAdd.length }} List{{ listsToAdd.length > 1 ? 's' : '' }} & {{ getSyncButtonText() }}
          </Button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  Film as FilmIcon,
  Tv as TvIcon,
  Database as DatabaseIcon,
  Info as InfoIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  BookOpen as BookOpenIcon,
  Globe as GlobeIcon,
  Zap as ZapIcon,
  Heart as HeartIcon,
  Calendar as CalendarIcon,
  Users as UsersIcon,
  Monitor as MonitorIcon,
  Plus as PlusIcon,
  Trash2 as TrashIcon,
  Sparkles as SparklesIcon,
} from 'lucide-vue-next'
import { useSyncStore } from '~/stores/sync'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'list-added': []
}>()

const { showSuccess, showError } = useToast()

// Computed for v-model
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// State
const currentStep = ref(1)
const selectedSource = ref('')
const listId = ref('')
const error = ref('')
const loading = ref(false)
const selectedSyncOption = ref<'all' | 'single' | 'schedule'>('schedule')
const currentPage = ref(1)
const itemsPerPage = 6

// Multi-list state
const listsToAdd = ref<Array<{
  id: string
  source: string
  listId: string
  displayName: string
  listType?: string
  mediaType?: string
}>>([])
const isAddingMultiple = ref(false)

// Multi-provider selection state
const selectedProviders = ref<string[]>([])
const currentProvider = ref('')

// Sources with improved icons and colors
const sources = [
  { 
    label: 'IMDb', 
    value: 'imdb', 
    icon: StarIcon, 
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/40',
    description: 'Internet Movie Database'
  },
  { 
    label: 'Trakt', 
    value: 'trakt', 
    icon: TrendingUpIcon, 
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/40',
    description: 'Track your movies & TV'
  },
  { 
    label: 'Trakt Special', 
    value: 'trakt_special', 
    icon: ZapIcon, 
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/40',
    description: 'Curated Trakt lists'
  },
  { 
    label: 'Letterboxd', 
    value: 'letterboxd', 
    icon: BookOpenIcon, 
    color: 'text-pink-400',
    bgColor: 'bg-pink-500/20',
    borderColor: 'border-pink-500/40',
    description: 'Social film discovery'
  },
  { 
    label: 'MDBList', 
    value: 'mdblist', 
    icon: DatabaseIcon, 
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/40',
    description: 'Movie database lists'
  },
  { 
    label: 'Steven Lu', 
    value: 'stevenlu', 
    icon: HeartIcon, 
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500/40',
    description: 'Curated movie collection'
  },
  { 
    label: 'TMDB', 
    value: 'tmdb', 
    icon: GlobeIcon, 
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
    borderColor: 'border-cyan-500/40',
    description: 'The Movie Database'
  },
  { 
    label: 'Simkl', 
    value: 'simkl', 
    icon: MonitorIcon, 
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/40',
    description: 'Track movies & shows'
  },
  { 
    label: 'TVDB', 
    value: 'tvdb', 
    icon: CalendarIcon, 
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/20',
    borderColor: 'border-indigo-500/40',
    description: 'TV series database'
  },
  { 
    label: 'AniList', 
    value: 'anilist', 
    icon: SparklesIcon, 
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
    borderColor: 'border-amber-500/40',
    description: 'Anime tracking platform'
  },
]

// Trakt special list options
const traktSpecialTypes = [
  { label: 'Trending', value: 'trending' },
  { label: 'Popular', value: 'popular' },
  { label: 'Anticipated', value: 'anticipated' },
  { label: 'Watched', value: 'watched' },
  { label: 'Collected', value: 'collected' },
  { label: 'Recommendations', value: 'recommendations' },
  { label: 'Box Office', value: 'boxoffice' },
]

const traktMediaTypes = [
  { label: 'Movies', value: 'movies' },
  { label: 'TV Shows', value: 'shows' },
]

// IMDb presets (using chart names as per documentation)
const imdbPresets = [
  { label: 'Top 250 Movies', value: 'top' },
  { label: 'Box Office', value: 'boxoffice' },
  { label: 'MovieMeter (Popular Movies)', value: 'moviemeter' },
  { label: 'TVMeter (Popular TV)', value: 'tvmeter' },
]

// State for Trakt Special selections
const selectedTraktType = ref('')
const selectedTraktMedia = ref('')

// Computed
const totalPages = computed(() => Math.ceil(sources.length / itemsPerPage))

const paginatedSources = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return sources.slice(start, end)
})

const isUrlRequired = computed(() => {
  return ['letterboxd', 'mdblist', 'tmdb', 'simkl', 'tvdb', 'anilist'].includes(selectedSource.value)
})

const isTraktSpecial = computed(() => {
  return selectedSource.value === 'trakt_special'
})

const canProceed = computed(() => {
  if (currentStep.value === 1) {
    return selectedSource.value !== ''
  }
  
  // For Trakt Special, require both selections
  if (isTraktSpecial.value) {
    return selectedTraktType.value !== '' && selectedTraktMedia.value !== ''
  }
  
  // For Steven Lu or IMDb presets, just check if listId is set
  if (selectedSource.value === 'stevenlu' || selectedSource.value === 'imdb') {
    return listId.value.trim() !== ''
  }
  
  return listId.value.trim() !== '' && !error.value
})

// Get source icon
const getSourceIcon = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.icon || DatabaseIcon
}

// Get source color info
const getSourceColor = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return {
    color: sourceData?.color || 'text-gray-400',
    bgColor: sourceData?.bgColor || 'bg-gray-500/20',
    borderColor: sourceData?.borderColor || 'border-gray-500/40'
  }
}

// Format list source for display
const formatListSource = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.label || source
}

// Get placeholder text
const getPlaceholder = (source: string) => {
  const placeholders: Record<string, string> = {
    imdb: "'top' or 'ls026785255'",
    trakt: 'https://trakt.tv/users/{user}/watchlist or /lists/{name}',
    trakt_special: 'Select from predefined lists below',
    letterboxd: 'https://letterboxd.com/{user}/list/{name}/ or /watchlist',
    mdblist: 'https://mdblist.com/lists/{user}/{name}',
    stevenlu: "'stevenlu'",
    tmdb: 'https://www.themoviedb.org/list/{id-name}',
    simkl: 'https://simkl.com/{id}/list/{id}/{name}',
    tvdb: 'https://www.thetvdb.com/lists/{idorname}',
    anilist: 'https://anilist.co/user/{username}/animelist or {username}',
  }
  return placeholders[source] || 'Enter list ID or URL'
}

// Get helper text
const getHelperText = (source: string) => {
  const helpers: Record<string, string> = {
    imdb: 'Enter a chart name like "top" or a list ID like "ls026785255"',
    trakt: 'Enter the full Trakt URL: https://trakt.tv/users/{user}/watchlist or https://app.trakt.tv/users/{user}/lists/{name}',
    trakt_special: 'Select a list type and media type from the dropdowns below to sync curated Trakt lists',
    letterboxd: 'Enter the full Letterboxd URL: https://letterboxd.com/{user}/list/{name}/ or https://letterboxd.com/{user}/watchlist/',
    mdblist: 'Enter the full MDBList URL: https://mdblist.com/lists/{user}/{name}',
    stevenlu: 'Click the button above to sync Steven Lu\'s curated movie collection (use "stevenlu")',
    tmdb: 'Enter the full TMDB list URL: https://www.themoviedb.org/list/{id-name}',
    simkl: 'Enter the full Simkl list URL: https://simkl.com/{id}/list/{id}/{name}',
    tvdb: 'Enter the full TVDB list URL: https://www.thetvdb.com/lists/{idorname}',
    anilist: 'Enter the full AniList URL: https://anilist.co/user/{username}/animelist or https://anilist.co/user/{username}/animelist/{status} (Planning, Watching, Completed, etc.) or just the username',
  }
  return helpers[source] || 'Enter the list identifier'
}

// Get source button class
const getSourceButtonClass = (source: string) => {
  const isSelected = selectedSource.value === source
  
  const baseClasses = [
    'w-full p-6 rounded-xl border-2 transition-all duration-300 group',
    'hover:scale-105 hover:shadow-lg',
  ]

  if (isSelected) {
    return [
      ...baseClasses,
      'bg-purple-500/10 border-purple-500/50 text-purple-300',
      'shadow-lg shadow-purple-500/20 scale-105',
    ].join(' ')
  }

  return [
    ...baseClasses,
    'bg-black/20 border-border text-muted-foreground',
    'hover:bg-white/5 hover:border-purple-500/30 hover:text-foreground',
    'hover:shadow-lg hover:shadow-purple-500/10',
  ].join(' ')
}

// Handlers
const selectSource = (source: string) => {
  // Toggle provider selection
  if (selectedProviders.value.includes(source)) {
    // Remove from selection
    selectedProviders.value = selectedProviders.value.filter(p => p !== source)
  } else {
    // Add to selection
    selectedProviders.value.push(source)
  }
}

// Start adding lists for selected providers
const startAddingLists = () => {
  if (selectedProviders.value.length === 0) return
  
  // Set the first provider as current and go to step 2
  currentProvider.value = selectedProviders.value[0]
  selectedSource.value = currentProvider.value
  currentStep.value = 2
}

// Move to next provider in the list
const nextProvider = () => {
  const currentIndex = selectedProviders.value.indexOf(currentProvider.value)
  if (currentIndex < selectedProviders.value.length - 1) {
    currentProvider.value = selectedProviders.value[currentIndex + 1]
    selectedSource.value = currentProvider.value
    // Reset form for next provider
    listId.value = ''
    selectedTraktType.value = ''
    selectedTraktMedia.value = ''
    error.value = ''
  } else {
    // All providers processed, go to summary
    currentStep.value = 4
  }
}

// Remove provider from selection
const removeProvider = (source: string) => {
  selectedProviders.value = selectedProviders.value.filter(p => p !== source)
}

// Add list to batch
const addListToBatch = () => {
  if (!validateInput()) return

  const listId = getFinalListId()
  const listType = getFinalListType()
  const displayName = getDisplayName()

  const newList = {
    id: `${listType}-${listId}-${Date.now()}`,
    source: selectedSource.value,
    listId: listId,
    displayName: displayName,
    listType: listType,
    mediaType: isTraktSpecial.value ? selectedTraktMedia.value : undefined
  }

  listsToAdd.value.push(newList)
  
  // Move to next provider or go to summary
  nextProvider()
}

// Get final list ID based on source
const getFinalListId = () => {
  if (isTraktSpecial.value) {
    return `${selectedTraktType.value}:${selectedTraktMedia.value}`
  }
  return listId.value.trim()
}

// Get final list type
const getFinalListType = () => {
  if (isTraktSpecial.value) {
    return 'trakt_special'
  }
  return selectedSource.value
}

// Get display name for the list
const getDisplayName = () => {
  if (isTraktSpecial.value) {
    const typeFormatted = selectedTraktType.value.charAt(0).toUpperCase() + selectedTraktType.value.slice(1)
    const mediaFormatted = selectedTraktMedia.value === 'movies' ? 'Movies' : 'TV Shows'
    return `${typeFormatted} ${mediaFormatted}`
  }
  
  if (selectedSource.value === 'imdb') {
    const imdbCharts: Record<string, string> = {
      'top': 'Top 250 Movies',
      'boxoffice': 'Box Office',
      'moviemeter': 'MovieMeter (Popular Movies)',
      'tvmeter': 'TVMeter (Popular TV)',
    }
    return imdbCharts[listId.value.toLowerCase()] || listId.value
  }
  
  if (selectedSource.value === 'stevenlu') {
    return "Steven Lu's Movie Collection"
  }
  
  return listId.value
}

// Remove list from batch
const removeListFromBatch = (index: number) => {
  listsToAdd.value.splice(index, 1)
}

// Add another list
const addAnotherList = () => {
  currentStep.value = 1
  selectedSource.value = ''
  listId.value = ''
  selectedTraktType.value = ''
  selectedTraktMedia.value = ''
  error.value = ''
  currentPage.value = 1
}

// Proceed to schedule (single list)
const proceedToSchedule = () => {
  // Skip current provider and move to next or finish
  nextProvider()
}

// Handler for Trakt Special selections
const handleTraktTypeSelect = (type: string) => {
  selectedTraktType.value = type
  // Don't auto-proceed yet, wait for media type selection
}

const handleTraktMediaSelect = (media: string) => {
  selectedTraktMedia.value = media
  // Auto-proceed once both are selected
  if (selectedTraktType.value && selectedTraktMedia.value) {
    // Check if we're in multi-provider mode
    if (selectedProviders.value.length > 1) {
      // In multi-provider mode, add to batch and continue
      nextTick(() => {
        addListToBatch()
      })
    } else {
      // Single provider mode, proceed to step 3 (sync options)
      nextTick(() => {
        currentStep.value = 3
      })
    }
  }
}

// Handler for IMDb Preset selection
const handleImdbPresetSelect = (presetValue: string) => {
  listId.value = presetValue
  error.value = ''
  // Check if we're in multi-provider mode
  if (selectedProviders.value.length > 1) {
    // In multi-provider mode, add to batch and continue
    nextTick(() => {
      if (validateInput()) {
        addListToBatch()
      }
    })
  } else {
    // Single provider mode, proceed to step 3 (sync options)
    nextTick(() => {
      if (validateInput()) {
        currentStep.value = 3
      }
    })
  }
}

// Handler for Steven Lu selection
const handleStevenLuSelect = () => {
  listId.value = 'stevenlu'
  error.value = ''
  // Check if we're in multi-provider mode
  if (selectedProviders.value.length > 1) {
    // In multi-provider mode, add to batch and continue
    nextTick(() => {
      if (validateInput()) {
        addListToBatch()
      }
    })
  } else {
    // Single provider mode, proceed to step 3 (sync options)
    nextTick(() => {
      if (validateInput()) {
        currentStep.value = 3
      }
    })
  }
}

const validateInput = () => {
  error.value = ''
  
  // For Trakt Special, validate selections instead of text input
  if (isTraktSpecial.value) {
    if (!selectedTraktType.value || !selectedTraktMedia.value) {
      error.value = 'Please select both list type and media type'
      return false
    }
    return true
  }
  
  const value = listId.value.trim()

  if (!value) {
    error.value = 'This field is required'
    return false
  }

  // Basic validation based on source
  if (selectedSource.value === 'imdb') {
    // Accept chart names (top, boxoffice, moviemeter, tvmeter), list IDs (ls...), or URLs
    const validCharts = ['top', 'boxoffice', 'moviemeter', 'tvmeter']
    const isChartName = validCharts.includes(value.toLowerCase())
    const isListId = value.match(/^ls\d+$/) // More specific: ls followed by digits only
    const isUrl = value.includes('imdb.com')
    
    if (!isChartName && !isListId && !isUrl) {
      error.value = 'Enter "top" or a list ID like "ls026785255"'
      return false
    }
  } else if (selectedSource.value === 'stevenlu') {
    // Steven Lu: accept "stevenlu" or the URL
    if (value !== 'stevenlu' && !value.includes('stevenlu.com')) {
      error.value = 'Enter "stevenlu" or the Steven Lu URL'
      return false
    }
  } else if (selectedSource.value === 'trakt') {
    // Trakt: validate URL format (accept both custom lists and watchlists)
    const isTraktUrl = value.includes('trakt.tv/users/')
    const hasValidEndpoint = value.includes('/lists/') || value.includes('/watchlist')
    
    if (!isTraktUrl || !hasValidEndpoint) {
      error.value = 'Enter a valid Trakt URL: https://trakt.tv/users/{user}/watchlist or /lists/{name}'
      return false
    }
  } else if (selectedSource.value === 'letterboxd') {
    // Letterboxd: validate URL format (accept both custom lists and watchlists)
    const isLetterboxdUrl = value.startsWith('https://letterboxd.com/')
    const hasValidEndpoint = value.includes('/list/') || value.includes('/watchlist')
    
    if (!isLetterboxdUrl || !hasValidEndpoint) {
      error.value = 'Enter a valid Letterboxd URL: https://letterboxd.com/{user}/list/{name}/ or /watchlist/'
      return false
    }
  } else if (selectedSource.value === 'mdblist') {
    // MDBList: validate URL format
    if (!value.startsWith('https://mdblist.com/lists/')) {
      error.value = 'Enter a valid MDBList URL: https://mdblist.com/lists/{user}/{name}'
      return false
    }
  } else if (selectedSource.value === 'tmdb') {
    // TMDB: validate URL format
    if (!value.startsWith('https://www.themoviedb.org/list/')) {
      error.value = 'Enter a valid TMDB URL: https://www.themoviedb.org/list/{id-name}'
      return false
    }
  } else if (selectedSource.value === 'simkl') {
    // Simkl: validate URL format
    if (!value.startsWith('https://simkl.com/') || !value.includes('/list/')) {
      error.value = 'Enter a valid Simkl URL: https://simkl.com/{id}/list/{id}/{name}'
      return false
    }
  } else if (selectedSource.value === 'tvdb') {
    // TVDB: validate URL format
    if (!value.startsWith('https://www.thetvdb.com/lists/')) {
      error.value = 'Enter a valid TVDB URL: https://www.thetvdb.com/lists/{idorname}'
      return false
    }
  } else if (selectedSource.value === 'anilist') {
    // AniList: validate URL format or username
    const isAniListUrl = value.startsWith('https://anilist.co/user/') && value.includes('/animelist')
    const isUsername = /^[a-zA-Z0-9_-]+$/.test(value)
    
    if (!isAniListUrl && !isUsername) {
      error.value = 'Enter a valid AniList URL or username: https://anilist.co/user/{username}/animelist or just username'
      return false
    }
  }

  return true
}

const getSyncButtonText = () => {
  const options = {
    schedule: 'Schedule',
    single: 'Sync This',
    all: 'Sync All'
  }
  return options[selectedSyncOption.value]
}

const handleNext = () => {
  if (currentStep.value === 1) {
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    if (validateInput()) {
      currentStep.value = 3
    }
  } else {
    handleSubmit()
  }
}

const handleSubmit = async () => {
  if (!validateInput()) return

  loading.value = true
  error.value = ''

  try {
    const listsStore = useListsStore()
    const syncStore = useSyncStore()
    
    // For Trakt Special, construct the list_id from selections
    let finalListId = listId.value.trim()
    let finalListType = selectedSource.value
    
    if (isTraktSpecial.value) {
      finalListId = `${selectedTraktType.value}:${selectedTraktMedia.value}`
      finalListType = 'trakt_special'
    }
    
    // Step 1: Add the list
    await listsStore.addList({
      list_type: finalListType,
      list_id: finalListId,
    })

    showSuccess('List Added', `Successfully added ${finalListType} list`)
    
    // Step 2: Handle sync option
    if (selectedSyncOption.value === 'single') {
      // Sync just this list
      showSuccess('Syncing List', 'Starting sync for this list...')
      const api = useApiService()
      await api.syncSingleList(finalListType, finalListId)
      navigateTo('/sync')
    } else if (selectedSyncOption.value === 'all') {
      // Sync all lists
      showSuccess('Syncing All', 'Starting sync for all lists...')
      await syncStore.triggerSync()
      navigateTo('/sync')
    } else {
      // Just schedule for next sync
      showSuccess('Scheduled', 'List will sync during the next scheduled interval')
    }

    emit('list-added')
    handleClose()
  } catch (err: any) {
    error.value = err.message || 'Failed to add list'
    showError('Failed to add list', err.message)
  } finally {
    loading.value = false
  }
}

const handleSubmitMultiple = async () => {
  if (listsToAdd.value.length === 0) return

  loading.value = true
  error.value = ''

  try {
    const listsStore = useListsStore()
    const syncStore = useSyncStore()
    
    // Add all lists
    for (const list of listsToAdd.value) {
      await listsStore.addList({
        list_type: list.listType,
        list_id: list.listId,
      })
    }

    showSuccess('Lists Added', `Successfully added ${listsToAdd.value.length} lists`)
    
    // Handle sync option
    if (selectedSyncOption.value === 'single') {
      // Sync just these lists
      showSuccess('Syncing Lists', `Starting sync for ${listsToAdd.value.length} lists...`)
      const api = useApiService()
      
      // Track sync results
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // Sync each list with individual error handling
      for (const list of listsToAdd.value) {
        try {
          console.log(`[Add List Modal] Starting sync for ${list.listType}:${list.listId}`)
          await api.syncSingleList(list.listType, list.listId)
          successCount++
          console.log(`[Add List Modal] Successfully triggered sync for ${list.listType}:${list.listId}`)
        } catch (error: any) {
          failCount++
          const errorMsg = `${list.displayName}: ${error.message || 'Failed to sync'}`
          errors.push(errorMsg)
          console.error(`[Add List Modal] Failed to sync ${list.listType}:${list.listId}:`, error)
        }
      }
      
      // Show summary of sync results
      if (successCount > 0) {
        showSuccess('Syncs Started', `Started ${successCount} of ${listsToAdd.value.length} list syncs`)
      }
      if (failCount > 0) {
        showError('Some Syncs Failed', `${failCount} list(s) failed to start: ${errors.join(', ')}`)
      }
      
      // Navigate to sync page to monitor progress
      navigateTo('/sync')
    } else if (selectedSyncOption.value === 'all') {
      // Sync all lists
      showSuccess('Syncing All', 'Starting sync for all lists...')
      await syncStore.triggerSync()
      navigateTo('/sync')
    } else {
      // Just schedule for next sync
      showSuccess('Scheduled', `${listsToAdd.value.length} lists will sync during the next scheduled interval`)
    }

    emit('list-added')
    handleClose()
  } catch (err: any) {
    error.value = err.message || 'Failed to add lists'
    showError('Failed to add lists', err.message)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  isOpen.value = false
  // Reset form after a delay
  setTimeout(() => {
    currentStep.value = 1
    selectedSource.value = ''
    listId.value = ''
    selectedTraktType.value = ''
    selectedTraktMedia.value = ''
    selectedSyncOption.value = 'schedule'
    error.value = ''
    currentPage.value = 1
    listsToAdd.value = []
    isAddingMultiple.value = false
    selectedProviders.value = []
    currentProvider.value = ''
  }, 300)
}
</script>

