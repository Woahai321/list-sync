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

// API service
const api = useApiService()
const router = useRouter()
const { showInfo } = useToast()

// Check setup status on mount (backup check in case middleware doesn't catch it)
const checkSetup = async () => {
  // Skip if already on setup page
  if (router.currentRoute.value.path === '/setup') {
    return
  }

  try {
    const status: any = await api.checkSetupStatus()
    
    // If setup complete, continue normally
    if (status.is_complete) {
      return
    }
    
    // If .env exists and needs migration, auto-migrate
    if (status.needs_migration) {
      console.log('Migrating configuration from .env to database...')
      try {
        await api.migrateFromEnv()
        showInfo('Configuration Migrated', 'Your settings have been migrated to the database')
        console.log('Migration complete')
        // Reload to ensure everything is in sync
        window.location.reload()
      } catch (error) {
        console.error('Migration failed:', error)
        // Redirect to setup on migration failure
        router.replace('/setup')
      }
    } else {
      // No setup and no .env - redirect to setup wizard
      console.log('No configuration found, redirecting to setup wizard')
      router.replace('/setup')
    }
  } catch (error) {
    console.error('Error checking setup status:', error)
    // On error, redirect to setup (fail-closed)
    router.replace('/setup')
  }
}

// Load theme and check setup on mount
onMounted(() => {
  loadTheme()
  // Run setup check after a brief delay to ensure API is ready
  setTimeout(() => {
    checkSetup()
  }, 100)
})
</script>

