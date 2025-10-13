<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <ListCard
      v-for="list in lists"
      :key="`${list.list_type}-${list.list_id}`"
      :list="list"
      :selectable="selectable"
      :is-selected="isListSelected(list)"
      @sync="$emit('sync-list', list.list_type, list.list_id)"
      @delete="$emit('delete-list', list.list_type, list.list_id)"
      @toggle-select="$emit('toggle-select', list)"
    />
  </div>
</template>

<script setup lang="ts">
import type { List } from '~/types'

interface Props {
  lists: List[]
  selectable?: boolean
  selectedLists?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  selectable: false,
  selectedLists: () => new Set(),
})

defineEmits<{
  'sync-list': [listType: string, listId: string]
  'delete-list': [listType: string, listId: string]
  'toggle-select': [list: List]
}>()

// Check if a list is selected
const isListSelected = (list: List) => {
  const key = `${list.list_type}-${list.list_id}`
  return props.selectedLists.has(key)
}
</script>

