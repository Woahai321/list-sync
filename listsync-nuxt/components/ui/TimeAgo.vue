<template>
  <ClientOnly>
    <span>{{ formattedTime }}</span>
    <template #fallback>
      <span class="opacity-50">...</span>
    </template>
  </ClientOnly>
</template>

<script setup lang="ts">
import { formatRelativeTime } from '~/utils/formatters'

interface Props {
  timestamp: string | Date | null | undefined
}

const props = defineProps<Props>()

const formattedTime = computed(() => formatRelativeTime(props.timestamp))
</script>

