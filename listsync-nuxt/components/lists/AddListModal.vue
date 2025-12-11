<template>
  <Modal
    v-model="isOpen"
    title="Add New List"
    size="full"
    @close="handleClose"
  >
    <!-- Main Split Layout -->
    <div class="flex flex-col sm:flex-row h-[70vh] sm:h-[650px] max-h-[600px] sm:max-h-none -mx-4 sm:-mx-6 -my-3 sm:-my-4">
      <!-- Left Panel: Configuration Steps -->
      <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <!-- Step Indicator -->
        <div class="px-4 sm:px-6 pt-5 pb-4 border-b border-purple-500/10 bg-purple-500/5">
          <div class="flex items-center justify-center gap-2 sm:gap-4">
            <button
              v-for="step in 3"
              :key="step"
              type="button"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all',
                currentStep === step
                  ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30'
                  : currentStep > step
                    ? 'bg-purple-500/30 text-purple-300 cursor-pointer hover:bg-purple-500/40'
                    : 'bg-white/5 text-muted-foreground'
              ]"
              :disabled="currentStep < step"
              @click="currentStep > step && (currentStep = step)"
            >
              <span class="w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold"
                :class="currentStep >= step ? 'bg-white/20' : 'bg-white/10'"
              >
                {{ step }}
              </span>
              <span class="hidden sm:inline">{{ stepLabels[step - 1] }}</span>
            </button>
          </div>
        </div>

        <!-- Step Content -->
        <div class="flex-1 overflow-y-auto px-4 sm:px-6 py-4 custom-scrollbar">
          <!-- Step 1: Choose Provider -->
          <div v-if="currentStep === 1" class="space-y-5">
            <div class="text-center mb-6">
              <p class="text-lg font-bold text-foreground">Select a Provider</p>
              <p class="text-sm text-muted-foreground mt-2">Choose where your list is from</p>
            </div>

            <!-- Collections Banner -->
            <button
              class="w-full p-3 sm:p-4 rounded-xl border border-purple-500/30 bg-gradient-to-r from-purple-500/10 to-purple-600/10 hover:from-purple-500/20 hover:to-purple-600/20 transition-all group"
              @click="handleCollectionsRedirect"
            >
              <div class="flex items-center gap-3 sm:gap-4">
                <div class="p-2 sm:p-3 rounded-lg bg-purple-500/20">
                  <component :is="LayersIcon" :size="20" class="sm:w-6 sm:h-6 text-purple-400" />
                </div>
                <div class="flex-1 text-left">
                  <span class="font-medium text-foreground text-sm sm:text-base">Collections</span>
                  <span class="text-xs sm:text-sm text-muted-foreground ml-2">Browse popular movie collections</span>
                </div>
                <component :is="ChevronRightIcon" :size="18" class="sm:w-5 sm:h-5 text-purple-400 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            <!-- Provider Grid -->
            <div class="grid grid-cols-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 sm:gap-3">
              <button
                v-for="source in sources"
                :key="source.value"
                type="button"
                :class="[
                  'p-3 sm:p-4 rounded-xl border-2 transition-all text-center group',
                  'hover:scale-[1.02] hover:shadow-lg',
                  selectedSource === source.value
                    ? `${source.borderColor} ${source.bgColor}`
                    : 'border-border bg-black/20 hover:border-purple-500/40'
                ]"
                @click="selectSource(source.value)"
              >
                <div :class="['p-2 sm:p-3 rounded-lg mx-auto w-fit mb-2', source.bgColor]">
                  <component :is="source.icon" :size="20" class="sm:w-6 sm:h-6" :class="source.color" />
                </div>
                <span class="text-xs sm:text-sm font-medium text-foreground block">{{ source.label }}</span>
                <span v-if="hasPresets(source.value)" class="text-[9px] sm:text-[10px] text-purple-400 mt-0.5 block">
                  {{ getPresetCount(source.value) }} presets
                </span>
              </button>
            </div>
          </div>

          <!-- Step 2: Select List -->
          <div v-else-if="currentStep === 2" class="space-y-4">
            <!-- Back + Provider Badge -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="p-1 rounded hover:bg-white/5 transition-colors"
                @click="currentStep = 1"
              >
                <component :is="ChevronLeftIcon" :size="18" class="text-muted-foreground" />
              </button>
              <Badge variant="primary" size="sm">
                <component :is="getSourceIcon(selectedSource)" :size="12" />
                {{ formatListSource(selectedSource) }}
              </Badge>
            </div>

            <!-- Trakt Special Selection - Categorized like other providers -->
            <div v-if="isTraktSpecial" class="space-y-3">
              <!-- Search -->
              <div class="relative">
                <component :is="SearchIcon" :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  v-model="presetSearch"
                  type="text"
                  placeholder="Search Trakt lists..."
                  class="w-full pl-8 pr-3 py-2 rounded-lg bg-black/20 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-all"
                />
              </div>

              <!-- Trakt Presets Grid -->
              <div class="space-y-3 max-h-[280px] sm:max-h-[350px] overflow-y-auto custom-scrollbar pr-1">
                <div v-for="category in filteredTraktSpecialPresets" :key="category.category" class="space-y-2">
                  <button
                    type="button"
                    @click="toggleCategory(`trakt_special-${category.category}`)"
                    class="w-full flex items-center justify-between p-2 rounded-lg bg-black/30 hover:bg-black/40 transition-colors"
                  >
                    <div class="flex items-center gap-2">
                      <component :is="category.category === 'Movies' ? FilmIcon : TvIcon" :size="14" :class="category.category === 'Movies' ? 'text-purple-400' : 'text-green-400'" />
                      <span class="text-xs font-semibold text-foreground uppercase tracking-wider">
                        {{ category.category }}
                      </span>
                      <span class="text-[10px] text-muted-foreground">({{ category.items.length }})</span>
                    </div>
                    <component 
                      :is="isCategoryCollapsed(`trakt_special-${category.category}`) ? ChevronDownIcon : ChevronUpIcon" 
                      :size="14" 
                      class="text-muted-foreground"
                    />
                  </button>
                  
                  <div 
                    v-show="!isCategoryCollapsed(`trakt_special-${category.category}`)"
                    class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2"
                  >
                    <button
                      v-for="preset in category.items"
                      :key="`${preset.type}-${preset.media}`"
                      type="button"
                      :class="[
                        'group relative p-3 rounded-xl border-2 text-left transition-all hover:scale-[1.01] hover:shadow-md',
                        selectedTraktType === preset.type && selectedTraktMedia === preset.media
                          ? 'border-purple-500 bg-purple-500/20'
                          : 'border-border bg-black/20 hover:border-purple-500/40'
                      ]"
                      @click="handleTraktSpecialPresetSelect(preset.type, preset.media)"
                    >
                      <div class="flex items-start gap-2.5">
                        <div :class="[
                          'p-1.5 rounded-lg transition-colors flex-shrink-0',
                          selectedTraktType === preset.type && selectedTraktMedia === preset.media
                            ? 'bg-purple-500/30' 
                            : 'bg-white/5 group-hover:bg-white/10'
                        ]">
                          <component :is="ZapIcon" :size="14" class="text-purple-400" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs sm:text-sm font-medium text-foreground truncate">{{ preset.label }}</p>
                          <p class="text-[10px] text-muted-foreground mt-0.5">Trakt {{ category.category }}</p>
                        </div>
                        <div class="flex items-center gap-1.5 flex-shrink-0">
                          <button
                            type="button"
                            class="p-1 rounded-md bg-black/20 hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-500/50 transition-all opacity-0 group-hover:opacity-100"
                            title="Preview on Trakt"
                            @click.stop="openTraktSpecialUrl(preset.type, preset.media)"
                          >
                            <component :is="ExternalLinkIcon" :size="12" class="text-purple-400" />
                          </button>
                          <component 
                            v-if="selectedTraktType === preset.type && selectedTraktMedia === preset.media" 
                            :is="CheckIcon" 
                            :size="16" 
                            class="text-purple-400" 
                          />
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
                
                <div v-if="filteredTraktSpecialPresets.length === 0" class="text-center py-6 text-muted-foreground text-sm">
                  No presets found matching your search
                </div>
              </div>
            </div>

            <!-- Provider with Presets -->
            <div v-else-if="hasPresets(selectedSource)" class="space-y-3">
              <!-- Search -->
              <div class="relative">
                <component :is="SearchIcon" :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  v-model="presetSearch"
                  type="text"
                  placeholder="Search presets..."
                  class="w-full pl-8 pr-3 py-2 rounded-lg bg-black/20 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-all"
                />
              </div>

              <!-- Preset Grid with Rich Cards -->
              <div class="space-y-3 max-h-[280px] sm:max-h-[350px] overflow-y-auto custom-scrollbar pr-1">
                <div v-for="category in currentFilteredPresets" :key="category.category" class="space-y-2">
                  <button
                    type="button"
                    @click="toggleCategory(`${selectedSource}-${category.category}`)"
                    class="w-full flex items-center justify-between p-2 rounded-lg bg-black/30 hover:bg-black/40 transition-colors"
                  >
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-semibold text-foreground uppercase tracking-wider">
                        {{ category.category }}
                      </span>
                      <span class="text-[10px] text-muted-foreground">({{ category.items.length }})</span>
                    </div>
                    <component 
                      :is="isCategoryCollapsed(`${selectedSource}-${category.category}`) ? ChevronDownIcon : ChevronUpIcon" 
                      :size="14" 
                      class="text-muted-foreground"
                    />
                  </button>
                  
                  <div 
                    v-show="!isCategoryCollapsed(`${selectedSource}-${category.category}`)"
                    class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2"
                  >
                    <button
                      v-for="preset in category.items"
                      :key="preset.value"
                      type="button"
                      :class="[
                        'group relative p-3 rounded-xl border-2 text-left transition-all hover:scale-[1.01] hover:shadow-md',
                        listId === preset.value
                          ? `${getProviderColor(selectedSource).border} ${getProviderColor(selectedSource).bg}`
                          : 'border-border bg-black/20 hover:border-purple-500/40'
                      ]"
                      @click="handlePresetSelect(preset.value, preset.label)"
                    >
                      <div class="flex items-start gap-2.5">
                        <div :class="[
                          'p-1.5 rounded-lg transition-colors flex-shrink-0',
                          listId === preset.value 
                            ? getProviderColor(selectedSource).bg 
                            : 'bg-white/5 group-hover:bg-white/10'
                        ]">
                          <component :is="getSourceIcon(selectedSource)" :size="14" :class="getSourceColor(selectedSource).color" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs sm:text-sm font-medium text-foreground truncate">{{ preset.label }}</p>
                          <p class="text-[10px] text-muted-foreground mt-0.5">{{ formatListSource(selectedSource) }}</p>
                        </div>
                        <div class="flex items-center gap-1.5 flex-shrink-0">
                          <button
                            v-if="getPresetUrl(selectedSource, preset.value)"
                            type="button"
                            class="p-1 rounded-md bg-black/20 hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-500/50 transition-all opacity-0 group-hover:opacity-100"
                            title="Preview on website"
                            @click.stop="openPresetUrl($event, selectedSource, preset.value)"
                          >
                            <component :is="ExternalLinkIcon" :size="12" class="text-purple-400" />
                          </button>
                          <component 
                            v-if="listId === preset.value" 
                            :is="CheckIcon" 
                            :size="16" 
                            :class="getSourceColor(selectedSource).color" 
                          />
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
                
                <div v-if="currentFilteredPresets.length === 0" class="text-center py-6 text-muted-foreground text-sm">
                  No presets found matching your search
                </div>
              </div>

              <!-- Custom Input Divider -->
              <div class="relative py-2">
                <div class="absolute inset-0 flex items-center">
                  <div class="w-full border-t border-border"></div>
                </div>
                <div class="relative flex justify-center text-[10px] uppercase">
                  <span class="bg-background px-2 text-muted-foreground">Or enter custom</span>
                </div>
              </div>

              <!-- Custom Input -->
              <Input
                v-model="listId"
                :placeholder="getPlaceholder(selectedSource)"
                :error="error"
                @blur="validateInput"
                @keydown.enter="handleAddList"
              />
            </div>

            <!-- Provider without Presets (Custom Input Only) -->
            <div v-else class="space-y-3">
              <Input
                v-model="listId"
                :label="`${formatListSource(selectedSource)} List ${isUrlRequired ? 'URL' : 'ID'}`"
                :placeholder="getPlaceholder(selectedSource)"
                :error="error"
                @blur="validateInput"
                @keydown.enter="handleAddList"
              />
              
              <div class="flex items-start gap-2 p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <component :is="InfoIcon" :size="14" class="text-purple-400 flex-shrink-0 mt-0.5" />
                <p class="text-[11px] text-muted-foreground leading-relaxed">
                  {{ getHelperText(selectedSource) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Step 3: Confirm -->
          <div v-else-if="currentStep === 3" class="space-y-5">
            <div class="text-center mb-6">
              <div class="flex justify-center mb-4">
                <div class="relative">
                  <!-- Subtle glow -->
                  <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-green-500/20 rounded-full blur-xl" />
                  
                  <!-- Logo Image -->
                  <div class="relative">
                    <img 
                      :src="logoImage" 
                      alt="ListSync Logo" 
                      class="w-20 h-20 object-contain relative z-10"
                    />
                    
                    <!-- Success checkmark badge -->
                    <div class="absolute -top-1 -right-1 bg-gradient-to-br from-green-400 to-green-600 rounded-full p-1.5 shadow-lg">
                      <component :is="CheckIcon" class="w-4 h-4 text-white" />
                    </div>
                  </div>
                </div>
              </div>
              <p class="text-lg font-bold text-foreground">Ready to Add</p>
              <p class="text-sm text-muted-foreground mt-2">
                {{ listsToAdd.length }} list{{ listsToAdd.length !== 1 ? 's' : '' }} will be added
              </p>
            </div>

            <!-- Summary -->
            <div class="p-4 rounded-xl bg-black/30 border border-border space-y-3">
              <div v-for="list in listsToAdd" :key="list.id" class="flex items-center gap-3 text-sm">
                <div :class="['p-2 rounded-lg', getSourceColor(list.source || list.listType || '').bgColor]">
                  <component :is="getSourceIcon(list.source || list.listType || '')" :size="16" :class="getSourceColor(list.source || list.listType || '').color" />
                </div>
                <span class="flex-1 truncate text-foreground">{{ list.displayName }}</span>
                <span class="text-muted-foreground">{{ formatListSource(list.source || list.listType || '') }}</span>
              </div>
            </div>

            <!-- Add More Button -->
            <button
              type="button"
              class="w-full flex items-center justify-center gap-3 p-4 rounded-xl border-2 border-dashed border-purple-500/30 text-purple-400 text-sm font-semibold hover:bg-purple-500/10 hover:border-purple-500/50 transition-all"
              @click="addAnotherList"
            >
              <component :is="PlusIcon" :size="18" />
              Add Another List
            </button>
          </div>
        </div>
      </div>

      <!-- Right Panel: Selection Sidebar (Desktop) / Bottom Sheet (Mobile) -->
      <div class="hidden sm:flex w-80 flex-shrink-0">
        <SelectedListsSidebar
          :lists="allSelectedLists"
          :users="usersStore.users"
          :selected-user-id="selectedUserId"
          :selected-sync-option="selectedSyncOption"
          :overseerr-url="overseerrUrl"
          @remove="removeListFromBatch"
          @update:selected-user-id="selectedUserId = $event"
          @update:selected-sync-option="selectedSyncOption = $event"
        />
      </div>

      <!-- Mobile: Collapsed Sidebar Summary -->
      <div class="sm:hidden border-t border-purple-500/20 px-4 py-3 bg-black/30">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-xs text-muted-foreground">{{ listsToAdd.length }} list{{ listsToAdd.length !== 1 ? 's' : '' }}</span>
            <span class="text-xs text-muted-foreground">|</span>
            <span class="text-xs text-foreground">{{ usersStore.users.find(u => String(u.id) === selectedUserId)?.display_name || 'User' }}</span>
          </div>
          <button
            type="button"
            class="text-xs text-purple-400 hover:text-purple-300"
            @click="showMobileSidebar = true"
          >
            Configure
          </button>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <Button variant="ghost" @click="handleClose">
          Cancel
        </Button>

        <div class="flex items-center gap-2">
          <!-- Step 1: No action needed, just select provider -->
          
          <!-- Step 2: Add List Button -->
          <Button
            v-if="currentStep === 2"
            variant="primary"
            :disabled="!canProceed"
            :loading="loading"
            @click="handleAddList"
          >
            <component :is="PlusIcon" :size="14" class="mr-1" />
            Add List
          </Button>

          <!-- Step 3: Submit Button -->
          <Button
            v-if="currentStep === 3"
            variant="primary"
            :disabled="listsToAdd.length === 0"
            :loading="loading"
            @click="handleSubmitAll"
          >
            {{ getSubmitButtonText() }}
          </Button>
        </div>
      </div>
    </template>

    <!-- Mobile Sidebar Modal -->
    <Teleport to="body">
      <Transition name="slide-up">
        <div
          v-if="showMobileSidebar"
          class="sm:hidden fixed inset-0 z-[60] flex items-end"
          @click.self="showMobileSidebar = false"
        >
          <div class="absolute inset-0 bg-black/80" />
          <div class="relative w-full max-h-[70vh] bg-card rounded-t-2xl overflow-hidden">
            <div class="p-4 border-b border-border flex items-center justify-between">
              <h3 class="text-sm font-semibold text-foreground">Configuration</h3>
              <button
                type="button"
                class="p-1 rounded hover:bg-white/10"
                @click="showMobileSidebar = false"
              >
                <component :is="XIcon" :size="18" />
              </button>
            </div>
            <div class="overflow-y-auto max-h-[calc(70vh-60px)]">
              <SelectedListsSidebar
                :lists="allSelectedLists"
                :users="usersStore.users"
                :selected-user-id="selectedUserId"
                :selected-sync-option="selectedSyncOption"
                :overseerr-url="overseerrUrl"
                @remove="removeListFromBatch"
                @update:selected-user-id="selectedUserId = $event"
                @update:selected-sync-option="selectedSyncOption = $event"
              />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
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
  ChevronDown as ChevronDownIcon,
  ChevronUp as ChevronUpIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  BookOpen as BookOpenIcon,
  Globe as GlobeIcon,
  Zap as ZapIcon,
  Heart as HeartIcon,
  Calendar as CalendarIcon,
  Plus as PlusIcon,
  X as XIcon,
  Sparkles as SparklesIcon,
  Check as CheckIcon,
  CheckCircle as CheckCircleIcon,
  Layers as LayersIcon,
  Search as SearchIcon,
  ExternalLink as ExternalLinkIcon,
} from 'lucide-vue-next'
import { useSyncStore } from '~/stores/sync'
import { useUsersStore } from '~/stores/users'
import SelectedListsSidebar from './SelectedListsSidebar.vue'
import logoImage from '~/assets/images/list-sync-logo.webp'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'list-added': []
}>()

