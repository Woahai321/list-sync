<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <BellIcon class="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 class="text-base font-bold titillium-web-semibold">
              Notification Settings
            </h3>
            <p class="text-[10px] text-muted-foreground font-medium">
              Configure notification preferences
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          :loading="isTesting"
          @click="$emit('test-notification')"
        >
          <SendIcon class="w-4 h-4 mr-2" />
          Send Test
        </Button>
      </div>

      <!-- Form Fields -->
      <div class="space-y-4">
        <!-- Discord Webhook -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Discord Webhook URL
          </label>
          <Input
            v-model="localValue.discordWebhook"
            type="url"
            placeholder="https://discord.com/api/webhooks/..."
            :icon="MessageSquareIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            Get notified in Discord when sync completes
          </p>
        </div>

        <!-- Discord Notifications Toggle -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Discord Notifications
          </label>
          <div class="flex items-center gap-3">
            <!-- Status Label -->
            <span 
              :class="[
                'text-sm font-semibold tabular-nums',
                localValue.enabled ? 'text-green-400' : 'text-gray-400'
              ]"
            >
              {{ localValue.enabled ? 'ON' : 'OFF' }}
            </span>
            
            <!-- Toggle Switch -->
            <button
              type="button"
              role="switch"
              :aria-checked="localValue.enabled"
              :class="[
                'relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-black',
                localValue.enabled ? 'bg-green-500' : 'bg-gray-600'
              ]"
              @click="toggleEnabled"
            >
              <span
                :class="[
                  'inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white shadow-lg transition-all duration-200',
                  localValue.enabled ? 'translate-x-7' : 'translate-x-0.5'
                ]"
              >
                <!-- Icon inside toggle -->
                <CheckIcon v-if="localValue.enabled" :size="14" class="text-green-500" />
                <XIcon v-else :size="14" class="text-gray-600" />
              </span>
            </button>
            
            <span class="text-sm text-muted-foreground">
              {{ localValue.enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <p class="text-xs text-muted-foreground mt-1.5">
            Send sync completion summary to Discord
          </p>
        </div>
      </div>

      <!-- Help Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">How to get a Discord Webhook</p>
            <ol class="text-muted-foreground space-y-1 list-decimal list-inside">
              <li>Go to your Discord server settings</li>
              <li>Navigate to Integrations → Webhooks</li>
              <li>Click "New Webhook" and copy the URL</li>
              <li>Paste the URL above and click "Send Test"</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Bell as BellIcon,
  Send as SendIcon,
  MessageSquare as MessageSquareIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  X as XIcon,
} from 'lucide-vue-next'

interface NotificationSettings {
  discordWebhook: string
  enabled: boolean
}

interface Props {
  modelValue: NotificationSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: NotificationSettings]
  'test-notification': []
}>()

const localValue = ref({ ...props.modelValue })
const isTesting = ref(false)

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

// Toggle function
const toggleEnabled = () => {
  localValue.value.enabled = !localValue.value.enabled
  emitUpdate()
}
</script>

