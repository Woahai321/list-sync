<template>
  <Card class="glass-card p-2">
    <div class="flex items-center gap-2 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap transition-all duration-200"
        :class="[
          activeTab === tab.id
            ? 'bg-primary text-primary-foreground shadow-lg'
            : 'hover:bg-muted/50 text-muted-foreground hover:text-foreground'
        ]"
        @click="$emit('update:active-tab', tab.id)"
      >
        <component :is="tab.icon" class="w-4 h-4 flex-shrink-0" />
        <span class="font-medium">{{ tab.label }}</span>
        <Badge
          v-if="counts[tab.id] !== undefined"
          :variant="activeTab === tab.id ? 'default' : 'secondary'"
          size="sm"
          class="ml-1"
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

