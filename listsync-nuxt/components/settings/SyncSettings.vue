<template>
  <Card class="glass-card">
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center gap-3">
        <div class="p-3 rounded-lg bg-accent/10">
          <RefreshIcon class="w-5 h-5 text-accent" />
        </div>
        <div>
          <h3 class="text-lg font-semibold titillium-web-semibold">
            Sync Settings
          </h3>
          <p class="text-sm text-muted-foreground">
            Configure synchronization behavior
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Sync Interval -->
        <div>
          <label class="block text-sm font-medium mb-2">
            Sync Interval (hours)
            <span class="text-danger">*</span>
          </label>
          <Input
            v-model.number="localValue.interval"
            type="number"
            :min="1"
            :max="168"
            placeholder="24"
            :icon="ClockIcon"
            @update:model-value="emitUpdate"
          />
          <div class="mt-2 flex items-start gap-2 p-2 rounded-lg bg-info/10 border border-info/20">
            <InfoIcon class="w-4 h-4 text-info flex-shrink-0 mt-0.5" />
            <p class="text-xs text-info">
              This value is stored in the database and syncs with the /sync page. Changes take effect immediately.
            </p>
          </div>
        </div>

        <!-- Timezone -->
        <div>
          <label class="block text-sm font-medium mb-2">
            Timezone
          </label>
          <div class="relative">
            <input
              v-model="timezoneSearch"
              type="text"
              placeholder="Search timezones..."
              class="w-full px-4 py-2 bg-black/30 border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              @focus="showTimezoneDropdown = true"
              @blur="hideTimezoneDropdown"
            />
            
            <!-- Timezone Dropdown -->
            <div
              v-if="showTimezoneDropdown && filteredTimezones.length > 0"
              class="absolute z-50 w-full mt-2 max-h-64 overflow-y-auto bg-black/95 border border-border rounded-lg shadow-xl backdrop-blur-sm"
            >
              <button
                v-for="tz in filteredTimezones.slice(0, 50)"
                :key="tz.value"
                type="button"
                class="w-full text-left px-4 py-2 hover:bg-purple-500/20 transition-colors text-sm"
                @mousedown.prevent="selectTimezone(tz.value)"
              >
                <div class="font-medium">{{ tz.label }}</div>
                <div class="text-xs text-muted-foreground">{{ tz.offset }}</div>
              </button>
            </div>
          </div>
          
          <!-- Current Timezone Display -->
          <div class="mt-2 flex items-center gap-2">
            <Badge v-if="localValue.timezone" variant="primary" size="sm">
              <ClockIcon :size="12" class="mr-1" />
              {{ localValue.timezone }}
            </Badge>
            <span v-if="currentTimezoneInfo" class="text-xs text-muted-foreground">
              {{ currentTimezoneInfo.offset }}
            </span>
          </div>
          
          <p class="text-xs text-muted-foreground mt-1">
            Timezone for scheduling syncs (supports IANA names, UTC offsets, and abbreviations)
          </p>
        </div>

        <!-- Automated Mode -->
        <div class="md:col-span-2">
          <label class="block text-sm font-medium mb-2">
            Automated Sync
          </label>
          <div class="flex items-center gap-3">
            <!-- Status Label -->
            <span 
              :class="[
                'text-sm font-semibold tabular-nums min-w-[32px]',
                localValue.automatedMode ? 'text-green-400' : 'text-gray-400'
              ]"
            >
              {{ localValue.automatedMode ? 'ON' : 'OFF' }}
            </span>
            
            <!-- Toggle Switch -->
            <button
              type="button"
              role="switch"
              :aria-checked="localValue.automatedMode"
              :class="[
                'relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-black',
                localValue.automatedMode ? 'bg-green-500' : 'bg-gray-600'
              ]"
              @click="toggleAutomatedMode"
            >
              <span
                :class="[
                  'inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white shadow-lg transition-all duration-200',
                  localValue.automatedMode ? 'translate-x-7' : 'translate-x-0.5'
                ]"
              >
                <!-- Icon inside toggle -->
                <CheckIcon v-if="localValue.automatedMode" :size="14" class="text-green-500" />
                <XIcon v-else :size="14" class="text-gray-600" />
              </span>
            </button>
            
            <span class="text-sm text-muted-foreground">
              {{ localValue.automatedMode ? 'Sync runs automatically' : 'Manual sync only' }}
            </span>
          </div>
          <p class="text-xs text-muted-foreground mt-3">
            When enabled, sync will run automatically at the specified interval
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">Sync Behavior</p>
            <ul class="text-muted-foreground space-y-1 list-disc list-inside">
              <li>Syncs run in the background without blocking the UI</li>
              <li>Manual syncs can be triggered at any time</li>
              <li>Failed items can be retried individually</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  Clock as ClockIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  X as XIcon,
} from 'lucide-vue-next'

