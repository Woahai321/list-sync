<template>
  <Card variant="default" class="overflow-hidden relative group/card max-w-2xl mx-auto w-full">
    <!-- Animated gradient background -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-purple-500/5 to-transparent opacity-60 group-hover/card:opacity-80 transition-opacity duration-500" />
    
    <div class="relative space-y-4 sm:space-y-6">
      <!-- Header (only show on step 0 and 1, not on completion) -->
      <div v-if="currentStep < 2" class="text-center pt-4 sm:pt-6 px-4 sm:px-6">
        <div class="flex items-center justify-center mb-3 sm:mb-4">
          <img 
            :src="logoImage" 
            alt="ListSync Logo" 
            class="w-20 h-20 sm:w-32 sm:h-32 object-contain"
          />
        </div>
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground titillium-web-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent px-2">
          Welcome to ListSync
        </h1>
        <p class="text-muted-foreground mt-1.5 sm:mt-2 text-sm sm:text-base">
          Quick setup • {{ steps.length }} steps
        </p>
      </div>

      <!-- Progress Indicator (only show on step 0 and 1, not on completion) -->
      <div v-if="currentStep < 2" class="px-4 sm:px-6">
        <!-- Visual line indicators (like Add List Modal) -->
        <div class="flex items-center justify-center gap-1.5 sm:gap-2 mb-4 sm:mb-6">
          <div
            v-for="(step, index) in steps"
            :key="index"
            :class="[
              'h-1.5 rounded-full transition-all',
              index === currentStep ? 'w-6 sm:w-8 bg-purple-500' : index < currentStep ? 'w-5 sm:w-6 bg-purple-500/50' : 'w-5 sm:w-6 bg-white/10'
            ]"
          />
        </div>
      </div>

      <!-- Step Content -->
      <div class="px-4 sm:px-6 pb-4 sm:pb-6">
        <Step1Essential
          v-if="currentStep === 0"
          v-model="formData.step1"
          :is-validating="isValidating"
          :errors="validationErrors"
          @next="handleStep1Next"
          @clear-error="(field) => { 
            if (validationErrors.value[field]) {
              delete validationErrors.value[field]
            }
          }"
        />
        
        <Step2Configuration
          v-else-if="currentStep === 1"
          v-model="formData.step2"
          :is-validating="isValidating"
          :errors="validationErrors"
          @next="handleStep2Next"
          @back="currentStep--"
        />
        
        <SetupComplete v-else-if="currentStep === 2" />
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

// Form data for steps
const formData = ref({
  step1: {
    overseerr_url: '',
    overseerr_api_key: '',
    overseerr_user_id: '1',
    overseerr_4k: false,
    trakt_client_id: '',
  },
  step2: {
    sync_interval: 24,
    auto_sync: true,
    timezone: 'UTC',
    discord_webhook: '',
    discord_enabled: false,
  },
})

// Reset form data (useful for starting fresh)
const resetFormData = () => {
  formData.value = {
    step1: {
      overseerr_url: '',
      overseerr_api_key: '',
      overseerr_user_id: '1',
      overseerr_4k: false,
      trakt_client_id: '',
    },
    step2: {
      sync_interval: 24,
      auto_sync: true,
      timezone: 'UTC',
      discord_webhook: '',
      discord_enabled: false,
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
  
  // Get fresh values directly from formData to ensure we're using current data
  const step1Data = {
    overseerr_url: formData.value.step1.overseerr_url?.trim() || '',
    overseerr_api_key: formData.value.step1.overseerr_api_key?.trim() || '',
    overseerr_user_id: formData.value.step1.overseerr_user_id || '1',
    overseerr_4k: formData.value.step1.overseerr_4k || false,
    trakt_client_id: formData.value.step1.trakt_client_id?.trim() || '',
  }
  
  console.log('Saving Step 1 with values:', {
    overseerr_url: step1Data.overseerr_url,
    overseerr_api_key: step1Data.overseerr_api_key ? '***' : 'MISSING',
    trakt_client_id: step1Data.trakt_client_id ? '***' : 'MISSING'
  })
  
  try {
    const response: any = await api.saveStepEssential(step1Data)
    
    if (response.valid) {
      // Clear any errors on success
      validationErrors.value = {}
      showSuccess('Step 1 Complete', 'Essential configuration saved')
      currentStep.value++
    } else {
      // Set errors from response
      validationErrors.value = response.errors || {}
      
      // Build detailed error message
      const errorFields = Object.keys(validationErrors.value)
      let errorMessage = 'Please fix the following errors:'
      if (errorFields.length > 0) {
        errorMessage += '\n' + errorFields.map(field => {
          const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          return `• ${fieldName}: ${validationErrors.value[field]}`
        }).join('\n')
      }
      
      showError('Validation Failed', errorMessage)
    }
  } catch (error: any) {
    // Extract error details from API response
    let errorMessage = 'Failed to save configuration'
    
    if (error?.data?.detail) {
      errorMessage = error.data.detail
    } else if (error?.data?.errors) {
      // If we have field-specific errors, set them
      validationErrors.value = error.data.errors
      errorMessage = 'Please fix the errors and try again'
    } else if (error?.message) {
      errorMessage = error.message
    }
    
    // If we have validation errors, show them
    if (Object.keys(validationErrors.value).length > 0) {
      const errorFields = Object.keys(validationErrors.value)
      errorMessage = 'Please fix the following errors:\n' + errorFields.map(field => {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        return `• ${fieldName}: ${validationErrors.value[field]}`
      }).join('\n')
    }
    
    showError('Error', errorMessage)
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
</script>

