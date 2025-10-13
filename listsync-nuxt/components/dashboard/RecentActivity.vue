<template>
  <Card variant="default">
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">Recent Activity</h3>
        <Button
          variant="ghost"
          size="sm"
          @click="$router.push('/recent-activity')"
        >
          View All
        </Button>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="md" text="Loading activity..." />
    </div>

    <!-- Activity List -->
    <div v-else-if="activities.length > 0" class="space-y-2">
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors"
      >
        <!-- Status Icon -->
        <div :class="getStatusClasses(activity.status)">
          <component :is="getStatusIcon(activity.status)" :size="16" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="font-medium text-foreground truncate">
              {{ activity.title }}
            </p>
            <Badge :variant="getMediaTypeBadge(activity.media_type)" size="sm">
              {{ formatMediaType(activity.media_type) }}
            </Badge>
          </div>
          <p class="text-xs text-muted-foreground mt-0.5">
            {{ getActionText(activity.action) }}
          </p>
        </div>

        <!-- Time -->
        <div class="flex-shrink-0 text-right">
          <p class="text-xs text-muted-foreground">
            <TimeAgo :timestamp="activity.last_synced" />
          </p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else
      :icon="ActivityIcon"
      title="No recent activity"
      description="Activity will appear here after syncing"
    />
  </Card>
</template>

<script setup lang="ts">
import {
  CheckCircle2 as CheckIcon,
  XCircle as ErrorIcon,
  MinusCircle as SkipIcon,
  Clock as PendingIcon,
  Activity as ActivityIcon,
} from 'lucide-vue-next'
import type { RecentActivity } from '~/types'

interface Props {
  activities: RecentActivity[]
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
})

const getStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    synced: CheckIcon,
    requested: CheckIcon,
    available: CheckIcon,
    success: CheckIcon,
    error: ErrorIcon,
    not_found: ErrorIcon,
    failed: ErrorIcon,
    skipped: SkipIcon,
    pending: PendingIcon,
  }
  return iconMap[status] || PendingIcon
}

const getStatusClasses = (status: string) => {
  const baseClasses = 'flex items-center justify-center w-8 h-8 rounded-lg'
  
  const statusClasses: Record<string, string> = {
    synced: 'bg-green-500/20 text-green-400',
    requested: 'bg-green-500/20 text-green-400',
    available: 'bg-blue-500/20 text-blue-400',
    success: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400',
    not_found: 'bg-red-500/20 text-red-400',
    failed: 'bg-red-500/20 text-red-400',
    skipped: 'bg-yellow-500/20 text-yellow-400',
    pending: 'bg-gray-500/20 text-gray-400',
  }

  return `${baseClasses} ${statusClasses[status] || statusClasses.pending}`
}

const getMediaTypeBadge = (type: string): 'primary' | 'info' => {
  return type === 'movie' ? 'primary' : 'info'
}

const formatMediaType = (type: string) => {
  return type === 'movie' ? 'Movie' : 'TV'
}

const getActionText = (action: string) => {
  const actionMap: Record<string, string> = {
    synced: 'Successfully synced',
    requested: 'Requested to Overseerr',
    available: 'Already available',
    success: 'Successfully processed',
    error: 'Failed to process',
    not_found: 'Not found in database',
    failed: 'Processing failed',
    skipped: 'Skipped (already available)',
    pending: 'Pending',
  }
  return actionMap[action] || action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}
</script>

