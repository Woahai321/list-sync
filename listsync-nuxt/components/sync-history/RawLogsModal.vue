<template>
  <Modal :is-open="true" size="2xl" @close="$emit('close')">
    <template #header>
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-foreground titillium-web-bold flex items-center gap-2">
            <component :is="FileTextIcon" :size="24" class="text-purple-400" />
            Raw Sync Logs
          </h2>
          <p class="text-sm text-muted-foreground mt-1">
            Session: {{ sessionId }}
          </p>
        </div>
        <Button
          v-if="logs"
          variant="secondary"
          size="sm"
          :icon="CopyIcon"
          @click="copyLogs"
        >
          Copy All
        </Button>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading logs..." />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <component :is="AlertCircleIcon" :size="48" class="text-red-400 mb-4" />
      <p class="text-foreground mb-2">Failed to load logs</p>
      <p class="text-sm text-muted-foreground">{{ error }}</p>
    </div>

    <!-- Logs Display -->
    <div v-else-if="logs" class="space-y-4">
      <!-- Stats -->
      <div class="flex items-center justify-between text-sm">
        <div class="flex items-center gap-4 text-muted-foreground">
          <span>{{ logs.line_count }} lines</span>
          <span v-if="logs.start_timestamp">{{ formatDate(logs.start_timestamp, 'PPpp') }}</span>
        </div>
      </div>

      <!-- Log Content -->
      <Card variant="flat" class="bg-black/50 border-purple-500/20">
        <div class="relative">
          <pre class="text-xs font-mono text-foreground overflow-x-auto max-h-[60vh] p-4 whitespace-pre-wrap break-words"><code>{{ logs.lines.join('\n') }}</code></pre>
          
          <!-- Scroll to bottom button -->
          <Button
            v-if="showScrollButton"
            variant="primary"
            size="sm"
            class="absolute bottom-4 right-4 shadow-lg"
            :icon="ArrowDownIcon"
            @click="scrollToBottom"
          >
            Scroll to Bottom
          </Button>
        </div>
      </Card>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3">
        <Button variant="secondary" @click="$emit('close')">
          Close
        </Button>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import {
  FileText as FileTextIcon,
  Copy as CopyIcon,
  AlertCircle as AlertCircleIcon,
  ArrowDown as ArrowDownIcon,
} from 'lucide-vue-next'

interface Props {
  sessionId: string
}

const props = defineProps<Props>()
defineEmits<{
  close: []
}>()

// State
const isLoading = ref(true)
const error = ref<string | null>(null)
const logs = ref<any>(null)
const showScrollButton = ref(false)

// API
const { showSuccess, showError } = useToast()
const api = useApiService()

// Load logs
const loadLogs = async () => {
  try {
    isLoading.value = true
    error.value = null
    logs.value = await api.getSyncSessionRawLogs(props.sessionId)
  } catch (err: any) {
    console.error('Error loading raw logs:', err)
    error.value = err.message || 'Failed to load logs'
  } finally {
    isLoading.value = false
  }
}

// Copy logs to clipboard
const copyLogs = async () => {
  if (!logs.value) return
  
  try {
    await navigator.clipboard.writeText(logs.value.lines.join('\n'))
    showSuccess('Logs copied to clipboard')
  } catch (err) {
    showError('Failed to copy logs')
  }
}

// Scroll to bottom
const scrollToBottom = () => {
  const pre = document.querySelector('pre')
  if (pre) {
    pre.scrollTop = pre.scrollHeight
  }
}

// Detect scroll
const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement
  const isNearBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 100
  showScrollButton.value = !isNearBottom && target.scrollHeight > target.clientHeight
}

// Initialize
onMounted(async () => {
  await loadLogs()
  
  // Add scroll listener
  nextTick(() => {
    const pre = document.querySelector('pre')
    if (pre) {
      pre.addEventListener('scroll', handleScroll)
      showScrollButton.value = pre.scrollHeight > pre.clientHeight
    }
  })
})

onUnmounted(() => {
  const pre = document.querySelector('pre')
  if (pre) {
    pre.removeEventListener('scroll', handleScroll)
  }
})
</script>

