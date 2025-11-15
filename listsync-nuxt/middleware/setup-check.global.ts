/**
 * Setup Check Middleware (Global)
 * 
 * Ensures user completes setup wizard before accessing the app.
 * Redirects to /setup if configuration is incomplete.
 * 
 * This middleware runs on ALL routes except /setup itself.
 * 
 * In Nuxt 3, .global.ts suffix makes this run automatically on all routes.
 */

export default defineNuxtRouteMiddleware(async (to) => {
  // Allow access to setup page itself
  if (to.path === '/setup') {
    return
  }

  // On server-side, we need to check but can't use client-side APIs
  // So we'll let it pass and check on client-side
  if (process.server) {
    // On server, we can't make API calls easily, so we'll check on client
    // This prevents hydration mismatches
    return
  }

  // Client-side check - this runs on initial page load and navigation
  try {
    const api = useApiService()
    
    // Check setup status
    const status: any = await api.checkSetupStatus()
    
    // If setup is complete, allow navigation
    if (status?.is_complete) {
      return
    }
    
    // If .env exists and needs migration, auto-migrate
    if (status?.needs_migration) {
      console.log('Auto-migrating .env to database...')
      try {
        await api.migrateFromEnv()
        console.log('Migration complete, continuing to app')
        // Reload page to ensure everything is in sync
        window.location.reload()
        return
      } catch (error) {
        console.error('Migration failed:', error)
        // On migration failure, redirect to setup
        return navigateTo('/setup', { replace: true })
      }
    }
    
    // Setup not complete and no migration needed - redirect to setup
    console.log('Setup not complete, redirecting to wizard')
    return navigateTo('/setup', { replace: true })
    
  } catch (error) {
    console.error('Error checking setup status:', error)
    // On error, redirect to setup (fail-closed to ensure setup completes)
    return navigateTo('/setup', { replace: true })
  }
})

