<template>
  <Modal
    v-model="isOpen"
    title="Delete List"
    size="md"
    @close="handleClose"
  >
    <div v-if="list" class="space-y-4">
      <!-- Warning Icon -->
      <div class="flex items-center justify-center py-4">
        <div class="p-4 rounded-full bg-red-500/20 border-2 border-red-500/40">
          <component :is="AlertTriangleIcon" :size="32" class="text-red-400" />
        </div>
      </div>

      <!-- Warning Message -->
      <div class="text-center space-y-2">
        <p class="text-lg font-semibold text-foreground">
          Are you sure you want to delete this list?
        </p>
        <p class="text-sm text-muted-foreground">
          This action cannot be undone.
        </p>
      </div>

      <!-- List Details -->
      <Card variant="default" class="bg-red-500/5 border-red-500/20">
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">List Name</span>
            <span class="text-sm font-medium text-foreground">{{ getDisplayName(list) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Provider</span>
            <span class="text-sm font-medium text-foreground">{{ formatProvider(list.list_type) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Items</span>
            <span class="text-sm font-medium text-foreground">{{ formatNumber(list.item_count) }}</span>
          </div>
          <div v-if="list.last_synced" class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Last Synced</span>
            <span class="text-sm font-medium text-foreground">
              <TimeAgo :timestamp="list.last_synced" />
            </span>
          </div>
        </div>
      </Card>

      <!-- Don't Ask Again Checkbox -->
      <label class="flex items-center gap-2 cursor-pointer group">
        <input
          v-model="dontAskAgain"
          type="checkbox"
          class="w-4 h-4 rounded border-2 border-purple-500/40 bg-black/40 text-purple-500 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-black cursor-pointer transition-all"
        />
        <span class="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
          Don't ask me again
        </span>
      </label>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3">
        <Button
          variant="ghost"
          @click="handleClose"
        >
          Cancel
        </Button>
        <Button
          variant="primary"
          :class="'bg-red-500 hover:bg-red-600 border-red-500'"
          @click="handleConfirm"
        >
          Delete List
        </Button>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { AlertTriangle as AlertTriangleIcon } from 'lucide-vue-next'
import type { List } from '~/types'

interface Props {
  modelValue: boolean
  list: List | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [dontAskAgain: boolean]
  'cancel': []
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dontAskAgain = ref(false)

const handleClose = () => {
  dontAskAgain.value = false
  emit('cancel')
}

const handleConfirm = () => {
  emit('confirm', dontAskAgain.value)
}

const getDisplayName = (list: List) => {
  return list.display_name || list.list_id
}

const formatProvider = (type: string) => {
  const providers: Record<string, string> = {
    imdb: 'IMDb',
    trakt: 'Trakt',
    trakt_special: 'Trakt Special',
    letterboxd: 'Letterboxd',
    mdblist: 'MDBList',
    stevenlu: 'Steven Lu',
    tmdb: 'TMDB',
    simkl: 'Simkl',
    tvdb: 'TVDB',
    anilist: 'AniList',
  }
  return providers[type.toLowerCase()] || type
}
</script>








