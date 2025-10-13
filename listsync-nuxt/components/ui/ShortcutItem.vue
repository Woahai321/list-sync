<template>
  <div class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/5 transition-colors">
    <span class="text-sm text-muted-foreground">{{ description }}</span>
    <div class="flex items-center gap-1">
      <kbd v-if="ctrl" class="kbd">Ctrl</kbd>
      <kbd v-if="shift" class="kbd">Shift</kbd>
      <kbd class="kbd">{{ shortcut }}</kbd>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  shortcut: string
  description: string
  ctrl?: boolean
  shift?: boolean
}

withDefaults(defineProps<Props>(), {
  ctrl: false,
  shift: false,
})
</script>

<style scoped>
.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 600;
  color: hsl(var(--foreground));
  background-color: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 0.375rem;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
</style>

