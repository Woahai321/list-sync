<template>
  <div class="flex h-screen overflow-hidden bg-black">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Mobile Backdrop -->
    <Transition name="fade">
      <div
        v-if="uiStore.mobileMenuOpen"
        class="fixed inset-0 z-30 bg-black/80 backdrop-blur-sm lg:hidden"
        @click="uiStore.closeMobileMenu"
      />
    </Transition>

    <!-- Main Content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Mobile Header -->
      <header class="flex items-center justify-between px-6 py-4 border-b border-purple-500/20 lg:hidden">
        <button
          type="button"
          class="p-2 rounded-lg hover:bg-white/5 transition-colors text-foreground"
          @click="uiStore.toggleMobileMenu"
          aria-label="Open menu"
        >
          <component :is="MenuIcon" :size="24" />
        </button>

        <h1 class="text-lg font-bold">ListSync</h1>

        <div class="w-10" /> <!-- Spacer for centering -->
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto custom-scrollbar floating-orbs relative">
        <div class="container mx-auto px-4 py-8 max-w-7xl">
          <ErrorBoundary>
            <slot />
          </ErrorBoundary>
        </div>
      </main>
    </div>

    <!-- Toast Container -->
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { Menu as MenuIcon } from 'lucide-vue-next'

const uiStore = useUIStore()

// Initialize theme on mount
onMounted(() => {
  uiStore.initTheme()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

