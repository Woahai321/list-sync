<template>
  <Card variant="default" class="overflow-hidden relative group/card max-w-4xl mx-auto w-full">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <!-- Live region for screen reader announcements -->
    <div class="sr-only" role="status" aria-live="polite" aria-atomic="true">
      {{ screenReaderAnnouncement }}
    </div>
    
    <div class="relative space-y-3 sm:space-y-4">
      <!-- Header (only show on step 0 and 1, not on completion) -->
      <div v-if="currentStep < 2" class="text-center pt-3 sm:pt-4 px-4 sm:px-6">
        <div class="flex items-center justify-center mb-2 sm:mb-3">
          <img 
            :src="logoImage" 
            alt="ListSync Logo" 
            class="w-16 h-16 sm:w-20 sm:h-20 object-contain"
          />
        </div>
        <h1 class="text-xl sm:text-2xl md:text-3xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent px-2">
          Welcome to ListSync
        </h1>
        <p class="text-muted-foreground mt-1 sm:mt-1.5 text-xs sm:text-sm">
          Quick setup • {{ steps.length }} steps
        </p>
      </div>

      <!-- Progress Indicator (only show on step 0 and 1, not on completion) -->
      <div v-if="currentStep < 2" class="px-4 sm:px-6">
        <!-- Visual line indicators with labels -->
        <div class="mb-3 sm:mb-4">
          <!-- Step indicators -->
          <div class="flex items-center justify-center gap-1.5 sm:gap-2 mb-2">
            <div
              v-for="(step, index) in steps"
              :key="index"
              :class="[
                'h-1.5 rounded-full transition-all duration-500',
                index === currentStep ? 'w-8 sm:w-10 bg-purple-500 shadow-lg shadow-purple-500/50' : 
                index < currentStep ? 'w-6 sm:w-8 bg-green-500 shadow-md shadow-green-500/30' : 
                'w-6 sm:w-8 bg-white/10'
              ]"
            />
          </div>
          
          <!-- Step labels with checkmarks -->
          <div class="flex items-center justify-center gap-4 sm:gap-8 mt-2 sm:mt-3">
            <div
              v-for="(step, index) in steps"
              :key="`label-${index}`"
              class="flex flex-col items-center min-w-[70px] sm:min-w-[90px] transition-all duration-300"
            >
              <!-- Checkmark or step number -->
              <div
                :class="[
                  'w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center mb-1.5 transition-all duration-300',
                  index < currentStep ? 'bg-green-500 text-white scale-100' :
                  index === currentStep ? 'bg-purple-500 text-white scale-110 shadow-lg shadow-purple-500/50' :
                  'bg-white/10 text-muted-foreground scale-100'
                ]"
              >
                <component 
                  v-if="index < currentStep" 
                  :is="CheckIcon" 
                  :size="14" 
                  class="animate-scale-in"
                />
                <span v-else class="text-xs sm:text-sm font-bold">{{ index + 1 }}</span>
              </div>
              
              <!-- Step label -->
              <span
                :class="[
                  'text-xs sm:text-sm font-semibold transition-all duration-300',
                  index === currentStep ? 'text-purple-400' :
                  index < currentStep ? 'text-green-400' :
                  'text-muted-foreground'
                ]"
              >
                {{ step.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="px-4 sm:px-6 pb-3 sm:pb-4">
        <Transition 
          name="step-transition" 
          mode="out-in"
          @before-enter="onBeforeEnter"
          @enter="onEnter"
          @leave="onLeave"
        >
          <Step1Essential
            v-if="currentStep === 0"
            key="step1"
            v-model="formData.step1"
            :is-validating="isValidating"
            :errors="validationErrors"
            @next="handleStep1Next"
            @clear-error="(field) => { 
              try {
                if (validationErrors.value && field && typeof field === 'string' && validationErrors.value[field]) {
                  delete validationErrors.value[field]
                }
              } catch (e) {
                // Silently ignore errors in clearError handler
                console.debug('Error in clearError handler:', e)
              }
            }"
          />
          
          <Step2Configuration
            v-else-if="currentStep === 1"
            key="step2"
            v-model="formData.step2"
            :is-validating="isValidating"
            :errors="validationErrors"
            @next="handleStep2Next"
            @back="currentStep--"
          />
          
          <SetupComplete v-else-if="currentStep === 2" key="complete" />
        </Transition>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Check as CheckIcon,
} from 'lucide-vue-next'
import logoImage from '~/assets/images/list-sync-logo.webp'

const { showSuccess, showError } = useToast()
const api = useApiService()
const router = useRouter()

// Steps configuration (removed Content Sources)
const steps = [
  { name: 'Connect', key: 'step1' },
  { name: 'Configure', key: 'step2' },
]

// Current step state
const currentStep = ref(0)
const isValidating = ref(false)
const validationErrors = ref<Record<string, string>>({})

