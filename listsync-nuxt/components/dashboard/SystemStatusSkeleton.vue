<template>
  <Card variant="default" class="overflow-hidden relative">
    <div class="space-y-3">
      <!-- Top Row: Overall Health -->
      <div class="p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/40">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-1.5">
            <SkeletonLoader width="auto" height="sm" class="w-3.5 h-3.5 rounded" />
            <SkeletonLoader width="1/4" height="xs" />
          </div>
          <SkeletonLoader width="1/4" height="xs" class="rounded-full" />
        </div>
        <div class="flex items-center gap-3">
          <SkeletonLoader width="1/3" height="lg" />
          <div class="flex-1">
            <SkeletonLoader width="1/2" height="xs" />
          </div>
        </div>
      </div>

      <!-- Service Status Grid -->
      <div class="grid grid-cols-3 gap-2">
        <div
          v-for="i in 3"
          :key="`service-skeleton-${i}`"
          class="p-2.5 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-400/10 border border-purple-500/40"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <SkeletonLoader width="auto" height="sm" class="w-3.5 h-3.5 rounded" />
            <SkeletonLoader width="auto" height="xs" class="w-1.5 h-1.5 rounded-full" />
          </div>
          <SkeletonLoader width="2/3" height="sm" class="mb-0.5" />
          <SkeletonLoader width="1/2" height="xs" />
        </div>
      </div>

      <!-- Sync Timing Info -->
      <div class="grid grid-cols-2 gap-2">
        <div
          v-for="i in 2"
          :key="`timing-skeleton-${i}`"
          class="p-2 rounded-lg bg-purple-500/5 border border-purple-500/10"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <SkeletonLoader width="auto" height="xs" class="w-1.5 h-1.5 rounded-full" />
            <SkeletonLoader width="1/3" height="xs" />
          </div>
          <SkeletonLoader width="2/3" height="sm" />
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import SkeletonLoader from '~/components/ui/SkeletonLoader.vue'
</script>

