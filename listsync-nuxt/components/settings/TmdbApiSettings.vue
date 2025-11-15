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
            TMDB API Configuration
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            Optional - for faster processing and better reliability
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="space-y-4">
        <!-- TMDB API Key -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            TMDB API Key
            <span class="text-muted-foreground">(Optional)</span>
          </label>
          <Input
            v-model="localValue.apiKey"
            type="password"
            placeholder="Enter your TMDB API Key"
            :icon="KeyIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Get your API key from <a href="https://www.themoviedb.org/settings/api" target="_blank" class="text-purple-400 hover:text-purple-300 underline">TMDB API Settings</a>
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">Why use TMDB API?</p>
            <ul class="text-muted-foreground space-y-1 list-disc list-inside">
              <li>Much faster than web scraping</li>
              <li>More reliable (no UI changes affect it)</li>
              <li>Comprehensive metadata access</li>
              <li>40 requests per 10 seconds rate limit</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Help Box -->
      <div class="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <HelpCircleIcon class="w-5 h-5 text-purple-400 flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-purple-400 mb-1">How to get your TMDB API Key</p>
            <ol class="text-muted-foreground space-y-1 list-decimal list-inside">
              <li>Visit <a href="https://www.themoviedb.org/settings/api" target="_blank" class="text-purple-400 hover:text-purple-300 underline">themoviedb.org/settings/api</a></li>
              <li>Click "Request an API Key"</li>
              <li>Fill in the application details</li>
              <li>Copy the API Key (v3 auth)</li>
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

interface TmdbApiSettings {
  apiKey: string
}

interface Props {
  modelValue: TmdbApiSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: TmdbApiSettings]
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


