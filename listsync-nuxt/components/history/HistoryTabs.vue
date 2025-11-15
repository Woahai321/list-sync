<template>
  <Card class="glass-card p-2 border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="flex items-center gap-2 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-1.5 px-3 py-2 rounded-lg whitespace-nowrap transition-all duration-200"
        :class="[
          activeTab === tab.id
            ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-sm'
            : 'hover:bg-purple-500/10 text-muted-foreground hover:text-purple-300 border border-transparent'
        ]"
        @click="$emit('update:active-tab', tab.id)"
      >
        <component :is="tab.icon" class="w-3.5 h-3.5 flex-shrink-0" />
        <span class="text-xs font-bold uppercase tracking-wide">{{ tab.label }}</span>
        <Badge
          v-if="counts[tab.id] !== undefined"
          :variant="activeTab === tab.id ? 'default' : 'secondary'"
          size="sm"
          class="ml-1 text-[10px]"
        >
          {{ formatCount(counts[tab.id]) }}
        </Badge>
      </button>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Activity as ActivityIcon,
  Database as DatabaseIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
} from 'lucide-vue-next'

interface Props {
  activeTab: string
  counts?: Record<string, number>
}

withDefaults(defineProps<Props>(), {
  counts: () => ({}),
})

defineEmits<{
  'update:active-tab': [tab: string]
}>()

const tabs = [
  {
    id: 'recent',
    label: 'Recent Activity',
    icon: ActivityIcon,
  },
  {
    id: 'processed',
    label: 'Processed',
    icon: DatabaseIcon,
  },
  {
    id: 'requested',
    label: 'Requested',
    icon: SendIcon,
  },
  {
    id: 'success',
    label: 'Successful',
    icon: CheckCircleIcon,
  },
  {
    id: 'failed',
    label: 'Failed',
    icon: XCircleIcon,
  },
]

// Format count for display
const formatCount = (count: number) => {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`
  }
  return count.toString()
}
</script>

