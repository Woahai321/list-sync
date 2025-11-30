<template>
  <div class="view-toggle inline-flex items-center gap-1 p-1 rounded-lg bg-purple-950/30 border border-purple-500/30">
    <button
      @click="$emit('update:modelValue', 'grid')"
      :class="[
        'px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2',
        modelValue === 'grid'
          ? 'bg-purple-600 text-white shadow-lg'
          : 'text-muted-foreground hover:text-foreground hover:bg-purple-900/30'
      ]"
      aria-label="Grid view"
    >
      <LayoutGridIcon :size="16" />
      <span class="hidden sm:inline">Grid</span>
    </button>
    
    <button
      @click="$emit('update:modelValue', 'list')"
      :class="[
        'px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2',
        modelValue === 'list'
          ? 'bg-purple-600 text-white shadow-lg'
          : 'text-muted-foreground hover:text-foreground hover:bg-purple-900/30'
      ]"
      aria-label="List view"
    >
      <ListIcon :size="16" />
      <span class="hidden sm:inline">List</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  LayoutGrid as LayoutGridIcon,
  List as ListIcon,
} from 'lucide-vue-next'

interface Props {
  modelValue: 'grid' | 'list'
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: 'grid' | 'list']
}>()
</script>

