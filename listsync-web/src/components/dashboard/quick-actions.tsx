"use client"

import { Button } from "@/components/ui/button"
import { RotateCw, Plus, Settings, Activity, Zap, CheckCircle, AlertCircle } from "lucide-react"
import { useState } from "react"
import { apiClient } from "@/lib/api/client"
import { toast } from "sonner"

export function QuickActions() {
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncSuccess, setSyncSuccess] = useState(false)

  const handleSyncNow = async () => {
    setIsSyncing(true)
    setSyncSuccess(false)
    
    try {
      // First check if we can trigger sync
      const syncStatus = await apiClient.getSyncProcessStatus()
      
      if (!syncStatus.can_trigger_sync) {
        toast.error("Cannot trigger sync", {
          description: "No ListSync process found. Please ensure ListSync is running in automated mode."
        })
        return
      }

      // Trigger the sync
      const result = await apiClient.triggerManualSync()
      
      if (result.success) {
        setSyncSuccess(true)
        toast.success("Sync triggered successfully!", {
          description: result.note
        })
        
        // Reset success state after 3 seconds
        setTimeout(() => setSyncSuccess(false), 3222)
      } else {
        toast.error("Failed to trigger sync", {
          description: "Check the console for more details"
        })
      }
    } catch (error) {
      console.error("Error triggering sync:", error)
      toast.error("Failed to trigger sync", {
        description: error instanceof Error ? error.message : "Unknown error occurred"
      })
    } finally {
      setIsSyncing(false)
    }
  }

  const handleAddList = () => {
    // TODO: Open add list modal
    toast.info("Add List feature coming soon!")
  }

  const handleViewActivity = () => {
    // Navigate to activity page
    window.location.href = "/dashboard/activity"
  }

  const handleSettings = () => {
    // TODO: Open settings modal
    toast.info("Settings feature coming soon!")
  }

  const actions = [
    {
      title: "Sync Now",
      description: isSyncing ? "Triggering sync..." : syncSuccess ? "Sync triggered!" : "Trigger immediate sync",
      icon: syncSuccess ? CheckCircle : RotateCw,
      onClick: handleSyncNow,
      variant: "outline" as const,
      disabled: isSyncing,
      loading: isSyncing,
      success: syncSuccess,
    },
    {
      title: "Add List",
      description: "Connect new watchlist",
      icon: Plus,
      onClick: handleAddList,
      variant: "outline" as const,
      disabled: false,
      loading: false,
      success: false,
    },
    {
      title: "View Activity",
      description: "Recent sync history",
      icon: Activity,
      onClick: handleViewActivity,
      variant: "outline" as const,
      disabled: false,
      loading: false,
      success: false,
    },
    {
      title: "Settings",
      description: "Configure ListSync",
      icon: Settings,
      onClick: handleSettings,
      variant: "outline" as const,
      disabled: false,
      loading: false,
      success: false,
    },
  ]

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg status-info">
          <Zap className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-white titillium-web-semibold">
            Quick Actions
          </h3>
          <p className="text-sm titillium-web-light" style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            Manage your sync operations
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {actions.map((action, index) => (
          <div
            key={action.title}
            className="group"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <Button 
              onClick={action.onClick}
              disabled={action.disabled}
              className={`w-full h-32 p-4 flex flex-col items-center justify-center gap-3 text-center transition-all duration-300 glass-button hover:scale-105 ${
                action.success ? 'border-green-500/50 bg-green-500/10' : ''
              } ${
                action.disabled ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              variant={action.variant}
            >
              <div className={`p-3 rounded-lg transition-all duration-300 group-hover:scale-110 ${
                action.loading ? 'animate-spin' : ''
              } ${
                action.success ? 'bg-green-500/20 border-green-500/30' : 'bg-purple-500/20 border-purple-500/30'
              }`}
              style={{
                backgroundColor: action.success ? 'rgba(34, 197, 94, 0.2)' : 'rgba(157, 52, 218, 0.2)',
                borderColor: action.success ? 'rgba(34, 197, 94, 0.3)' : 'rgba(157, 52, 218, 0.3)'
              }}>
                <action.icon className={`h-5 w-5 ${
                  action.success ? 'text-green-400' : ''
                }`} />
              </div>
              
              <div className="space-y-1">
                <div className="font-medium text-sm titillium-web-semibold">
                  {action.title}
                </div>
                <div className="text-xs opacity-80 titillium-web-light"
                style={{
                  color: 'rgba(255, 255, 255, 0.8)'
                }}>
                  {action.description}
                </div>
              </div>
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
} 
