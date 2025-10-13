<template>
  <div class="space-y-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold">
          History
        </h1>
        <p class="text-muted-foreground mt-2 text-base">
          View activity history and processed items
        </p>
      </div>

      <div class="flex items-center gap-3">
        <Button
          variant="secondary"
          :icon="RefreshIcon"
          :loading="isRefreshing"
          size="lg"
          @click="handleRefresh"
        >
          Refresh
        </Button>
      </div>
    </div>

    <!-- Tabs -->
    <HistoryTabs
      :active-tab="activeTab"
      :counts="tabCounts"
      @update:active-tab="changeTab"
    />

    <!-- Tab Content -->
    <div class="min-h-[400px]">
      <!-- Recent Activity Tab -->
      <ActivityList
        v-if="activeTab === 'recent'"
        :key="refreshKey"
      />

      <!-- Processed Items Tab -->
      <ProcessedItems
        v-else-if="activeTab === 'processed'"
        :key="refreshKey"
      />

      <!-- Requested Items Tab -->
      <RequestedItems
        v-else-if="activeTab === 'requested'"
        :key="refreshKey"
      />

      <!-- Successful Items Tab -->
      <SuccessItems
        v-else-if="activeTab === 'success'"
        :key="refreshKey"
      />

      <!-- Failed Items Tab -->
      <FailedItems
        v-else-if="activeTab === 'failed'"
        :key="refreshKey"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
} from 'lucide-vue-next'

// Set page title
useHead({
  title: 'History - ListSync',
})

// State
const activeTab = ref<'recent' | 'processed' | 'requested' | 'success' | 'failed'>('recent')
const isRefreshing = ref(false)
const refreshKey = ref(0)

// Tab counts (to be fetched from API)
const tabCounts = ref({
  recent: 0,
  processed: 0,
  requested: 0,
  success: 0,
  failed: 0,
})

// Change tab
const changeTab = (newTab: typeof activeTab.value) => {
  activeTab.value = newTab
}

// Refresh current tab
const handleRefresh = () => {
  isRefreshing.value = true
  refreshKey.value++
  
  // Reset after a delay
  setTimeout(() => {
    isRefreshing.value = false
  }, 500)
}

// Fetch tab counts
const fetchTabCounts = async () => {
  try {
    // Get stats from sync stats API
    const stats: any = await $fetch('/api/stats/sync').catch(() => null)
    const recentActivity: any = await $fetch('/api/activity/recent?limit=1').catch(() => null)
    
    if (stats) {
      tabCounts.value = {
        recent: recentActivity?.total_items || 0,
        processed: stats.total_processed || 0,
        requested: stats.total_requested || 0,
        success: stats.successful_items || 0,
        failed: stats.total_errors || 0,
      }
    }
  } catch (error) {
    console.error('Error fetching tab counts:', error)
  }
}

// Fetch counts on mount
onMounted(() => {
  fetchTabCounts()
})
</script>