const { showSuccess, showError } = useToast()
const router = useRouter()
const usersStore = useUsersStore()
const api = useApiService()

// State
const currentStep = ref(1)
const selectedSource = ref('')
const listId = ref('')
const error = ref('')
const loading = ref(false)
const selectedSyncOption = ref<'all' | 'single' | 'schedule'>('single')
const selectedUserId = ref('1')
const presetSearch = ref('')
const showMobileSidebar = ref(false)
const userManuallySelected = ref(false)
const overseerrUrl = ref('')

// Collapsed categories state
const collapsedCategories = ref<Record<string, boolean>>({})

// Multi-list state
const listsToAdd = ref<Array<{
  id: string
  source: string
  listId: string
  displayName: string
  listType?: string
  mediaType?: string
}>>([])

// Trakt Special state
const selectedTraktType = ref('')
const selectedTraktMedia = ref('')

// Step labels
const stepLabels = ['Provider', 'List', 'Confirm']

// Computed for v-model
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// Load default user and config when modal opens
watch(() => props.modelValue, async (newValue, oldValue) => {
  if (newValue && !oldValue) {
    userManuallySelected.value = false
    try {
      const [config] = await Promise.all([
        api.getConfig(),
        usersStore.fetchUsers()
      ])
      
      // Store Overseerr URL for avatar images
      if (config.overseerr_url) {
        overseerrUrl.value = config.overseerr_url
      }
      
      const configuredUserId = config.overseerr_user_id || '1'
      const userExists = usersStore.users.some(user => String(user.id) === String(configuredUserId))
      
      if (!userManuallySelected.value) {
        if (userExists) {
          selectedUserId.value = String(configuredUserId)
        } else if (usersStore.users.length > 0) {
          selectedUserId.value = String(usersStore.users[0].id)
        } else {
          selectedUserId.value = '1'
        }
      }
    } catch (error) {
      console.error('Failed to load default user:', error)
      if (!userManuallySelected.value) {
        selectedUserId.value = '1'
      }
      usersStore.fetchUsers().catch(err => console.error('Failed to fetch users:', err))
    }
  }
})

