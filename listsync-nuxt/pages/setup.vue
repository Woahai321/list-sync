<template>
  <div class="setup-background flex items-center justify-center p-2 sm:p-4 min-h-screen">
    <!-- Animated Lines Background -->
    <div class="setup-lines">
      <div v-for="i in 10" :key="i" class="setup-line" :style="{ animationDelay: `${i * 0.5}s` }"></div>
    </div>
    
    <!-- Setup Wizard Container -->
    <div class="w-full max-w-4xl relative z-10 px-2 sm:px-0">
      <SetupWizard />
    </div>
  </div>
</template>

<script setup lang="ts">
// Set page title
useHead({
  title: 'Setup - ListSync',
})

// Prevent navigation away from setup
definePageMeta({
  layout: false,
})
</script>

