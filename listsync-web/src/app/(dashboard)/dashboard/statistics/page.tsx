"use client"

import { DashboardOverview } from "@/components/dashboard/overview"

export default function StatisticsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">
          Sync Statistics
        </h1>
        <p className="text-purple-200/70 titillium-web-light">
          Detailed overview of your ListSync synchronization data
        </p>
      </div>

      {/* Statistics Overview - Full Width */}
      <div className="min-w-0">
        <DashboardOverview />
      </div>
    </div>
  )
} 