// Track manual user selection
watch(selectedUserId, (newUserId, oldUserId) => {
  if (oldUserId && newUserId !== oldUserId && props.modelValue) {
    userManuallySelected.value = true
  }
})

// Sources configuration
const sources = [
  { label: 'IMDb', value: 'imdb', icon: StarIcon, color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', borderColor: 'border-yellow-500/40' },
  { label: 'Trakt', value: 'trakt', icon: TrendingUpIcon, color: 'text-green-400', bgColor: 'bg-green-500/20', borderColor: 'border-green-500/40' },
  { label: 'Trakt Special', value: 'trakt_special', icon: ZapIcon, color: 'text-purple-400', bgColor: 'bg-purple-500/20', borderColor: 'border-purple-500/40' },
  { label: 'Letterboxd', value: 'letterboxd', icon: BookOpenIcon, color: 'text-pink-400', bgColor: 'bg-pink-500/20', borderColor: 'border-pink-500/40' },
  { label: 'MDBList', value: 'mdblist', icon: DatabaseIcon, color: 'text-purple-400', bgColor: 'bg-purple-500/20', borderColor: 'border-purple-500/40' },
  { label: 'Steven Lu', value: 'stevenlu', icon: HeartIcon, color: 'text-red-400', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/40' },
  { label: 'TMDB', value: 'tmdb', icon: GlobeIcon, color: 'text-cyan-400', bgColor: 'bg-cyan-500/20', borderColor: 'border-cyan-500/40' },
  { label: 'TVDB', value: 'tvdb', icon: CalendarIcon, color: 'text-indigo-400', bgColor: 'bg-indigo-500/20', borderColor: 'border-indigo-500/40' },
  { label: 'AniList', value: 'anilist', icon: SparklesIcon, color: 'text-amber-400', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/40' },
]

// Trakt special options
const traktSpecialTypes = [
  { label: 'Trending', value: 'trending' },
  { label: 'Popular', value: 'popular' },
  { label: 'Anticipated', value: 'anticipated' },
  { label: 'Watched', value: 'watched' },
  { label: 'Box Office', value: 'boxoffice' },
]

const traktMediaTypes = [
  { label: 'Movies', value: 'movies' },
  { label: 'TV Shows', value: 'shows' },
]

// Trakt Special presets organized by category (Movies/TV Shows)
const traktSpecialPresets = [
  {
    category: 'Movies',
    items: [
      { label: 'Trending Movies', type: 'trending', media: 'movies' },
      { label: 'Popular Movies', type: 'popular', media: 'movies' },
      { label: 'Anticipated Movies', type: 'anticipated', media: 'movies' },
      { label: 'Most Watched Movies', type: 'watched', media: 'movies' },
      { label: 'Box Office', type: 'boxoffice', media: 'movies' },
    ]
  },
  {
    category: 'TV Shows',
    items: [
      { label: 'Trending Shows', type: 'trending', media: 'shows' },
      { label: 'Popular Shows', type: 'popular', media: 'shows' },
      { label: 'Anticipated Shows', type: 'anticipated', media: 'shows' },
      { label: 'Most Watched Shows', type: 'watched', media: 'shows' },
    ]
  },
]

// Presets data
const imdbPresets = [
  {
    category: 'Top Lists',
    items: [
      { label: 'Top 250 Movies', value: 'top' },
      { label: 'Box Office', value: 'boxoffice' },
      { label: 'MovieMeter', value: 'moviemeter' },
      { label: 'TVMeter', value: 'tvmeter' },
    ]
  },
  {
    category: 'Film Festivals',
    items: [
      { label: 'London Film Festival 2025', value: 'ls4155557236' },
      { label: 'Sundance 2025', value: 'ls595865777' },
    ]
  },
]

const tmdbPresets = [
  {
    category: 'Top Lists',
    items: [
      { label: 'Top 250 IMDB', value: 'https://www.themoviedb.org/list/634' },
      { label: 'IMDB 50 Most Popular', value: 'https://www.themoviedb.org/list/6709' },
      { label: 'Top 10 Movies', value: 'https://www.themoviedb.org/list/8285446' },
    ]
  },
  {
    category: 'Box Office',
    items: [
      { label: 'All Time Box Office', value: 'https://www.themoviedb.org/list/9024' },
    ]
  },
]

const letterboxdPresets = [
  {
    category: 'Top Lists',
    items: [
      { label: 'Top 250 Narrative Films', value: 'https://letterboxd.com/dave/list/official-top-250-narrative-feature-films/' },
      { label: 'Top 250 Most Fans', value: 'https://letterboxd.com/jack/list/official-top-250-films-with-the-most-fans/' },
      { label: '1001 Must See Movies', value: 'https://letterboxd.com/peterstanley/list/1001-movies-you-must-see-before-you-die/' },
    ]
  },
  {
    category: 'Curated',
    items: [
      { label: 'Movies to Watch Once', value: 'https://letterboxd.com/fcbarcelona/list/movies-everyone-should-watch-at-least-once/' },
      { label: 'Feel Something', value: 'https://letterboxd.com/ellefnning/list/for-when-you-want-to-feel-something/' },
    ]
  },
]

const mdblistPresets = [
  {
    category: 'Streaming - Movies',
    items: [
      { label: 'Netflix Movies', value: 'https://mdblist.com/lists/garycrawfordgc/netflix-movies' },
      { label: 'Amazon Prime Movies', value: 'https://mdblist.com/lists/garycrawfordgc/amazon-prime-movies' },
      { label: 'Disney+ Movies', value: 'https://mdblist.com/lists/garycrawfordgc/disney-movies' },
    ]
  },
  {
    category: 'Streaming - Shows',
    items: [
      { label: 'Netflix Shows', value: 'https://mdblist.com/lists/garycrawfordgc/netflix-shows' },
      { label: 'HBO Shows', value: 'https://mdblist.com/lists/garycrawfordgc/hbo-shows' },
    ]
  },
  {
    category: 'Popular',
    items: [
      { label: 'Top Watched This Week', value: 'https://mdblist.com/lists/linaspurinis/top-watched-movies-of-the-week' },
    ]
  },
]

const stevenluPresets = [
  {
    category: 'All Movies',
    items: [
      { label: 'All Movies (Unfiltered)', value: 'all-movies.json' },
      { label: 'Original Collection', value: 'stevenlu' },
    ],
  },
  {
    category: 'Metacritic (Min Score)',
    items: [
      { label: 'Metacritic Min 50', value: 'movies-metacritic-min50.json' },
      { label: 'Metacritic Min 60', value: 'movies-metacritic-min60.json' },
      { label: 'Metacritic Min 70', value: 'movies-metacritic-min70.json' },
      { label: 'Metacritic Min 80', value: 'movies-metacritic-min80.json' },
    ],
  },
  {
    category: 'IMDb (Min Score)',
    items: [
      { label: 'IMDb Min 5.0', value: 'movies-imdb-min5.json' },
      { label: 'IMDb Min 6.0', value: 'movies-imdb-min6.json' },
      { label: 'IMDb Min 7.0', value: 'movies-imdb-min7.json' },
      { label: 'IMDb Min 8.0', value: 'movies-imdb-min8.json' },
    ],
  },
  {
    category: 'Rotten Tomatoes (Min Score)',
    items: [
      { label: 'RT Min 50', value: 'movies-rottentomatoes-min50.json' },
      { label: 'RT Min 60', value: 'movies-rottentomatoes-min60.json' },
      { label: 'RT Min 70', value: 'movies-rottentomatoes-min70.json' },
      { label: 'RT Min 80', value: 'movies-rottentomatoes-min80.json' },
    ],
  },
]

const traktPresets = [
  {
    category: 'Streaming - Movies',
    items: [
      { label: 'Netflix Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/netflix-movies' },
      { label: 'Amazon Prime Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/amazon-prime-movies' },
      { label: 'Disney+ Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/disney-movies' },
      { label: 'Hulu Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/hulu-movies' },
    ]
  },
  {
    category: 'Streaming - Shows',
    items: [
      { label: 'Netflix Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/netflix-shows' },
      { label: 'Amazon Prime Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/amazon-prime-shows' },
      { label: 'Disney+ Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/disney-shows' },
      { label: 'Hulu Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/hulu-shows' },
      { label: 'HBO Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/hbo-shows' },
      { label: 'BBC Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/bbc-shows' },
    ]
  },
  {
    category: 'Genre - Movies',
    items: [
      { label: 'Action', value: 'https://trakt.tv/users/garycrawfordgc/lists/action' },
      { label: 'Comedy', value: 'https://trakt.tv/users/garycrawfordgc/lists/comedy' },
      { label: 'Crime', value: 'https://trakt.tv/users/garycrawfordgc/lists/crime' },
      { label: 'Drama', value: 'https://trakt.tv/users/garycrawfordgc/lists/drama' },
      { label: 'Horror', value: 'https://trakt.tv/users/garycrawfordgc/lists/horror' },
      { label: 'Sci-Fi', value: 'https://trakt.tv/users/garycrawfordgc/lists/sci-fi' },
      { label: 'Thriller', value: 'https://trakt.tv/users/garycrawfordgc/lists/thriller' },
      { label: 'History', value: 'https://trakt.tv/users/garycrawfordgc/lists/history' },
      { label: 'War', value: 'https://trakt.tv/users/garycrawfordgc/lists/war' },
      { label: "80's Movies", value: 'https://trakt.tv/users/garycrawfordgc/lists/80-s-movies' },
    ]
  },
  {
    category: 'Genre - Shows',
    items: [
      { label: 'Comedy Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/comedy-shows' },
      { label: 'Crime Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/crime-shows' },
      { label: 'Drama Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/drama-shows' },
      { label: 'Horror Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/horror-shows' },
      { label: 'Sci-Fi Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/sci-fi-shows' },
    ]
  },
  {
    category: 'Popular & Latest',
    items: [
      { label: 'Top Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/top-movies' },
      { label: 'Top Movies of the Week', value: 'https://trakt.tv/users/garycrawfordgc/lists/top-movies-of-the-week' },
      { label: 'Latest Releases', value: 'https://trakt.tv/users/garycrawfordgc/lists/latest-releases' },
      { label: 'Latest Blu-ray Releases', value: 'https://trakt.tv/users/garycrawfordgc/lists/latest-blu-ray-releases' },
      { label: 'Latest TV Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/latest-tv-shows' },
    ]
  },
  {
    category: 'Recommendations',
    items: [
      { label: 'Gary Recommends', value: 'https://trakt.tv/users/garycrawfordgc/lists/gary-recommends' },
      { label: 'Recommended Movies', value: 'https://trakt.tv/users/garycrawfordgc/lists/recommended-movies' },
      { label: 'Movies from the Last Decade', value: 'https://trakt.tv/users/garycrawfordgc/lists/movies-from-the-last-decade-couchmoney-tv' },
      { label: 'TV Recommendations', value: 'https://trakt.tv/users/garycrawfordgc/lists/tv-recommendations-couchmoney-tv' },
    ]
  },
  {
    category: 'Regional',
    items: [
      { label: 'UK Shows', value: 'https://trakt.tv/users/garycrawfordgc/lists/uk-shows' },
      { label: 'Video Nasties', value: 'https://trakt.tv/users/garycrawfordgc/lists/video-nasties' },
    ]
  },
  {
    category: 'Other',
    items: [
      { label: 'Collaborations', value: 'https://trakt.tv/users/garycrawfordgc/lists/collaborations' },
    ]
  },
]

// Computed properties
const isTraktSpecial = computed(() => selectedSource.value === 'trakt_special')
const isLetterboxd = computed(() => selectedSource.value === 'letterboxd')
const isMDBList = computed(() => selectedSource.value === 'mdblist')
const isTmdb = computed(() => selectedSource.value === 'tmdb')
const isUrlRequired = computed(() => ['tmdb', 'tvdb', 'anilist'].includes(selectedSource.value))

const canProceed = computed(() => {
  if (isTraktSpecial.value) {
    return selectedTraktType.value !== '' && selectedTraktMedia.value !== ''
  }
  return listId.value.trim() !== '' && !error.value
})

const allSelectedLists = computed(() => {
  const lists = [...listsToAdd.value]
  
  // Add current configuration if valid AND we're still on step 2 (not yet added)
  // Don't add if we're on step 3 (already added to listsToAdd)
  if (currentStep.value === 2 && canProceed.value && selectedSource.value) {
    // Check if this exact list is already in the batch to prevent duplicates
    const currentListId = getFinalListId()
    const currentListType = getFinalListType()
    const alreadyExists = lists.some(l => l.listId === currentListId && (l.listType === currentListType || l.source === currentListType))
    
    if (!alreadyExists) {
      const currentList = {
        id: `current-${Date.now()}`,
        source: selectedSource.value,
        listId: currentListId,
        displayName: getDisplayName(),
        listType: currentListType,
        mediaType: isTraktSpecial.value ? selectedTraktMedia.value : undefined,
        isCurrent: true
      }
      lists.push(currentList)
    }
  }
  
  return lists
})

// Get filtered presets based on selected source
const currentFilteredPresets = computed(() => {
  const search = presetSearch.value.toLowerCase().trim()
  let presets: Array<{ category: string; items: Array<{ label: string; value: string }> }> = []
  
  switch (selectedSource.value) {
    case 'imdb': presets = imdbPresets; break
    case 'trakt': presets = traktPresets; break
    case 'tmdb': presets = tmdbPresets; break
    case 'letterboxd': presets = letterboxdPresets; break
    case 'mdblist': presets = mdblistPresets; break
    case 'stevenlu': presets = stevenluPresets; break
    default: presets = []
  }
  
  if (!search) return presets
  
  return presets
    .map(category => ({
      ...category,
      items: category.items.filter(item => 
        item.label.toLowerCase().includes(search) ||
        category.category.toLowerCase().includes(search)
      )
    }))
    .filter(category => category.items.length > 0)
})

// Get filtered Trakt Special presets
const filteredTraktSpecialPresets = computed(() => {
  const search = presetSearch.value.toLowerCase().trim()
  
  if (!search) return traktSpecialPresets
  
  return traktSpecialPresets
    .map(category => ({
      ...category,
      items: category.items.filter(item => 
        item.label.toLowerCase().includes(search) ||
        category.category.toLowerCase().includes(search)
      )
    }))
    .filter(category => category.items.length > 0)
})

// Helper functions
const hasPresets = (provider: string) => {
  return ['imdb', 'trakt', 'trakt_special', 'letterboxd', 'mdblist', 'stevenlu', 'tmdb'].includes(provider)
}

const getPresetCount = (provider: string) => {
  switch (provider) {
    case 'imdb': return imdbPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    case 'trakt': return traktPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    case 'trakt_special': return traktSpecialTypes.length * traktMediaTypes.length
    case 'letterboxd': return letterboxdPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    case 'mdblist': return mdblistPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    case 'stevenlu': return stevenluPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    case 'tmdb': return tmdbPresets.reduce((sum, cat) => sum + cat.items.length, 0)
    default: return 0
  }
}

const toggleCategory = (categoryKey: string) => {
  collapsedCategories.value[categoryKey] = !isCategoryCollapsed(categoryKey)
}

const isCategoryCollapsed = (categoryKey: string) => {
  if (collapsedCategories.value[categoryKey] === undefined) {
    const [provider] = categoryKey.split('-')
    const categoryName = categoryKey.substring(provider.length + 1)
    
    let firstCategory = ''
    switch (provider) {
      case 'imdb': firstCategory = imdbPresets[0]?.category || ''; break
      case 'trakt': firstCategory = traktPresets[0]?.category || ''; break
      case 'letterboxd': firstCategory = letterboxdPresets[0]?.category || ''; break
      case 'mdblist': firstCategory = mdblistPresets[0]?.category || ''; break
      case 'stevenlu': firstCategory = stevenluPresets[0]?.category || ''; break
      case 'tmdb': firstCategory = tmdbPresets[0]?.category || ''; break
      case 'trakt_special': firstCategory = traktSpecialPresets[0]?.category || ''; break
    }
    
    return categoryName !== firstCategory
  }
  return collapsedCategories.value[categoryKey] === true
}

const getProviderColor = (provider: string) => {
  const colors: Record<string, { border: string; bg: string; text: string }> = {
    imdb: { border: 'border-yellow-500', bg: 'bg-yellow-500/20', text: 'text-yellow-300' },
    trakt: { border: 'border-green-500', bg: 'bg-green-500/20', text: 'text-green-300' },
    letterboxd: { border: 'border-pink-500', bg: 'bg-pink-500/20', text: 'text-pink-300' },
    mdblist: { border: 'border-purple-500', bg: 'bg-purple-500/20', text: 'text-purple-300' },
    stevenlu: { border: 'border-red-500', bg: 'bg-red-500/20', text: 'text-red-300' },
    trakt_special: { border: 'border-purple-500', bg: 'bg-purple-500/20', text: 'text-purple-300' },
    tmdb: { border: 'border-cyan-500', bg: 'bg-cyan-500/20', text: 'text-cyan-300' },
  }
  return colors[provider] || { border: 'border-purple-500', bg: 'bg-purple-500/20', text: 'text-purple-300' }
}

const getSourceIcon = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.icon || DatabaseIcon
}

const getSourceColor = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return {
    color: sourceData?.color || 'text-gray-400',
    bgColor: sourceData?.bgColor || 'bg-gray-500/20',
    borderColor: sourceData?.borderColor || 'border-gray-500/40'
  }
}

const formatListSource = (source: string) => {
  const sourceData = sources.find(s => s.value === source)
  return sourceData?.label || source
}

const getPlaceholder = (source: string) => {
  const placeholders: Record<string, string> = {
    imdb: "'top', 'ls026785255', or 'ur12345678'",
    trakt: 'https://trakt.tv/users/{user}/watchlist',
    letterboxd: 'https://letterboxd.com/{user}/list/{name}/',
    mdblist: 'https://mdblist.com/lists/{user}/{name}',
    stevenlu: "'stevenlu' or JSON filename",
    tmdb: 'https://www.themoviedb.org/list/{id}',
    tvdb: 'https://www.thetvdb.com/lists/{name}',
    anilist: 'https://anilist.co/user/{username}/animelist',
  }
  return placeholders[source] || 'Enter list ID or URL'
}

const getHelperText = (source: string) => {
  const helpers: Record<string, string> = {
    imdb: 'Enter a chart name (top, boxoffice), list ID (ls...), or user ID (ur...) for watchlists',
    trakt: 'Enter the full Trakt URL for a watchlist or custom list',
    letterboxd: 'Enter the full Letterboxd list URL',
    mdblist: 'Enter the full MDBList URL',
    stevenlu: 'Enter "stevenlu" or a JSON filename like "movies-imdb-min8.json"',
    tmdb: 'Enter the full TMDB list URL',
    tvdb: 'Enter the full TVDB list URL',
    anilist: 'Enter the AniList URL or just the username',
  }
  return helpers[source] || 'Enter the list identifier'
}

// Get preview URL for a preset
const getPresetUrl = (provider: string, value: string): string | null => {
  if (provider === 'imdb') {
    const imdbUrls: Record<string, string> = {
      'top': 'https://www.imdb.com/chart/top/',
      'boxoffice': 'https://www.imdb.com/chart/boxoffice/',
      'moviemeter': 'https://www.imdb.com/chart/moviemeter/',
      'tvmeter': 'https://www.imdb.com/chart/tvmeter/',
    }
    if (imdbUrls[value]) return imdbUrls[value]
    if (value.startsWith('ls')) return `https://www.imdb.com/list/${value}/`
    return null
  } else if (provider === 'trakt' || provider === 'letterboxd' || provider === 'mdblist' || provider === 'tmdb') {
    return value.startsWith('http') ? value : null
  } else if (provider === 'stevenlu') {
    if (value === 'stevenlu') return 'https://movies.stevenlu.com/'
    if (value.endsWith('.json')) return `https://movies.stevenlu.com/${value}`
    return null
  }
  return null
}

// Open preset URL in new tab
const openPresetUrl = (event: Event, provider: string, value: string) => {
  event.stopPropagation()
  const url = getPresetUrl(provider, value)
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

const getFinalListId = () => {
  if (isTraktSpecial.value) {
    return `${selectedTraktType.value}:${selectedTraktMedia.value}`
  }
  return listId.value.trim()
}

const getFinalListType = () => {
  if (isTraktSpecial.value) return 'trakt_special'
  return selectedSource.value
}

const getDisplayName = () => {
  if (isTraktSpecial.value) {
    const type = selectedTraktType.value.charAt(0).toUpperCase() + selectedTraktType.value.slice(1)
    const media = selectedTraktMedia.value === 'movies' ? 'Movies' : 'TV Shows'
    return `${type} ${media}`
  }
  
  // Check presets (including traktPresets)
  const allPresets = [...imdbPresets, ...traktPresets, ...tmdbPresets, ...letterboxdPresets, ...mdblistPresets, ...stevenluPresets]
  for (const category of allPresets) {
    const preset = category.items.find(p => p.value === listId.value)
    if (preset) return preset.label
  }
  
  return listId.value
}

const getSubmitButtonText = () => {
  const count = listsToAdd.value.length
  const syncText = selectedSyncOption.value === 'single' ? 'Sync' : selectedSyncOption.value === 'all' ? 'Sync All' : 'Schedule'
  return `Add ${count} List${count !== 1 ? 's' : ''} & ${syncText}`
}

// Handlers
const handleCollectionsRedirect = () => {
  handleClose()
  setTimeout(() => router.push('/collections'), 150)
}

const selectSource = (source: string) => {
  selectedSource.value = source
  presetSearch.value = ''
  collapsedCategories.value = {}
  listId.value = ''
  selectedTraktType.value = ''
  selectedTraktMedia.value = ''
  error.value = ''
  currentStep.value = 2
}

const handleTraktMediaSelect = (media: string) => {
  selectedTraktMedia.value = media
}

// Handle Trakt Special preset selection (selects both type and media at once)
const handleTraktSpecialPresetSelect = (type: string, media: string) => {
  selectedTraktType.value = type
  selectedTraktMedia.value = media
  error.value = ''
}

// Open Trakt Special URL in new tab
const openTraktSpecialUrl = (type: string, media: string) => {
  const mediaPath = media === 'movies' ? 'movies' : 'shows'
  const url = `https://trakt.tv/${mediaPath}/${type}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

const handlePresetSelect = (presetValue: string, _presetLabel: string) => {
  listId.value = presetValue
  error.value = ''
}

const handleAddList = () => {
  if (!validateInput()) return
  
  const finalListId = getFinalListId()
  const finalListType = getFinalListType()
  
  // Check if already exists to prevent duplicates
  const alreadyExists = listsToAdd.value.some(
    l => l.listId === finalListId && (l.listType === finalListType || l.source === finalListType)
  )
  
  if (!alreadyExists) {
    // Add current list to batch
    const newList = {
      id: `${finalListType}-${finalListId}-${Date.now()}`,
      source: selectedSource.value,
      listId: finalListId,
      displayName: getDisplayName(),
      listType: finalListType,
      mediaType: isTraktSpecial.value ? selectedTraktMedia.value : undefined
    }
    
    listsToAdd.value.push(newList)
  }
  
  // Clear current selection state to prevent showing as "current" in sidebar
  listId.value = ''
  selectedTraktType.value = ''
  selectedTraktMedia.value = ''
  
  // Go to confirm step
  currentStep.value = 3
}

const addAnotherList = () => {
  // Reset for new list selection
  selectedSource.value = ''
  listId.value = ''
  selectedTraktType.value = ''
  selectedTraktMedia.value = ''
  error.value = ''
  presetSearch.value = ''
  currentStep.value = 1
}

const removeListFromBatch = (index: number) => {
  // Filter out current list marker
  const actualLists = listsToAdd.value
  if (index < actualLists.length) {
    actualLists.splice(index, 1)
  }
}

const validateInput = () => {
  error.value = ''
  
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

  // Source-specific validation
  if (selectedSource.value === 'imdb') {
    const validCharts = ['top', 'boxoffice', 'moviemeter', 'tvmeter']
    const isValid = validCharts.includes(value.toLowerCase()) || 
                    value.match(/^ls\d+$/) || 
                    value.match(/^ur\d+$/) || 
                    value.includes('imdb.com')
    if (!isValid) {
      error.value = 'Enter "top", a list ID (ls...), or user ID (ur...)'
      return false
    }
  } else if (selectedSource.value === 'trakt') {
    if (!value.includes('trakt.tv/users/') || (!value.includes('/lists/') && !value.includes('/watchlist'))) {
      error.value = 'Enter a valid Trakt URL'
      return false
    }
  } else if (selectedSource.value === 'letterboxd') {
    if (!value.startsWith('https://letterboxd.com/') || (!value.includes('/list/') && !value.includes('/watchlist'))) {
      error.value = 'Enter a valid Letterboxd URL'
      return false
    }
  } else if (selectedSource.value === 'mdblist') {
    if (!value.startsWith('https://mdblist.com/lists/')) {
      error.value = 'Enter a valid MDBList URL'
      return false
    }
  } else if (selectedSource.value === 'tmdb') {
    if (!value.startsWith('https://www.themoviedb.org/list/')) {
      error.value = 'Enter a valid TMDB URL'
      return false
    }
  } else if (selectedSource.value === 'tvdb') {
    if (!value.startsWith('https://www.thetvdb.com/lists/')) {
      error.value = 'Enter a valid TVDB URL'
      return false
    }
  } else if (selectedSource.value === 'stevenlu') {
    const isValid = value === 'stevenlu' || 
                    (value.endsWith('.json') && value.startsWith('movies-')) ||
                    value.includes('stevenlu.com')
    if (!isValid) {
      error.value = 'Enter "stevenlu" or a valid JSON filename'
      return false
    }
  } else if (selectedSource.value === 'anilist') {
    const isValid = (value.startsWith('https://anilist.co/user/') && value.includes('/animelist')) ||
                    /^[a-zA-Z0-9_-]+$/.test(value)
    if (!isValid) {
      error.value = 'Enter a valid AniList URL or username'
      return false
    }
  }

  return true
}

const handleSubmitAll = async () => {
  // Collect all lists from the batch
  const allLists = [...listsToAdd.value]
  
  // If we're still on step 2 with a valid selection that hasn't been added yet, add it
  if (currentStep.value === 2 && canProceed.value && selectedSource.value) {
    const finalListId = getFinalListId()
    const finalListType = getFinalListType()
    const alreadyExists = allLists.some(
      l => l.listId === finalListId && (l.listType === finalListType || l.source === finalListType)
    )
    
    if (!alreadyExists) {
      allLists.push({
        id: `${finalListType}-${finalListId}-${Date.now()}`,
        source: selectedSource.value,
        listId: finalListId,
        displayName: getDisplayName(),
        listType: finalListType,
        mediaType: isTraktSpecial.value ? selectedTraktMedia.value : undefined
      })
    }
  }
  
  if (allLists.length === 0) {
    showError('No Lists', 'Please add at least one list')
    return
  }

  loading.value = true
  error.value = ''

  try {
    const listsStore = useListsStore()
    const syncStore = useSyncStore()
    
    // Add all lists
    for (const list of allLists) {
      await listsStore.addList({
        list_type: list.listType || list.source,
        list_id: list.listId,
        user_id: String(selectedUserId.value),
      })
    }

    showSuccess('Lists Added', `Successfully added ${allLists.length} list${allLists.length !== 1 ? 's' : ''}`)
    
    await listsStore.fetchLists(true)
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Handle sync option
    if (selectedSyncOption.value === 'single') {
      if (allLists.length > 1) {
        showSuccess('Syncing Lists', `Starting sync for ${allLists.length} lists...`)
        await syncStore.triggerSync()
      } else {
        showSuccess('Syncing List', 'Starting sync...')
        await api.syncSingleList(allLists[0].listType || allLists[0].source, allLists[0].listId)
      }
    } else if (selectedSyncOption.value === 'all') {
      showSuccess('Syncing All', 'Starting sync for all lists...')
      await syncStore.triggerSync()
    } else {
      showSuccess('Scheduled', `${allLists.length} list${allLists.length !== 1 ? 's' : ''} will sync on next schedule`)
    }

    emit('list-added')
    handleClose()
    
    if (process.client && selectedSyncOption.value !== 'schedule') {
      setTimeout(() => router.push('/logs'), 150)
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to add lists'
    showError('Failed to add lists', err.message)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  isOpen.value = false
  setTimeout(() => {
    currentStep.value = 1
    selectedSource.value = ''
    listId.value = ''
    selectedTraktType.value = ''
    selectedTraktMedia.value = ''
    selectedSyncOption.value = 'single'
    error.value = ''
    listsToAdd.value = []
    presetSearch.value = ''
    showMobileSidebar.value = false
  }, 300)
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

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}

.slide-up-enter-from > div:last-child,
.slide-up-leave-to > div:last-child {
  transform: translateY(100%);
}
</style>

