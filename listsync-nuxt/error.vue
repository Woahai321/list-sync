<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-black">
    <!-- Floating orbs background -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute top-20% left-10% w-[300px] h-[300px] bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow" />
      <div class="absolute bottom-20% right-10% w-[200px] h-[200px] bg-accent/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1s" />
    </div>

    <div class="relative z-10 max-w-2xl w-full">
      <Card variant="default" class="text-center">
        <!-- Error Icon -->
        <div class="mb-6 flex justify-center">
          <div class="p-6 rounded-full bg-gradient-to-br from-red-500/20 to-rose-600/20 animate-pulse-slow">
            <component 
              :is="error.statusCode === 404 ? SearchXIcon : AlertTriangleIcon" 
              :size="64" 
              class="text-red-400"
            />
          </div>
        </div>

        <!-- Error Code -->
        <div class="mb-4">
          <h1 class="text-8xl font-black text-foreground titillium-web-black mb-2 tabular-nums">
            {{ error.statusCode || 500 }}
          </h1>
          <h2 class="text-2xl font-bold text-foreground titillium-web-bold">
            {{ errorTitle }}
          </h2>
        </div>

        <!-- Error Message -->
        <p class="text-muted-foreground mb-8 text-lg">
          {{ errorMessage }}
        </p>

        <!-- Technical Details (in development) -->
        <div 
          v-if="showDetails && error.message" 
          class="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-left"
        >
          <p class="text-sm font-mono text-red-300 break-all">
            {{ error.message }}
          </p>
        </div>

        <!-- Actions -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            variant="primary"
            size="lg"
            :icon="HomeIcon"
            @click="handleClearError"
          >
            Go to Dashboard
          </Button>

          <Button
            variant="secondary"
            size="lg"
            :icon="RefreshCwIcon"
            @click="handleRefresh"
          >
            Refresh Page
          </Button>

          <Button
            v-if="error.statusCode !== 404"
            variant="ghost"
            size="lg"
            :icon="ChevronLeftIcon"
            @click="handleGoBack"
          >
            Go Back
          </Button>
        </div>

        <!-- Help Text -->
        <div class="mt-8 pt-8 border-t border-purple-500/10">
          <p class="text-sm text-muted-foreground">
            If this problem persists, please check your configuration or 
            <a href="https://github.com/your-repo/listsync" target="_blank" class="text-purple-400 hover:text-purple-300 underline">
              report an issue
            </a>
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Home as HomeIcon,
  RefreshCw as RefreshCwIcon,
  ChevronLeft as ChevronLeftIcon,
  AlertTriangle as AlertTriangleIcon,
  SearchX as SearchXIcon,
} from 'lucide-vue-next'
import type { NuxtError } from '#app'

interface Props {
  error: NuxtError
}

const props = defineProps<Props>()

// Show technical details in development
const showDetails = process.dev

const errorTitle = computed(() => {
  switch (props.error.statusCode) {
    case 404:
      return 'Page Not Found'
    case 500:
      return 'Internal Server Error'
    case 403:
      return 'Access Forbidden'
    case 401:
      return 'Unauthorized'
    default:
      return 'Something Went Wrong'
  }
})

const errorMessage = computed(() => {
  switch (props.error.statusCode) {
    case 404:
      return 'The page you are looking for doesn\'t exist or has been moved.'
    case 500:
      return 'We encountered an unexpected error. Our team has been notified.'
    case 403:
      return 'You don\'t have permission to access this resource.'
    case 401:
      return 'You need to be authenticated to access this page.'
    default:
      return props.error.message || 'An unexpected error occurred. Please try again.'
  }
})

const handleClearError = () => {
  clearError({ redirect: '/' })
}

const handleRefresh = () => {
  if (process.client) {
    window.location.reload()
  }
}

const handleGoBack = () => {
  if (process.client && window.history.length > 1) {
    window.history.back()
  } else {
    clearError({ redirect: '/' })
  }
}
</script>

