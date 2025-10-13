<template>
  <div class="space-y-6">
    <!-- Page Disabled Message -->
    <Card>
      <div class="text-center py-20">
        <div class="text-6xl mb-4">🚧</div>
        <h1 class="text-2xl font-bold text-foreground mb-2">Page Disabled</h1>
        <p class="text-muted-foreground mb-6">
          The detailed session view has been disabled. Please return to the sync history page.
        </p>
        <Button
          variant="primary"
          :icon="ArrowLeftIcon"
          @click="$router.push('/sync-history')"
        >
          Back to Sync History
        </Button>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft as ArrowLeftIcon } from 'lucide-vue-next'

// Set page title
useHead({
  title: 'Sync Session Details - ListSync',
})
</script>