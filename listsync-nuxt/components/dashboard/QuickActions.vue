<template>
  <Card variant="default" class="overflow-hidden relative">
    <!-- Subtle animated background -->
    <div class="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-transparent to-accent/5 opacity-50" />
    
    <template #header>
      <h3 class="text-xl font-bold titillium-web-bold relative">Quick Actions</h3>
    </template>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 relative">
      <!-- Trigger Sync -->
      <button
        :class="[
          actionButtonClasses,
          syncStore.isSyncing 
            ? 'bg-purple-500/20 border-purple-500/50' 
            : 'hover:border-purple-500/40'
        ]"
        :disabled="syncStore.isSyncing"
        @click="handleTriggerSync"
      >
        <component 
          :is="syncStore.isSyncing ? LoaderIcon : RefreshCwIcon" 
          :size="18" 
          :class="syncStore.isSyncing ? 'animate-spin' : 'group-hover:rotate-90 transition-transform duration-300'" 
        />
        <span class="text-sm font-medium">
          {{ syncStore.isSyncing ? 'Syncing...' : 'Trigger Sync' }}
        </span>
      </button>

      <!-- Add List -->
      <button
        :class="[actionButtonClasses, 'hover:border-green-500/40']"
        @click="$router.push('/lists?action=add')"
      >
        <component :is="PlusCircleIcon" :size="18" class="group-hover:scale-110 transition-transform duration-300" />
        <span class="text-sm font-medium">Add List</span>
      </button>

      <!-- Sync History -->
      <button
        :class="[actionButtonClasses, 'hover:border-purple-500/40']"
        @click="$router.push('/sync-history')"
      >
        <component :is="HistoryIcon" :size="18" class="group-hover:scale-110 transition-transform duration-300" />
        <span class="text-sm font-medium">Sync History</span>
      </button>

      <!-- Settings -->
      <button
        :class="[actionButtonClasses, 'hover:border-amber-500/40']"
        @click="$router.push('/settings')"
      >
        <component :is="SettingsIcon" :size="18" class="group-hover:rotate-90 transition-transform duration-300" />
        <span class="text-sm font-medium">Settings</span>
      </button>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshCwIcon,
  PlusCircle as PlusCircleIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Loader2 as LoaderIcon,
} from 'lucide-vue-next'

const syncStore = useSyncStore()
const { showSuccess, showError } = useToast()

const actionButtonClasses = computed(() => {
  return [
    'flex items-center justify-center gap-2 px-4 py-3',
    'rounded-lg border border-purple-500/20',
    'bg-black/20',
    'hover:border-purple-500/50 hover:bg-purple-500/10',
    'active:scale-98',
    'transition-all duration-200',
    'text-foreground hover:text-purple-300',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'shadow-sm hover:shadow-lg hover:shadow-purple-500/10',
    'group',
  ].join(' ')
})

const handleTriggerSync = async () => {
  if (syncStore.isSyncing) return

  try {
    await syncStore.triggerSync()
    showSuccess('Sync Started', 'Your sync has been triggered successfully')
  } catch (error: any) {
    showError('Sync Failed', error.message || 'Failed to trigger sync')
  }
}
</script>

