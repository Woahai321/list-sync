"use client"

import { useEffect, useState } from "react"

interface AnimatedCounterProps {
  value: number
  duration?: number
  className?: string
  prefix?: string
  suffix?: string
  formatter?: (value: number) => string
}

export function AnimatedCounter({ 
  value, 
  duration = 800, 
  className = "",
  prefix = "",
  suffix = "",
  formatter
}: AnimatedCounterProps) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let startTime: number
    let animationFrame: number

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      setCount(Math.floor(easeOutQuart * value))

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate)
      }
    }

    animationFrame = requestAnimationFrame(animate)

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame)
      }
    }
  }, [value, duration])

  const formatValue = (val: number) => {
    if (formatter) {
      return formatter(val)
    }
    return val.toLocaleString()
  }

  return (
    <span className={`counter-animate ${className}`}>
      {prefix}{formatValue(count)}{suffix}
    </span>
  )
} 
