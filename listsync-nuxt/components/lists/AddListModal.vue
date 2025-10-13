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
          v-for="step in 3"
          :key="step"
          :class="[
            'h-2 rounded-full transition-all',
            step === currentStep ? 'w-8 bg-purple-500' : step < currentStep ? 'w-6 bg-purple-500/50' : 'w-6 bg-white/10'
          ]"
        />
      </div>

      <!-- Step 1: Choose Source -->
      <div v-if="currentStep === 1" class="space-y-4">
        <p class="text-sm text-muted-foreground">
          Select the source of your list
        </p>

        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="source in sources"
            :key="source.value"
            :class="getSourceButtonClass(source.value)"
            @click="selectSource(source.value)"
          >
            <component :is="source.icon" :size="24" />
            <span class="font-medium">{{ source.label }}</span>
          </button>
        </div>
      </div>

      <!-- Step 2: Enter Details -->
      <div v-else-if="currentStep === 2" class="space-y-4">
        <div class="flex items-center gap-2 mb-4">
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
            v-if="currentStep > 1"
            variant="secondary"
            :disabled="loading"
            @click="currentStep--"
          >
            Back
          </Button>

          <Button
            variant="primary"
            :disabled="!canProceed"
            :loading="loading"
            @click="handleNext"
          >
            {{ currentStep === 1 ? 'Next' : currentStep === 2 ? 'Next' : 'Add List & ' + getSyncButtonText() }}
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

// Sources
const sources = [
  { label: 'IMDb', value: 'imdb', icon: FilmIcon },
  { label: 'Trakt', value: 'trakt', icon: TvIcon },
  { label: 'Trakt Special', value: 'trakt_special', icon: TvIcon },
  { label: 'Letterboxd', value: 'letterboxd', icon: FilmIcon },
  { label: 'MDBList', value: 'mdblist', icon: DatabaseIcon },
  { label: 'Steven Lu', value: 'stevenlu', icon: DatabaseIcon },
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
const isUrlRequired = computed(() => {
  return ['letterboxd', 'mdblist'].includes(selectedSource.value)
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
  const sourceMap: Record<string, any> = {
    imdb: FilmIcon,
    trakt: TvIcon,
    trakt_special: TvIcon,
    letterboxd: FilmIcon,
    mdblist: DatabaseIcon,
    stevenlu: DatabaseIcon,
  }
  return sourceMap[source] || DatabaseIcon
}

// Get placeholder text
const getPlaceholder = (source: string) => {
  const placeholders: Record<string, string> = {
    imdb: 'top, boxoffice, moviemeter, ls123456789, or full URL',
    trakt: 'https://app.trakt.tv/users/username/lists/name',
    trakt_special: 'Select from predefined lists below',
    letterboxd: 'https://letterboxd.com/username/list/...',
    mdblist: 'https://mdblist.com/lists/...',
    stevenlu: 'https://movies.stevenlu.com or stevenlu',
  }
  return placeholders[source] || 'Enter list ID or URL'
}

// Get helper text
const getHelperText = (source: string) => {
  const helpers: Record<string, string> = {
    imdb: 'Enter a chart name (top, boxoffice, moviemeter, tvmeter), list ID (ls...), or full URL',
    trakt: 'Enter the full Trakt user list URL from your browser (e.g., https://app.trakt.tv/users/username/lists/name)',
    trakt_special: 'Select a list type and media type from the dropdowns below to sync curated Trakt lists',
    letterboxd: 'Enter the full Letterboxd list URL',
    mdblist: 'Enter the full MDBList URL',
    stevenlu: 'Click the button above to sync Steven Lu\'s curated movie collection',
  }
  return helpers[source] || 'Enter the list identifier'
}

// Get source button class
const getSourceButtonClass = (source: string) => {
  const isSelected = selectedSource.value === source
  
  const baseClasses = [
    'flex flex-col items-center gap-3 p-6 rounded-lg border transition-all',
  ]

  if (isSelected) {
    return [
      ...baseClasses,
      'bg-purple-500/20 border-purple-500/40 text-purple-300',
      'shadow-sm shadow-purple-500/20',
    ].join(' ')
  }

  return [
    ...baseClasses,
    'bg-black/20 border-border text-muted-foreground',
    'hover:bg-white/5 hover:border-purple-500/30 hover:text-foreground',
  ].join(' ')
}

// Handlers
const selectSource = (source: string) => {
  selectedSource.value = source
  // Auto-proceed to step 2 for all sources
  currentStep.value = 2
}

// Handler for Trakt Special selections
const handleTraktTypeSelect = (type: string) => {
  selectedTraktType.value = type
  // Don't auto-proceed yet, wait for media type selection
}

const handleTraktMediaSelect = (media: string) => {
  selectedTraktMedia.value = media
  // Auto-proceed to step 3 once both are selected
  if (selectedTraktType.value && selectedTraktMedia.value) {
    nextTick(() => {
      currentStep.value = 3
    })
  }
}

// Handler for IMDb Preset selection
const handleImdbPresetSelect = (presetValue: string) => {
  listId.value = presetValue
  error.value = ''
  // Auto-proceed to step 3
  nextTick(() => {
    if (validateInput()) {
      currentStep.value = 3
    }
  })
}

// Handler for Steven Lu selection
const handleStevenLuSelect = () => {
  listId.value = 'stevenlu'
  error.value = ''
  // Auto-proceed to step 3
  nextTick(() => {
    if (validateInput()) {
      currentStep.value = 3
    }
  })
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
    const isListId = value.match(/^(ls\d+|ur\d+)/)
    const isUrl = value.includes('imdb.com')
    
    if (!isChartName && !isListId && !isUrl) {
      error.value = 'Invalid IMDb list ID, chart name, or URL'
      return false
    }
  } else if (selectedSource.value === 'stevenlu') {
    // Steven Lu: just accept the value (should be "stevenlu")
    return true
  } else if (['letterboxd', 'mdblist'].includes(selectedSource.value)) {
    if (!value.startsWith('http')) {
      error.value = 'Please enter a valid URL'
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
  }, 300)
}
</script>

