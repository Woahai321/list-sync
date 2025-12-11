/**
 * Smart lazy loading composable with Intersection Observer
 * 
 * Provides smarter image loading than native lazy loading:
 * - Starts loading images 400px before they become visible
 * - Tracks load state for animations and placeholders
 * - Automatically cleans up observers
 * - Handles errors gracefully
 * - Watches for URL changes (handles async poster loading)
 */

export function useLazyImage(imageUrl: Ref<string | null | undefined>) {
  const imageLoaded = ref(false)
  const imageError = ref(false)
  const actualSrc = ref<string | null>(null)
  const imageRef = ref<HTMLElement | null>(null)

  let observer: IntersectionObserver | null = null

  // Setup or re-setup the intersection observer
  const setupObserver = () => {
    if (!process.client || !imageRef.value || !imageUrl.value) return
    if (actualSrc.value) return // Already loaded, no need to observe

    // Check if element is already in or near the viewport
    const rect = imageRef.value.getBoundingClientRect()
    const isInViewport = rect.top < window.innerHeight + 400 && rect.bottom > -400

    if (isInViewport) {
      // Element is already visible or near viewport - load immediately
      actualSrc.value = imageUrl.value
      return
    }

    // Clean up existing observer before creating new one
    if (observer) {
      observer.disconnect()
    }

    // Set up observer for lazy loading
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !actualSrc.value && imageUrl.value) {
            // Image is approaching viewport - start loading
            actualSrc.value = imageUrl.value
            if (observer) {
              observer.disconnect()
            }
          }
        })
      },
      {
        // Start loading 400px before image enters viewport (roughly 2 screen heights)
        // This ensures images are ready when user scrolls to them
        rootMargin: '400px',
        threshold: 0
      }
    )

    observer.observe(imageRef.value)
  }

  onMounted(() => {
    setupObserver()
  })

  // Watch for URL changes - this handles async poster loading
  // When poster URLs are fetched in the background and become available,
  // we need to set up the observer or load the image immediately if in view
  watch(imageUrl, (newUrl) => {
    if (newUrl && !actualSrc.value) {
      // URL just became available, set up observer on next tick
      // (ensures DOM ref is ready)
      nextTick(() => {
        setupObserver()
      })
    }
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  const handleLoad = () => {
    imageLoaded.value = true
  }

  const handleError = () => {
    imageError.value = true
  }

  return {
    imageRef,
    actualSrc,
    imageLoaded,
    imageError,
    handleLoad,
    handleError,
  }
}