interface SyncSettings {
  interval: number
  automatedMode: boolean
  timezone: string
}

interface Props {
  modelValue: SyncSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: SyncSettings]
}>()

const api = useApiService()

const localValue = ref({ ...props.modelValue })

// Timezone state
const timezoneSearch = ref('')
const showTimezoneDropdown = ref(false)
const supportedTimezones = ref<any[]>([])
const currentTimezoneInfo = ref<any>(null)

// Fallback timezones if API fails
const fallbackTimezones = [
  { label: 'UTC', value: 'UTC', offset: '+00:00' },
  { label: 'America/New_York (EST/EDT)', value: 'America/New_York', offset: 'UTC-05:00' },
  { label: 'America/Chicago (CST/CDT)', value: 'America/Chicago', offset: 'UTC-06:00' },
  { label: 'America/Denver (MST/MDT)', value: 'America/Denver', offset: 'UTC-07:00' },
  { label: 'America/Los_Angeles (PST/PDT)', value: 'America/Los_Angeles', offset: 'UTC-08:00' },
  { label: 'Europe/London (GMT/BST)', value: 'Europe/London', offset: 'UTC+00:00' },
  { label: 'Europe/Paris (CET/CEST)', value: 'Europe/Paris', offset: 'UTC+01:00' },
  { label: 'Asia/Tokyo (JST)', value: 'Asia/Tokyo', offset: 'UTC+09:00' },
  { label: 'Australia/Sydney (AEDT)', value: 'Australia/Sydney', offset: 'UTC+11:00' },
]

// Load supported timezones
const loadTimezones = async () => {
  try {
    const response: any = await api.getSupportedTimezones()
    supportedTimezones.value = response.timezones || fallbackTimezones
  } catch (error) {
    console.error('Error loading timezones, using fallback:', error)
    supportedTimezones.value = fallbackTimezones
  }
}

// Load current timezone info
const loadCurrentTimezoneInfo = async () => {
  try {
    currentTimezoneInfo.value = await api.getCurrentTimezone()
  } catch (error) {
    console.error('Error loading current timezone:', error)
  }
}

// Filtered timezones based on search
const filteredTimezones = computed(() => {
  if (!timezoneSearch.value) {
    return supportedTimezones.value
  }
  
  const search = timezoneSearch.value.toLowerCase()
  return supportedTimezones.value.filter((tz: any) =>
    tz.label?.toLowerCase().includes(search) ||
    tz.value?.toLowerCase().includes(search) ||
    tz.offset?.toLowerCase().includes(search)
  )
})

// Select timezone
const selectTimezone = (timezone: string) => {
  localValue.value.timezone = timezone
  timezoneSearch.value = timezone
  showTimezoneDropdown.value = false
  emitUpdate()
  loadCurrentTimezoneInfo()
}

// Hide dropdown with delay
const hideTimezoneDropdown = () => {
  setTimeout(() => {
    showTimezoneDropdown.value = false
  }, 200)
}

// Initialize
onMounted(() => {
  loadTimezones()
  loadCurrentTimezoneInfo()
  timezoneSearch.value = localValue.value.timezone || ''
})

// Timezone options (common timezones)
const timezoneOptions = [
  { label: 'UTC', value: 'UTC' },
  { label: 'America/New_York (EST/EDT)', value: 'America/New_York' },
  { label: 'America/Chicago (CST/CDT)', value: 'America/Chicago' },
  { label: 'America/Denver (MST/MDT)', value: 'America/Denver' },
  { label: 'America/Los_Angeles (PST/PDT)', value: 'America/Los_Angeles' },
  { label: 'Europe/London (GMT/BST)', value: 'Europe/London' },
  { label: 'Europe/Paris (CET/CEST)', value: 'Europe/Paris' },
  { label: 'Asia/Tokyo (JST)', value: 'Asia/Tokyo' },
  { label: 'Australia/Sydney (AEDT/AEST)', value: 'Australia/Sydney' },
]

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

// Toggle automated mode
const toggleAutomatedMode = () => {
  localValue.value.automatedMode = !localValue.value.automatedMode
  emitUpdate()
}
</script>

