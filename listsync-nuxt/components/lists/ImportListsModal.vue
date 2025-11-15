<template>
  <Modal v-model="isOpen" size="2xl" @close="handleClose">
    <template #header>
      <div class="flex items-center gap-3">
        <component :is="UploadIcon" :size="24" class="text-purple-400" />
        <div>
          <h2 class="text-2xl font-bold text-foreground titillium-web-bold">
            Import Lists
          </h2>
          <p class="text-sm text-muted-foreground mt-1">
            Import lists from an exported text file
          </p>
        </div>
      </div>
    </template>

    <!-- Step 1: File Upload -->
    <div v-if="currentStep === 1" class="space-y-6">
      <div class="border-2 border-dashed border-purple-500/30 rounded-lg p-8 text-center hover:border-purple-500/50 transition-colors">
        <input
          ref="fileInput"
          type="file"
          accept=".txt"
          class="hidden"
          @change="handleFileSelect"
        />
        <div class="flex flex-col items-center gap-4">
          <div class="p-4 rounded-full bg-purple-500/20">
            <component :is="UploadIcon" :size="32" class="text-purple-400" />
          </div>
          <div>
            <p class="text-sm font-medium text-foreground mb-1">
              Select export file
            </p>
            <p class="text-xs text-muted-foreground">
              Choose a .txt file exported from ListSync
            </p>
          </div>
          <Button
            variant="secondary"
            :icon="UploadIcon"
            @click="fileInput?.click()"
          >
            Choose File
          </Button>
        </div>
      </div>

      <div v-if="error" class="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <p class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>

    <!-- Step 2: Review and Sync Options -->
    <div v-if="currentStep === 2" class="space-y-6">
      <!-- Lists Preview -->
      <div>
        <h3 class="text-lg font-semibold text-foreground mb-3">
          Lists to Import ({{ parsedLists.length }})
        </h3>
        <div class="max-h-96 overflow-y-auto space-y-2 custom-scrollbar">
          <Card
            v-for="(list, index) in parsedLists"
            :key="index"
            variant="flat"
            class="p-3 hover:border-purple-500/30 transition-all"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <Badge variant="info" size="sm">{{ list.list_type }}</Badge>
                  <span class="font-medium text-foreground truncate">
                    {{ list.display_name || list.list_id }}
                  </span>
                </div>
                <p class="text-xs text-muted-foreground truncate">
                  ID: {{ list.list_id }}
                </p>
                <p v-if="list.url" class="text-xs text-purple-400 truncate mt-1">
                  {{ list.url }}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <!-- Sync Options -->
      <div class="space-y-3">
        <h3 class="text-lg font-semibold text-foreground mb-2">
          Sync Options
        </h3>
        
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
                Immediately sync all imported lists
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
                Sync all lists in your system (including existing ones)
              </p>
            </div>
          </div>
        </button>
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
            v-if="currentStep === 2"
            variant="secondary"
            :disabled="loading"
            @click="currentStep = 1"
          >
            Back
          </Button>

          <Button
            v-if="currentStep === 2"
            variant="primary"
            :disabled="parsedLists.length === 0 || loading"
            :loading="loading"
            @click="handleImport"
          >
            Import {{ parsedLists.length }} List{{ parsedLists.length !== 1 ? 's' : '' }} & {{ getSyncButtonText() }}
          </Button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  Upload as UploadIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'lists-imported': []
}>()

const { showSuccess, showError } = useToast()
const router = useRouter()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// State
const currentStep = ref(1)
const fileInput = ref<HTMLInputElement | null>(null)
const error = ref('')
const loading = ref(false)
const parsedLists = ref<Array<{
  list_type: string
  list_id: string
  display_name?: string
  url?: string
}>>([])
const selectedSyncOption = ref<'all' | 'single' | 'schedule'>('schedule')

// Parse the exported text file
const parseExportFile = (content: string): Array<{
  list_type: string
  list_id: string
  display_name?: string
  url?: string
}> => {
  const lists: Array<{
    list_type: string
    list_id: string
    display_name?: string
    url?: string
  }> = []

  const lines = content.split('\n')
  let currentType = ''
  let currentList: any = null

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()

    // Skip header and separator lines
    if (line.startsWith('=') || line.startsWith('-') || line === '' || 
        line.includes('ListSync') || line.includes('Exported') || line.includes('Total Lists')) {
      continue
    }

    // Detect list type section (e.g., "IMDB Lists (2)")
    const typeMatch = line.match(/^([A-Z_]+)\s+Lists\s+\((\d+)\)$/i)
    if (typeMatch) {
      currentType = typeMatch[1].toLowerCase()
      continue
    }

    // Detect list entry (e.g., "1. My Watchlist")
    const listMatch = line.match(/^\d+\.\s+(.+)$/)
    if (listMatch) {
      // Save previous list if exists
      if (currentList && currentList.list_type && currentList.list_id) {
        lists.push(currentList)
      }
      // Start new list
      currentList = {
        list_type: currentType,
        display_name: listMatch[1],
        list_id: '',
        url: undefined,
      }
      continue
    }

    // Parse list properties
    if (currentList) {
      if (line.startsWith('Type:')) {
        const type = line.replace('Type:', '').trim()
        if (type) {
          currentList.list_type = type.toLowerCase()
        }
      } else if (line.startsWith('ID:')) {
        currentList.list_id = line.replace('ID:', '').trim()
      } else if (line.startsWith('URL:')) {
        const url = line.replace('URL:', '').trim()
        if (url && url !== 'N/A') {
          currentList.url = url
        }
      }
    }
  }

  // Add last list
  if (currentList && currentList.list_type && currentList.list_id) {
    lists.push(currentList)
  }

  return lists
}

