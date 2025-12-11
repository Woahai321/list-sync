<template>
  <Card variant="default" class="overflow-hidden relative">
    <div class="space-y-3">
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
        <div
          v-for="i in 6"
          :key="`stat-skeleton-${i}`"
          class="p-3 sm:p-3 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/40 min-h-[80px] sm:min-h-0"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <SkeletonLoader width="auto" height="sm" class="w-3.5 h-3.5 rounded" />
            <SkeletonLoader width="1/3" height="xs" />
          </div>
          <SkeletonLoader width="2/3" height="lg" class="mb-0.5" />
          <SkeletonLoader width="1/2" height="xs" />
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import SkeletonLoader from '~/components/ui/SkeletonLoader.vue'
</script>

