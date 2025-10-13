<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-4xl font-bold text-foreground titillium-web-bold">
          Processed Items
        </h1>
        <p class="text-base text-muted-foreground mt-2">
          All items that have been processed by ListSync
        </p>
      </div>

      <div class="flex gap-3">
        <Button
          variant="ghost"
          :icon="ArrowLeftIcon"
          @click="$router.back()"
        >
          Back
        </Button>
        
        <Button
          variant="primary"
          :icon="RefreshIcon"
          :loading="isRefreshing"
          @click="refreshData"
        >
          Refresh
        </Button>
      </div>
    </div>

    <!-- Processed Items Component -->
    <ProcessedItems />
  </div>
</template>

<script setup lang="ts">
import {
  RefreshCw as RefreshIcon,
  ArrowLeft as ArrowLeftIcon,
} from 'lucide-vue-next'

// Set page title
useHead({
  title: 'Processed Items',
})

const isRefreshing = ref(false)

// Refresh data
const refreshData = async () => {
  isRefreshing.value = true
  // Component has its own refresh logic
  setTimeout(() => {
    window.location.reload()
  }, 100)
}
</script>

