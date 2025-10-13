<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center animate-fade-in">
    <!-- Icon with animation -->
    <div class="mb-6 rounded-full bg-gradient-to-br from-purple-500/20 to-accent/20 p-8 backdrop-blur-sm border border-purple-500/20 animate-pulse-slow">
      <component
        v-if="icon"
        :is="icon"
        :size="iconSize"
        class="text-purple-400"
      />
    </div>

    <!-- Title -->
    <h3 v-if="title" class="mb-3 text-2xl font-bold text-foreground titillium-web-bold">
      {{ title }}
    </h3>

    <!-- Description -->
    <p v-if="description" class="mb-8 max-w-lg text-base text-muted-foreground leading-relaxed">
      {{ description }}
    </p>

    <!-- Action Button -->
    <slot name="action">
      <Button
        v-if="actionLabel"
        :icon="actionIcon"
        variant="primary"
        size="lg"
        @click="$emit('action')"
      >
        {{ actionLabel }}
      </Button>
    </slot>

    <!-- Additional Content -->
    <div v-if="$slots.default" class="mt-8">
      <slot />
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse-slow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}

.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}
</style>

<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  icon?: Component
  iconSize?: number
  title?: string
  description?: string
  actionLabel?: string
  actionIcon?: Component
}

withDefaults(defineProps<Props>(), {
  iconSize: 48,
})

defineEmits<{
  action: []
}>()
</script>

