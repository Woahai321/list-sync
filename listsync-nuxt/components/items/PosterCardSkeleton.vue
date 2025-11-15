<template>
  <div class="poster-card-skeleton animate-fade-in">
    <!-- Poster Placeholder -->
    <div class="poster-container relative w-full rounded-xl overflow-hidden shadow-xl bg-gradient-to-br from-gray-900 via-purple-950/10 to-gray-900">
      <!-- Aspect ratio keeper (2:3 for movie posters) -->
      <div class="aspect-[2/3] relative">
        <!-- Shimmer effect -->
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent shimmer" />
        
        <!-- Icon placeholder -->
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="w-16 h-16 bg-purple-500/10 rounded-full animate-pulse" />
        </div>
        
        <!-- Badge placeholders (matching new design) -->
        <div class="absolute top-2 left-2 w-6 h-6 bg-purple-600/20 rounded-md animate-pulse" />
        <div class="absolute top-2 right-2 w-6 h-6 bg-purple-600/20 rounded-md animate-pulse" />
        
        <!-- Title placeholder -->
        <div class="absolute bottom-3 left-3 right-3 space-y-2">
          <div class="h-4 bg-gray-700/50 rounded-md w-4/5 animate-pulse" />
          <div class="h-3 bg-purple-700/30 rounded-md w-2/5 animate-pulse" />
        </div>
      </div>
    </div>
    
    <!-- Glow effect (matches PosterCard) -->
    <div class="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-purple-500/20 to-purple-600/20 rounded-xl opacity-50 -z-10 blur-lg" />
  </div>
</template>

<style scoped>
.poster-card-skeleton {
  position: relative;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.shimmer {
  animation: shimmer 2.5s ease-in-out infinite;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Fade in animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}

/* Stagger animation delay for skeleton items */
.poster-card-skeleton:nth-child(1) { animation-delay: 0ms; }
.poster-card-skeleton:nth-child(2) { animation-delay: 50ms; }
.poster-card-skeleton:nth-child(3) { animation-delay: 100ms; }
.poster-card-skeleton:nth-child(4) { animation-delay: 150ms; }
.poster-card-skeleton:nth-child(5) { animation-delay: 200ms; }
.poster-card-skeleton:nth-child(6) { animation-delay: 250ms; }
.poster-card-skeleton:nth-child(7) { animation-delay: 300ms; }
.poster-card-skeleton:nth-child(8) { animation-delay: 350ms; }
.poster-card-skeleton:nth-child(9) { animation-delay: 400ms; }
.poster-card-skeleton:nth-child(10) { animation-delay: 450ms; }
</style>

