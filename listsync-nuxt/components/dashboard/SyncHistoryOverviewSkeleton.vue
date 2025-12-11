<template>
  <Card variant="default" class="overflow-hidden relative">
    <div class="space-y-3">
      <!-- Top Row: Main Metrics -->
      <div class="grid grid-cols-3 gap-2">
        <div
          v-for="i in 3"
          :key="`main-skeleton-${i}`"
          class="p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <SkeletonLoader width="auto" height="sm" class="w-3.5 h-3.5 rounded" />
            <SkeletonLoader width="1/3" height="xs" />
          </div>
          <SkeletonLoader width="2/3" height="lg" class="mb-0.5" />
          <SkeletonLoader width="1/2" height="xs" />
        </div>
      </div>

      <!-- Recent Activity & Stats -->
      <div class="grid grid-cols-3 gap-2">
        <div
          v-for="i in 3"
          :key="`activity-skeleton-${i}`"
          class="p-2 rounded-lg bg-purple-600/10 border border-purple-600/20"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <SkeletonLoader width="auto" height="xs" class="w-1.5 h-1.5 rounded-full" />
            <SkeletonLoader width="1/3" height="xs" />
          </div>
          <SkeletonLoader width="1/2" height="md" />
        </div>
      </div>

      <!-- Bottom Stats Grid -->
      <div class="grid grid-cols-3 gap-2">
        <div
          v-for="i in 3"
          :key="`bottom-skeleton-${i}`"
          class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <SkeletonLoader width="auto" height="xs" class="w-1.5 h-1.5 rounded-full" />
            <SkeletonLoader width="1/3" height="xs" />
          </div>
          <SkeletonLoader width="1/2" height="sm" />
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import SkeletonLoader from '~/components/ui/SkeletonLoader.vue'
</script>

