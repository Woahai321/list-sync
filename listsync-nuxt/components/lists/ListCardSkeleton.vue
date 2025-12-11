<template>
  <Card variant="hover" class="relative overflow-hidden border border-purple-500/30">
    <!-- Subtle gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-purple-500/5 opacity-60" />
    
    <!-- Content -->
    <div class="space-y-3 relative">
      <!-- Header -->
      <div class="pr-16">
        <div class="h-5 bg-purple-500/20 rounded-md w-3/4 mb-2 animate-pulse" />
        <div class="h-3 bg-purple-500/10 rounded-md w-1/2 animate-pulse" />
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-2 gap-2">
        <div class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
            <div class="w-3.5 h-3.5 bg-purple-400/30 rounded animate-pulse" />
          </div>
          <div>
            <div class="h-2.5 bg-purple-500/10 rounded w-12 mb-1 animate-pulse" />
            <div class="h-6 bg-purple-500/20 rounded w-16 animate-pulse" />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-gradient-to-br from-purple-500/18 to-purple-400/9 border border-purple-400/28">
            <div class="w-3.5 h-3.5 bg-purple-300/30 rounded animate-pulse" />
          </div>
          <div class="flex-1">
            <div class="h-2.5 bg-purple-500/10 rounded w-16 mb-1 animate-pulse" />
            <div class="h-4 bg-purple-500/20 rounded w-20 animate-pulse" />
          </div>
        </div>
      </div>

      <!-- Quick Actions Bar -->
      <div class="flex items-center gap-2">
        <div class="flex-1 h-8 bg-purple-500/10 rounded-lg animate-pulse" />
        <div class="w-8 h-8 bg-purple-500/10 rounded-lg animate-pulse" />
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-2 border-t border-purple-500/10">
        <div class="flex-1 h-9 bg-purple-500/20 rounded-lg animate-pulse" />
        <div class="w-16 h-9 bg-purple-500/10 rounded-lg animate-pulse" />
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
// Skeleton component for ListCard
</script>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>