// Handle file selection
const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) {
    return
  }

  error.value = ''
  
  try {
    const content = await file.text()
    const parsed = parseExportFile(content)
    
    if (parsed.length === 0) {
      error.value = 'No valid lists found in the file. Please ensure it is a valid ListSync export file.'
      return
    }

    parsedLists.value = parsed
    currentStep.value = 2
  } catch (err: any) {
    console.error('Error parsing file:', err)
    error.value = 'Failed to read file. Please ensure it is a valid text file.'
  }
}

// Get sync button text
const getSyncButtonText = () => {
  const options = {
    schedule: 'Schedule',
    single: 'Sync These',
    all: 'Sync All'
  }
  return options[selectedSyncOption.value]
}

// Handle import
const handleImport = async () => {
  if (parsedLists.value.length === 0) {
    showError('No Lists', 'No lists to import')
    return
  }

  loading.value = true
  error.value = ''

  try {
    const listsStore = useListsStore()
    const syncStore = useSyncStore()
    const api = useApiService()

    // Add all lists
    let successCount = 0
    let failCount = 0
    const errors: string[] = []

    for (const list of parsedLists.value) {
      try {
        await listsStore.addList({
          list_type: list.list_type,
          list_id: list.list_id,
        })
        successCount++
      } catch (err: any) {
        failCount++
        const errorMsg = `${list.display_name || list.list_id}: ${err.message || 'Failed to add'}`
        errors.push(errorMsg)
        console.error(`Failed to add list ${list.list_type}:${list.list_id}:`, err)
      }
    }

    // Show results
    if (successCount > 0) {
      showSuccess('Lists Added', `Successfully imported ${successCount} of ${parsedLists.value.length} list(s)`)
    }
    if (failCount > 0) {
      showError('Some Lists Failed', `${failCount} list(s) failed to import: ${errors.slice(0, 3).join(', ')}${errors.length > 3 ? '...' : ''}`)
    }

    // Handle sync option
    if (selectedSyncOption.value === 'single' && successCount > 0) {
      // Sync just the imported lists
      showSuccess('Syncing Lists', `Starting sync for ${successCount} imported list(s)...`)
      
      let syncSuccessCount = 0
      let syncFailCount = 0
      
      for (const list of parsedLists.value) {
        try {
          await api.syncSingleList(list.list_type, list.list_id)
          syncSuccessCount++
        } catch (err: any) {
          syncFailCount++
          console.error(`Failed to sync ${list.list_type}:${list.list_id}:`, err)
        }
      }
      
      if (syncSuccessCount > 0) {
        showSuccess('Syncs Started', `Started ${syncSuccessCount} of ${successCount} list syncs`)
      }
      if (syncFailCount > 0) {
        showError('Some Syncs Failed', `${syncFailCount} list(s) failed to start sync`)
      }
      
      emit('lists-imported')
      handleClose()
      // Navigate to logs - use setTimeout to ensure modal closes first
      if (process.client) {
        setTimeout(() => {
          try {
            router.push('/logs')
          } catch (err) {
            console.error('Navigation error:', err)
            // Fallback to window.location if router fails
            window.location.href = '/logs'
          }
        }, 150)
      }
      return
    } else if (selectedSyncOption.value === 'all') {
      // Sync all lists
      showSuccess('Syncing All', 'Starting sync for all lists...')
      await syncStore.triggerSync()
      emit('lists-imported')
      handleClose()
      // Navigate to logs - use setTimeout to ensure modal closes first
      if (process.client) {
        setTimeout(() => {
          try {
            router.push('/logs')
          } catch (err) {
            console.error('Navigation error:', err)
            // Fallback to window.location if router fails
            window.location.href = '/logs'
          }
        }, 150)
      }
      return
    } else {
      // Just schedule for next sync
      showSuccess('Scheduled', `${successCount} list(s) will sync during the next scheduled interval`)
      emit('lists-imported')
      handleClose()
      // Navigate to logs - use setTimeout to ensure modal closes first
      if (process.client) {
        setTimeout(() => {
          try {
            router.push('/logs')
          } catch (err) {
            console.error('Navigation error:', err)
            // Fallback to window.location if router fails
            window.location.href = '/logs'
          }
        }, 150)
      }
      return
    }

    emit('lists-imported')
    handleClose()
  } catch (err: any) {
    error.value = err.message || 'Failed to import lists'
    showError('Import Failed', err.message || 'Failed to import lists')
  } finally {
    loading.value = false
  }
}

// Reset and close
const handleClose = () => {
  currentStep.value = 1
  parsedLists.value = []
  error.value = ''
  selectedSyncOption.value = 'schedule'
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  isOpen.value = false
}
</script>

