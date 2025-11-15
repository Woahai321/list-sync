<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <KeyIcon class="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <h3 class="text-base font-bold titillium-web-semibold">
            Trakt API Configuration
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            Required for accurate title matching via TMDB/IMDB ID resolution
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="space-y-4">
        <!-- Trakt Client ID -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            Trakt Client ID
            <span class="text-danger">*</span>
          </label>
          <Input
            v-model="localValue.clientId"
            type="text"
            placeholder="Enter your Trakt Client ID"
            :icon="KeyIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Get your Client ID from <a href="https://trakt.tv/oauth/applications" target="_blank" class="text-purple-400 hover:text-purple-300 underline">Trakt OAuth Applications</a>
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">Why is this required?</p>
            <ul class="text-muted-foreground space-y-1 list-disc list-inside">
              <li>Direct TMDB ID lookup (Trakt lists provide this automatically)</li>
              <li>IMDB ID → Trakt API → TMDB ID resolution</li>
              <li>Title/Year → Trakt API → TMDB ID lookup</li>
              <li>Without it, only fallback to Overseerr text search (less accurate)</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Help Box -->
      <div class="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <HelpCircleIcon class="w-5 h-5 text-purple-400 flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-purple-400 mb-1">How to get your Trakt Client ID</p>
            <ol class="text-muted-foreground space-y-1 list-decimal list-inside">
              <li>Visit <a href="https://trakt.tv/oauth/applications" target="_blank" class="text-purple-400 hover:text-purple-300 underline">trakt.tv/oauth/applications</a></li>
              <li>Click "New Application"</li>
              <li>Fill in the application details</li>
              <li>Copy the Client ID (NOT the Client Secret)</li>
              <li>Paste it above</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Key as KeyIcon,
  Info as InfoIcon,
  HelpCircle as HelpCircleIcon,
} from 'lucide-vue-next'

interface TraktApiSettings {
  clientId: string
}

interface Props {
  modelValue: TraktApiSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: TraktApiSettings]
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

