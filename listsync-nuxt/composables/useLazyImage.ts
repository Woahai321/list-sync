/**
 * Smart lazy loading composable with Intersection Observer
 * 
 * Provides smarter image loading than native lazy loading:
 * - Starts loading images 400px before they become visible
 * - Tracks load state for animations and placeholders
 * - Automatically cleans up observers
 * - Handles errors gracefully
 */

export function useLazyImage(imageUrl: Ref<string | null | undefined>) {
  const imageLoaded = ref(false)
  const imageError = ref(false)
  const actualSrc = ref<string | null>(null)
  const imageRef = ref<HTMLElement | null>(null)

  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!process.client || !imageRef.value || !imageUrl.value) return

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

