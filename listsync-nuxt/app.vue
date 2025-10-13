<template>
  <div>
    <!-- Skip to main content (accessibility) -->
    <a href="#main-content" class="skip-to-content">
      Skip to main content
    </a>

    <!-- Main Layout -->
    <NuxtLayout>
      <main id="main-content">
        <NuxtPage :key="$route.fullPath" />
      </main>
    </NuxtLayout>

    <!-- Keyboard Shortcuts Modal -->
    <KeyboardShortcutsModal v-model="showShortcutsHelp" />

    <!-- Toast Container (for notifications) -->
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
// Global app setup
useHead({
  titleTemplate: (titleChunk) => {
    return titleChunk ? `${titleChunk} | ListSync` : 'ListSync'
  },
  htmlAttrs: {
    lang: 'en',
  },
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { name: 'theme-color', content: '#9d34da' },
  ],
})

// Setup keyboard shortcuts
const { showShortcutsHelp } = useKeyboardShortcuts()

// Initialize theme system
const { loadTheme } = useTheme()

// Load theme on mount
onMounted(() => {
  loadTheme()
})
</script>

