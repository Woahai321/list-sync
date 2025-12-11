<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <ServerIcon class="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 class="text-base font-bold titillium-web-semibold">
              Overseerr Configuration
            </h3>
            <p class="text-[10px] text-muted-foreground font-medium">
              Configure your Overseerr instance connection
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          :loading="isTesting"
          @click="$emit('test-connection')"
        >
          <TestTubeIcon class="w-4 h-4 mr-2" />
          Test Connection
        </Button>
      </div>

      <!-- Form Fields -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- URL -->
        <div class="md:col-span-2">
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Overseerr URL
            <span class="text-danger ml-1">*</span>
          </label>
          <Input
            v-model="localValue.url"
            type="url"
            placeholder="https://overseerr.example.com"
            :icon="GlobeIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            The full URL to your Overseerr instance
          </p>
        </div>

        <!-- API Key -->
        <div class="md:col-span-2">
          <label class="block text-xs font-semibold mb-2 text-foreground">
            API Key
            <span class="text-danger ml-1">*</span>
          </label>
          <Input
            v-model="localValue.apiKey"
            type="password"
            placeholder="Enter your Overseerr API key"
            :icon="KeyIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            Found in Overseerr Settings → General → API Key
          </p>
        </div>

        <!-- 4K Toggle -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            4K Requests
          </label>
          <div class="flex items-center gap-3">
            <!-- Status Label -->
            <span 
              :class="[
                'text-sm font-semibold tabular-nums min-w-[32px]',
                localValue.enable4k ? 'text-green-400' : 'text-gray-400'
              ]"
            >
              {{ localValue.enable4k ? 'ON' : 'OFF' }}
            </span>
            
            <!-- Toggle Switch -->
            <button
              type="button"
              role="switch"
              :aria-checked="localValue.enable4k"
              :class="[
                'relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-black',
                localValue.enable4k ? 'bg-green-500' : 'bg-gray-600'
              ]"
              @click="toggleEnable4k"
            >
              <span
                :class="[
                  'inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white shadow-lg transition-all duration-200',
                  localValue.enable4k ? 'translate-x-7' : 'translate-x-0.5'
                ]"
              >
                <!-- Icon inside toggle -->
                <CheckIcon v-if="localValue.enable4k" :size="14" class="text-green-500" />
                <XIcon v-else :size="14" class="text-gray-600" />
              </span>
            </button>
            
            <span class="text-sm text-muted-foreground">
              {{ localValue.enable4k ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <p class="text-xs text-muted-foreground mt-1.5">
            Send requests as 4K to Overseerr
          </p>
        </div>
      </div>

      <!-- Connection Status -->
      <div
        v-if="connectionStatus"
        class="p-4 rounded-lg"
        :class="[
          connectionStatus.connected
            ? 'bg-success/10 border border-success/20'
            : 'bg-danger/10 border border-danger/20'
        ]"
      >
        <div class="flex items-start gap-2">
          <component
            :is="connectionStatus.connected ? CheckCircleIcon : XCircleIcon"
            :class="[
              'w-5 h-5 flex-shrink-0',
              connectionStatus.connected ? 'text-success' : 'text-danger'
            ]"
          />
          <div>
            <p
              :class="[
                'font-medium',
                connectionStatus.connected ? 'text-success' : 'text-danger'
              ]"
            >
              {{ connectionStatus.connected ? 'Connected' : 'Connection Failed' }}
            </p>
            <p class="text-sm text-muted-foreground mt-1">
              {{ connectionStatus.message || 'Test connection to verify settings' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Server as ServerIcon,
  TestTube as TestTubeIcon,
  Globe as GlobeIcon,
  Key as KeyIcon,
  CheckCircle as CheckCircleIcon,
  Check as CheckIcon,
  X as XIcon,
  XCircle as XCircleIcon,
} from 'lucide-vue-next'

interface OverseerrConfig {
  url: string
  apiKey: string
  userId: string
  enable4k: boolean
}

interface Props {
  modelValue: OverseerrConfig
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: OverseerrConfig]
  'test-connection': []
}>()

const localValue = ref({ ...props.modelValue })
const isTesting = ref(false)
const connectionStatus = ref<{ connected: boolean; message?: string } | null>(null)

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

// Toggle 4K
const toggleEnable4k = () => {
  localValue.value.enable4k = !localValue.value.enable4k
  emitUpdate()
}
</script>

