<template>
  <!-- Floating Action Button Menu (Bottom Right) -->
  <div class="fixed bottom-6 right-6 z-50 flex flex-col-reverse items-end gap-3">
    <!-- Action Buttons (show when expanded) -->
    <Transition name="slide-up">
      <div v-if="isExpanded" class="flex flex-col-reverse gap-2">
        <!-- Trigger Sync -->
        <button
          :class="[
            'group flex items-center gap-3 px-4 py-3 rounded-full shadow-lg backdrop-blur-md transition-all duration-200',
            syncStore.isSyncing 
              ? 'bg-purple-600/90 text-white cursor-not-allowed' 
              : 'bg-gray-900/90 text-foreground hover:bg-purple-600/90 hover:text-white hover:scale-105'
          ]"
          :disabled="syncStore.isSyncing"
          @click="handleTriggerSync"
        >
          <component 
            :is="syncStore.isSyncing ? LoaderIcon : RefreshCwIcon" 
            :size="20" 
            :class="syncStore.isSyncing ? 'animate-spin' : 'group-hover:rotate-90 transition-transform duration-300'" 
          />
          <span class="text-sm font-medium whitespace-nowrap">
            {{ syncStore.isSyncing ? 'Syncing...' : 'Trigger Sync' }}
          </span>
        </button>

        <!-- Add List -->
        <button
          class="group flex items-center gap-3 px-4 py-3 rounded-full bg-gray-900/90 backdrop-blur-md text-foreground hover:bg-green-600/90 hover:text-white shadow-lg hover:scale-105 transition-all duration-200"
          @click="handleAction(() => $router.push('/lists?action=add'))"
        >
          <component :is="PlusCircleIcon" :size="20" class="group-hover:scale-110 transition-transform duration-300" />
          <span class="text-sm font-medium whitespace-nowrap">Add List</span>
        </button>

        <!-- Sync History -->
        <button
          class="group flex items-center gap-3 px-4 py-3 rounded-full bg-gray-900/90 backdrop-blur-md text-foreground hover:bg-purple-600/90 hover:text-white shadow-lg hover:scale-105 transition-all duration-200"
          @click="handleAction(() => $router.push('/sync-history'))"
        >
          <component :is="HistoryIcon" :size="20" class="group-hover:scale-110 transition-transform duration-300" />
          <span class="text-sm font-medium whitespace-nowrap">Sync History</span>
        </button>

        <!-- Settings -->
        <button
          class="group flex items-center gap-3 px-4 py-3 rounded-full bg-gray-900/90 backdrop-blur-md text-foreground hover:bg-amber-600/90 hover:text-white shadow-lg hover:scale-105 transition-all duration-200"
          @click="handleAction(() => $router.push('/settings'))"
        >
          <component :is="SettingsIcon" :size="20" class="group-hover:rotate-90 transition-transform duration-300" />
          <span class="text-sm font-medium whitespace-nowrap">Settings</span>
        </button>
      </div>
    </Transition>

    <!-- Main Toggle Button -->
    <button
      class="w-14 h-14 rounded-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white shadow-2xl hover:shadow-purple-500/50 flex items-center justify-center transition-all duration-300 hover:scale-110"
      :class="{ 'rotate-45': isExpanded }"
      @click="isExpanded = !isExpanded"
      aria-label="Quick Actions Menu"
    >
      <component :is="isExpanded ? XIcon : ZapIcon" :size="24" class="transition-transform duration-300" />
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshCwIcon,
  PlusCircle as PlusCircleIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Loader2 as LoaderIcon,
  Zap as ZapIcon,
  X as XIcon,
} from 'lucide-vue-next'

const syncStore = useSyncStore()
const { showSuccess, showError } = useToast()

// State for expanded/collapsed menu
const isExpanded = ref(false)

// Handle action and collapse menu
const handleAction = (action: () => void) => {
  action()
  isExpanded.value = false
}

const handleTriggerSync = async () => {
  if (syncStore.isSyncing) return

  try {
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Your sync has been triggered successfully')
    isExpanded.value = false // Collapse menu
    navigateTo('/logs')
  } catch (error: any) {
    showError('Sync Failed', error.message || 'Failed to trigger sync')
  }
}
</script>

<style scoped>
/* Slide up animation for action buttons */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>

