<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <NetworkIcon class="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <h3 class="text-base font-bold titillium-web-semibold">
            Service Endpoints
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            Configure service URLs and domains
          </p>
        </div>
      </div>

      <!-- Form Fields -->
      <div class="grid grid-cols-1 gap-4">
        <!-- Frontend Domain -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            Frontend Domain
          </label>
          <Input
            v-model="localValue.frontendDomain"
            type="url"
            placeholder="http://localhost:3222"
            :icon="GlobeIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            URL where the Nuxt 3 Dashboard is accessible
          </p>
        </div>

        <!-- Backend Domain -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            Backend Domain
          </label>
          <Input
            v-model="localValue.backendDomain"
            type="url"
            placeholder="http://localhost:4222"
            :icon="ServerIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            URL where the FastAPI Server is running
          </p>
        </div>

        <!-- Nuxt Public API URL -->
        <div>
          <label class="block text-[10px] font-bold mb-1.5 uppercase tracking-wide">
            Nuxt Public API URL
          </label>
          <Input
            v-model="localValue.nuxtPublicApiUrl"
            type="url"
            placeholder="http://localhost:4222"
            :icon="LinkIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Public API URL for client-side requests (no /api suffix needed)
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="bg-info/10 border border-info/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <InfoIcon class="w-5 h-5 text-info flex-shrink-0" />
          <div class="text-sm">
            <p class="font-medium text-info mb-1">Service Endpoints</p>
            <p class="text-muted-foreground">
              These URLs define how different parts of ListSync communicate. Changes to these settings require a container restart to take effect.
            </p>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Network as NetworkIcon,
  Globe as GlobeIcon,
  Server as ServerIcon,
  Link as LinkIcon,
  Info as InfoIcon,
} from 'lucide-vue-next'

interface ServiceEndpointsSettings {
  frontendDomain: string
  backendDomain: string
  nuxtPublicApiUrl: string
}

interface Props {
  modelValue: ServiceEndpointsSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: ServiceEndpointsSettings]
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

