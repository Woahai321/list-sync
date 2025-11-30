<template>
  <div class="text-center py-12 space-y-8 relative overflow-visible min-h-[450px] flex flex-col items-center justify-center px-4 animate-fade-in" ref="containerRef">
    <!-- Content (above confetti) -->
    <div class="relative z-10 flex flex-col items-center justify-center space-y-8">
      <!-- Logo with success badge -->
      <div class="flex justify-center">
        <div class="relative">
          <!-- Subtle glow -->
          <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full blur-xl" />
          
          <!-- Logo Image -->
          <div class="relative">
            <img 
              :src="logoImage" 
              alt="ListSync Logo" 
              class="w-32 h-32 sm:w-40 sm:h-40 object-contain relative z-10"
            />
            
            <!-- Success checkmark badge -->
            <div class="absolute -top-2 -right-2 bg-gradient-to-br from-green-400 to-green-600 rounded-full p-2 shadow-lg animate-scale-in">
              <component :is="CheckCircleIcon" class="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      </div>

      <!-- Success Message -->
      <div class="space-y-4">
        <h2 class="text-4xl sm:text-5xl font-bold titillium-web-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-600 bg-clip-text text-transparent">
          Congratulations!
        </h2>
        <p class="text-lg sm:text-xl text-foreground">
          Core setup complete.
        </p>
        <p class="text-base text-muted-foreground mt-6">
          Redirecting you to add your first list...
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CheckCircle as CheckCircleIcon,
} from 'lucide-vue-next'
import logoImage from '~/assets/images/list-sync-logo.webp'

const confettiCanvas = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLElement | null>(null)

interface ConfettiParticle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  rotation: number
  rotationSpeed: number
}

const particles = ref<ConfettiParticle[]>([])

const launchConfetti = () => {
  if (!containerRef.value || !process.client) return
  
  // Create canvas element and add to setup page background
  const canvas = document.createElement('canvas')
  canvas.className = 'fixed top-0 left-0 w-screen h-screen pointer-events-none'
  canvas.style.zIndex = '2' // Between background lines (1) and content (10)
  canvas.style.width = '100vw'
  canvas.style.height = '100vh'
  
  // Add canvas to the setup background container
  const setupBackground = document.querySelector('.setup-background')
  if (setupBackground) {
    setupBackground.appendChild(canvas)
    confettiCanvas.value = canvas
  } else {
    // Fallback: add to body
    document.body.appendChild(canvas)
    confettiCanvas.value = canvas
  }
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // Set canvas size to match full viewport (for fullscreen effect)
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  canvas.width = viewportWidth
  canvas.height = viewportHeight
  
  // Get the content box position to launch from left and right of it
  const contentBox = containerRef.value?.closest('.max-w-4xl')?.getBoundingClientRect()
  const centerX = viewportWidth / 2
  const centerY = viewportHeight / 2
  
  // Launch positions: left of box, center, and right of box
  const leftX = contentBox ? contentBox.left - 50 : viewportWidth * 0.25
  const rightX = contentBox ? contentBox.right + 50 : viewportWidth * 0.75
  
  // Purple color variations
  const purpleColors = [
    '#a855f7', // purple-500
    '#9333ea', // purple-600
    '#7e22ce', // purple-700
    '#c084fc', // purple-400
    '#d8b4fe', // purple-300
  ]
  
  // Create particles from multiple launch points - spread across screen
  const particleCount = 150 // Reduced particle count for cleaner effect
  particles.value = []
  
  // Launch from left side of box
  for (let i = 0; i < particleCount / 3; i++) {
    particles.value.push({
      x: leftX + (Math.random() - 0.5) * 100, // Spread around left position
      y: centerY + (Math.random() - 0.5) * 100,
      vx: (Math.random() - 0.3) * 18 - 2, // Bias to the right
      vy: (Math.random() - 0.5) * 15 - 4,
      size: Math.random() * 12 + 5,
      color: purpleColors[Math.floor(Math.random() * purpleColors.length)],
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.5,
    })
  }
  
  // Launch from center
  for (let i = 0; i < particleCount / 3; i++) {
    particles.value.push({
      x: centerX + (Math.random() - 0.5) * 100,
      y: centerY + (Math.random() - 0.5) * 100,
      vx: (Math.random() - 0.5) * 20, // Spread in all directions
      vy: (Math.random() - 0.5) * 15 - 4,
      size: Math.random() * 12 + 5,
      color: purpleColors[Math.floor(Math.random() * purpleColors.length)],
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.5,
    })
  }
  
  // Launch from right side of box
  for (let i = 0; i < particleCount / 3; i++) {
    particles.value.push({
      x: rightX + (Math.random() - 0.5) * 100, // Spread around right position
      y: centerY + (Math.random() - 0.5) * 100,
      vx: (Math.random() - 0.7) * 18 + 2, // Bias to the left
      vy: (Math.random() - 0.5) * 15 - 4,
      size: Math.random() * 12 + 5,
      color: purpleColors[Math.floor(Math.random() * purpleColors.length)],
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.5,
    })
  }
  
  // Animation loop
  const animate = () => {
    if (!ctx || !canvas || !confettiCanvas.value) return
    
    // Update canvas size if window resized (fullscreen)
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    if (canvas.width !== viewportWidth || canvas.height !== viewportHeight) {
      canvas.width = viewportWidth
      canvas.height = viewportHeight
    }
    
    // Clear canvas completely first
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Add slight dark overlay for trail effect (optional)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.02)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    // Update and draw particles
    particles.value = particles.value.filter((particle) => {
      particle.x += particle.vx
      particle.y += particle.vy
      particle.vy += 0.2 // gravity
      particle.rotation += particle.rotationSpeed
      
      // Draw particle with 60% opacity
      ctx.save()
      ctx.translate(particle.x, particle.y)
      ctx.rotate(particle.rotation)
      ctx.globalAlpha = 0.6
      ctx.fillStyle = particle.color
      ctx.fillRect(-particle.size / 2, -particle.size / 2, particle.size, particle.size)
      ctx.restore()
      
      // Keep particle if it's still on screen
      return (
        particle.x > -10 &&
        particle.x < canvas.width + 10 &&
        particle.y > -10 &&
        particle.y < canvas.height + 10
      )
    })
    
    // Continue animation if particles remain
    if (particles.value.length > 0) {
      requestAnimationFrame(animate)
    } else {
      // Clear canvas when done
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
  }
  
  animate()
}

onMounted(() => {
  if (process.client) {
    // Wait for container to be fully rendered before launching confetti
    nextTick(() => {
      setTimeout(() => {
        launchConfetti()
      }, 300)
    })
    
    // Handle window resize (fullscreen)
    const handleResize = () => {
      if (confettiCanvas.value) {
        const viewportWidth = window.innerWidth
        const viewportHeight = window.innerHeight
        confettiCanvas.value.width = viewportWidth
        confettiCanvas.value.height = viewportHeight
      }
    }
    
    window.addEventListener('resize', handleResize)
    
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      // Clean up canvas when component unmounts
      if (confettiCanvas.value && confettiCanvas.value.parentNode) {
        confettiCanvas.value.parentNode.removeChild(confettiCanvas.value)
      }
    })
  }
})
</script>
