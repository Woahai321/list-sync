<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <TimerIcon class="w-4 h-4 text-purple-400" />
          <h3 class="text-base font-bold titillium-web-semibold">
            Sync Interval
          </h3>
        </div>

        <Badge :variant="intervalSource === 'env' ? 'warning' : 'default'" class="text-[10px]">
          {{ intervalSource === 'env' ? 'Environment' : 'Database' }}
        </Badge>
      </div>

      <!-- Current Interval Display -->
      <div class="bg-purple-600/10 border border-purple-500/20 rounded-lg p-3">
        <div class="text-[10px] text-muted-foreground mb-1 font-medium uppercase tracking-wide">
          Current Interval
        </div>
        <div class="text-2xl font-bold titillium-web-bold leading-none">
          {{ currentInterval }} <span class="text-base text-muted-foreground">hours</span>
        </div>
        <div class="text-[10px] text-muted-foreground mt-1.5 font-medium">
          Sync runs every {{ formatInterval(currentInterval) }}
        </div>
      </div>

      <!-- Update Form -->
      <div class="space-y-3">
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            New Interval (hours)
          </label>
          <Input
            v-model.number="newInterval"
            type="number"
            :min="1"
            :max="168"
            placeholder="Enter hours (1-168)"
            :error="validationError"
          />
          <p v-if="validationError" class="text-sm text-danger mt-1">
            {{ validationError }}
          </p>
          <p v-else class="text-sm text-muted-foreground mt-1">
            Min: 1 hour, Max: 168 hours (1 week)
          </p>
        </div>

        <!-- Quick Presets -->
        <div>
          <div class="text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            Quick Presets
          </div>
          <div class="grid grid-cols-3 gap-2">
            <Button
              v-for="preset in presets"
              :key="preset.hours"
              variant="ghost"
              size="sm"
              @click="applyPreset(preset.hours)"
            >
              {{ preset.label }}
            </Button>
          </div>
        </div>

        <!-- Warning for environment-sourced intervals -->
        <div
          v-if="intervalSource === 'env'"
          class="bg-warning/10 border border-warning/20 rounded-lg p-3 flex items-start gap-2"
        >
          <AlertTriangleIcon class="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <div class="text-sm">
            <p class="font-medium text-warning mb-1">Environment Override</p>
            <p class="text-muted-foreground">
              Interval is set via environment variable. Database updates will be ignored.
            </p>
          </div>
        </div>

        <!-- Update Button -->
        <Button
          variant="primary"
          class="w-full"
          :disabled="!isValid || isUpdating || intervalSource === 'env'"
          :loading="isUpdating"
          @click="handleUpdate"
        >
          <SaveIcon class="w-4 h-4 mr-2" />
          Update Interval
        </Button>
      </div>

      <!-- Info -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-3 flex items-start gap-2">
        <InfoIcon class="w-5 h-5 text-info flex-shrink-0 mt-0.5" />
        <div class="text-sm text-muted-foreground">
          <p>Changes take effect after the next sync completes.</p>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Timer as TimerIcon,
  AlertTriangle as AlertTriangleIcon,
  Info as InfoIcon,
  Save as SaveIcon,
} from 'lucide-vue-next'

interface Props {
  currentInterval: number
  intervalSource: 'env' | 'database'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update-interval': [interval: number]
}>()

// State
const newInterval = ref(props.currentInterval)
const isUpdating = ref(false)

// Presets
const presets = [
  { label: '1 hour', hours: 1 },
  { label: '3 hours', hours: 3 },
  { label: '6 hours', hours: 6 },
  { label: '12 hours', hours: 12 },
  { label: '24 hours', hours: 24 },
  { label: '48 hours', hours: 48 },
]

// Validation
const validationError = computed(() => {
  if (!newInterval.value) {
    return 'Interval is required'
  }
  if (newInterval.value < 1) {
    return 'Interval must be at least 1 hour'
  }
  if (newInterval.value > 168) {
    return 'Interval cannot exceed 168 hours (1 week)'
  }
  return ''
})

const isValid = computed(() => {
  return !validationError.value && newInterval.value !== props.currentInterval
})

// Format interval
const formatInterval = (hours: number) => {
  if (hours === 1) return '1 hour'
  if (hours < 24) return `${hours} hours`
  
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  
  if (remainingHours === 0) {
    return days === 1 ? '1 day' : `${days} days`
  }
  
  return `${days} ${days === 1 ? 'day' : 'days'} and ${remainingHours} ${remainingHours === 1 ? 'hour' : 'hours'}`
}

// Apply preset
const applyPreset = (hours: number) => {
  newInterval.value = hours
}

// Handle update
const handleUpdate = async () => {
  if (!isValid.value) return

  isUpdating.value = true
  try {
    emit('update-interval', newInterval.value)
    // Reset after a delay
    setTimeout(() => {
      isUpdating.value = false
    }, 1000)
  } catch (error) {
    isUpdating.value = false
  }
}

// Update new interval when current interval changes
watch(
  () => props.currentInterval,
  (value) => {
    newInterval.value = value
  }
)
</script>

