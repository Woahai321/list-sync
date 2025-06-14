"use client"

import { ReactNode } from 'react'

// Base chart container component
interface ChartContainerProps {
  title: string
  icon: ReactNode
  children: ReactNode
  className?: string
}

export function ChartContainer({ title, icon, children, className = "" }: ChartContainerProps) {
  return (
    <div className={`glass-card p-6 rounded-lg border border-white/20 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white titillium-web-semibold">
          {title}
        </h3>
        {icon}
      </div>
      {children}
    </div>
  )
}

// Placeholder chart component for development
interface PlaceholderChartProps {
  icon: ReactNode
  description: string
  height?: string
}

export function PlaceholderChart({ icon, description, height = "h-64" }: PlaceholderChartProps) {
  return (
    <div className={`${height} flex items-center justify-center text-white/60`}>
      <div className="text-center">
        {icon}
        <p className="mt-2 text-sm">{description}</p>
      </div>
    </div>
  )
}

// Metric card component
interface MetricCardProps {
  title: string
  value: string | number
  icon: ReactNode
  trend?: {
    value: string
    positive: boolean
    icon: ReactNode
  }
  status?: {
    text: string
    color: string
    icon: ReactNode
  }
}

export function MetricCard({ title, value, icon, trend, status }: MetricCardProps) {
  return (
    <div className="glass-card p-6 rounded-lg border border-white/20">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white/60 text-sm titillium-web-light">{title}</p>
          <p className="text-2xl font-bold text-white titillium-web-bold">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
        {icon}
      </div>
      <div className="mt-4 flex items-center gap-2">
        {trend && (
          <>
            {trend.icon}
            <span className={`text-sm ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
              {trend.value}
            </span>
          </>
        )}
        {status && (
          <>
            {status.icon}
            <span className={`text-sm ${status.color}`}>
              {status.text}
            </span>
          </>
        )}
      </div>
    </div>
  )
}

// Simple bar chart component (will be enhanced with real charting library)
interface SimpleBarChartProps {
  data: Array<{ label: string; value: number; color?: string }>
  height?: string
}

export function SimpleBarChart({ data, height = "h-64" }: SimpleBarChartProps) {
  if (!data.length) {
    return (
      <div className={`${height} flex items-center justify-center text-white/60`}>
        <p>No data available</p>
      </div>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))

  return (
    <div className={`${height} flex items-end justify-between gap-2 p-4`}>
      {data.map((item, index) => (
        <div key={index} className="flex flex-col items-center flex-1">
          <div 
            className="w-full rounded-t-lg transition-all duration-300 hover:opacity-80"
            style={{
              height: `${(item.value / maxValue) * 100}%`,
              backgroundColor: item.color || '#9d34da',
              minHeight: '4px'
            }}
          />
          <span className="text-xs text-white/60 mt-2 text-center truncate w-full">
            {item.label}
          </span>
          <span className="text-xs text-white/80 font-semibold">
            {item.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// Simple line chart component (will be enhanced with real charting library)
interface SimpleLineChartProps {
  data: Array<{ label: string; value: number }>
  height?: string
  color?: string
}

export function SimpleLineChart({ data, height = "h-64", color = "#9d34da" }: SimpleLineChartProps) {
  if (!data.length) {
    return (
      <div className={`${height} flex items-center justify-center text-white/60`}>
        <p>No data available</p>
      </div>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value))
  const range = maxValue - minValue || 1

  return (
    <div className={`${height} p-4`}>
      <div className="relative h-full">
        <svg className="w-full h-full" viewBox="0 0 400 200">
          <defs>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0.1" />
            </linearGradient>
          </defs>
          
          {/* Grid lines */}
          {[0, 1, 2, 3, 4].map(i => (
            <line
              key={i}
              x1="0"
              y1={i * 40}
              x2="400"
              y2={i * 40}
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="1"
            />
          ))}
          
          {/* Line path */}
          <path
            d={`M ${data.map((point, index) => 
              `${(index / (data.length - 1)) * 400},${200 - ((point.value - minValue) / range) * 180}`
            ).join(' L ')}`}
            fill="none"
            stroke={color}
            strokeWidth="2"
          />
          
          {/* Area fill */}
          <path
            d={`M ${data.map((point, index) => 
              `${(index / (data.length - 1)) * 400},${200 - ((point.value - minValue) / range) * 180}`
            ).join(' L ')} L 400,200 L 0,200 Z`}
            fill="url(#lineGradient)"
          />
          
          {/* Data points */}
          {data.map((point, index) => (
            <circle
              key={index}
              cx={(index / (data.length - 1)) * 400}
              cy={200 - ((point.value - minValue) / range) * 180}
              r="4"
              fill={color}
              className="hover:r-6 transition-all duration-200"
            />
          ))}
        </svg>
      </div>
    </div>
  )
}

// Status indicator component
interface StatusIndicatorProps {
  status: 'success' | 'warning' | 'error' | 'info'
  text: string
  count?: number
}

export function StatusIndicator({ status, text, count }: StatusIndicatorProps) {
  const colors = {
    success: 'text-green-400 bg-green-400/20 border-green-400/30',
    warning: 'text-amber-400 bg-amber-400/20 border-amber-400/30',
    error: 'text-red-400 bg-red-400/20 border-red-400/30',
    info: 'text-blue-400 bg-blue-400/20 border-blue-400/30'
  }

  return (
    <div className={`px-3 py-2 rounded-lg border text-sm ${colors[status]}`}>
      <span>{text}</span>
      {count !== undefined && (
        <span className="ml-2 font-semibold">({count})</span>
      )}
    </div>
  )
} 