// Screen reader announcement for step changes
const screenReaderAnnouncement = ref('')

// Update screen reader announcement when step changes
watch(currentStep, (newStep, oldStep) => {
  if (newStep !== oldStep) {
    if (newStep === 0) {
      screenReaderAnnouncement.value = 'Step 1 of 2: Connect to Overseerr'
    } else if (newStep === 1) {
      screenReaderAnnouncement.value = 'Step 2 of 2: Configure your settings'
    } else if (newStep === 2) {
      screenReaderAnnouncement.value = 'Setup complete! Redirecting to lists page...'
    }
  }
}, { immediate: true })

// Form data for steps
const formData = ref({
  step1: {
    overseerr_url: '',
    overseerr_api_key: '',
    overseerr_user_id: '1',
  },
  step2: {
    sync_interval: 24,
    auto_sync: true,
    timezone: 'UTC',
    discord_webhook: '',
    discord_enabled: false,
    trakt_client_id: '',
  },
})

// Reset form data (useful for starting fresh)
const resetFormData = () => {
  formData.value = {
    step1: {
      overseerr_url: '',
      overseerr_api_key: '',
      overseerr_user_id: '1',
    },
    step2: {
      sync_interval: 24,
      auto_sync: true,
      timezone: 'UTC',
      discord_webhook: '',
      discord_enabled: false,
      trakt_client_id: '',
    },
  }
  validationErrors.value = {}
  currentStep.value = 0
}

// Reset on mount to ensure clean state
onMounted(() => {
  resetFormData()
})

// Handle Step 1 submission
const handleStep1Next = async () => {
  // Clear all previous errors first
  validationErrors.value = {}
  isValidating.value = true
  
  // Credentials are ALREADY saved during the "Test Connection & Sync Users" button
  // We just need to verify they exist in the database
  try {
    // Get config to verify credentials were saved
    const config = await api.getConfig()
    
    if (!config.overseerr_url || !config.overseerr_api_key) {
      throw new Error('Credentials not found. Please click "Sync Users from Overseerr" first.')
    }
    
    console.log('Step 1 credentials verified in database:', {
      overseerr_url: config.overseerr_url,
      overseerr_api_key: config.overseerr_api_key ? '***' : 'MISSING',
      overseerr_user_id: config.overseerr_user_id || '1'
    })
    
    // Update formData with the saved values
    formData.value.step1 = {
      overseerr_url: config.overseerr_url,
      overseerr_api_key: config.overseerr_api_key,
      overseerr_user_id: config.overseerr_user_id || '1',
    }
    
    // Move to next step
    currentStep.value++
  } catch (error: any) {
    console.error('Step 1 validation error:', error)
    validationErrors.value = {
      overseerr_url: error.message || 'Please test your Overseerr connection first'
    }
    showError('Validation Failed', error.message || 'Please click "Sync Users from Overseerr" to test your connection first.')
  } finally {
    isValidating.value = false
  }
}

// Handle Step 2 submission (final step)
const handleStep2Next = async () => {
  isValidating.value = true
  validationErrors.value = {}
  
  try {
    const response: any = await api.saveStepConfiguration(formData.value.step2)
    
    if (response.valid) {
      // Mark setup as complete
      await api.completeSetup()
      
      // Move to completion screen (no toast - completion screen shows success)
      currentStep.value++
      
      // Store flag in sessionStorage as fallback
      if (process.client) {
        sessionStorage.setItem('listsync_open_add_modal', 'true')
      }
      
      // Redirect to lists page with add modal after showing completion message
      // Use replace to avoid adding to history
      // Stay on page for 2 seconds as requested
      setTimeout(() => {
        router.replace('/lists?action=add')
      }, 2000)
    } else {
      validationErrors.value = response.errors || {}
      showError('Validation Failed', 'Please fix the errors and try again')
    }
  } catch (error: any) {
    showError('Error', error.message || 'Failed to save configuration')
  } finally {
    isValidating.value = false
  }
}

// Transition animations
const onBeforeEnter = (el: Element) => {
  const element = el as HTMLElement
  element.style.opacity = '0'
  element.style.transform = 'translateX(30px)'
}

const onEnter = (el: Element, done: () => void) => {
  const element = el as HTMLElement
  element.offsetHeight // Trigger reflow
  element.style.transition = 'opacity 0.3s ease, transform 0.3s ease'
  element.style.opacity = '1'
  element.style.transform = 'translateX(0)'
  setTimeout(done, 300)
}

const onLeave = (el: Element, done: () => void) => {
  const element = el as HTMLElement
  element.style.transition = 'opacity 0.3s ease, transform 0.3s ease'
  element.style.opacity = '0'
  element.style.transform = 'translateX(-30px)'
  setTimeout(done, 300)
}
</script>

