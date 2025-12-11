<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="text-center py-6 sm:py-8">
      <!-- Mascot Icon -->
      <div class="flex items-center justify-center mb-4 sm:mb-6">
        <div
          class="relative"
          :class="[
            isSyncing && 'mascot-pulse-glow'
          ]"
        >
          <img 
            :src="logoImage" 
            alt="ListSync Mascot" 
            class="w-20 h-20 sm:w-24 sm:h-24 object-contain"
          />
        </div>
      </div>

      <!-- Status Text -->
      <h3 class="text-xl sm:text-2xl font-bold mb-2 titillium-web-bold">
        {{ statusTitle }}
      </h3>
      <p class="text-muted-foreground mb-6 sm:mb-8 text-sm">
        {{ statusDescription }}
      </p>

      <!-- Sync Buttons - Improved styling -->
      <div class="flex flex-col sm:flex-row gap-3 justify-center items-stretch sm:items-center">
        <Button
          v-if="!isSyncing"
          variant="primary"
          :icon="PlayIcon"
          size="lg"
          class="w-full sm:w-auto sm:min-w-[200px] touch-manipulation"
          @click="$emit('trigger-sync')"
        >
          Start Sync Now
        </Button>
        
        <Button
          v-else
          variant="danger"
          :icon="StopIcon"
          size="lg"
          class="w-full sm:w-auto sm:min-w-[200px] touch-manipulation"
          @click="$emit('stop-sync')"
        >
          Stop Sync
        </Button>
      </div>

      <!-- Helper text -->
      <p class="text-xs text-muted-foreground mt-3">
        {{ isSyncing ? 'Click stop to immediately terminate the sync' : 'Click to begin synchronization' }}
      </p>

      <!-- Sync Info - Removed (now in SyncStatusCards) -->
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Play as PlayIcon,
  RefreshCw as RefreshCwIcon,
  Square as StopIcon,
} from 'lucide-vue-next'
import logoImage from '~/assets/images/list-sync-logo.webp'

interface Props {
  isSyncing: boolean
  lastSync: string | null
  nextSync: string | null
}

const props = defineProps<Props>()

defineEmits<{
  'trigger-sync': []
  'stop-sync': []
}>()

// Status computed
const statusTitle = computed(() => {
  return props.isSyncing ? 'Sync in Progress' : 'Ready to Sync'
})

const statusDescription = computed(() => {
  return props.isSyncing
    ? 'Your data is being synchronized...'
    : 'Start synchronization to update your lists'
})
</script>

<style scoped>
/* Purple pulsating glow animation for mascot */
@keyframes mascot-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 10px rgba(168, 85, 247, 0.4));
  }
  50% {
    filter: drop-shadow(0 0 25px rgba(168, 85, 247, 0.8)) drop-shadow(0 0 40px rgba(168, 85, 247, 0.6));
  }
}

.mascot-pulse-glow {
  animation: mascot-pulse 1.5s ease-in-out infinite;
}

/* Button active state */
.active\:scale-98:active {
  transform: scale(0.98);
}
</style>
