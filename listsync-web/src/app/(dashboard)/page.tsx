export default function DashboardHomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white titillium-web-bold">
          Welcome to ListSync
        </h1>
        <p className="text-purple-200/70 titillium-web-light">
          Your media synchronization dashboard is ready
        </p>
      </div>
      
      <div className="glass-card p-8">
        <div className="text-center py-12">
          <div className="text-6xl mb-6">🎬</div>
          <h2 className="text-2xl font-semibold text-white mb-3 titillium-web-semibold">
            ListSync Web UI
          </h2>
          <p className="text-purple-200/70 mb-8 max-w-md mx-auto titillium-web-light">
            Ready to sync your watchlists with your media server. Connect your favorite platforms and automate your media requests.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="glass-card p-6 purple-gradient-subtle">
              <div className="w-12 h-12 rounded-lg bg-purple-600/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔗</span>
              </div>
              <h3 className="font-semibold text-purple-100 mb-2 titillium-web-semibold">Connect</h3>
              <p className="text-sm text-purple-200/70 titillium-web-light">Link your watchlist services like IMDb, Trakt, and Letterboxd</p>
            </div>
            
            <div className="glass-card p-6 purple-gradient-subtle">
              <div className="w-12 h-12 rounded-lg bg-purple-600/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="font-semibold text-purple-100 mb-2 titillium-web-semibold">Sync</h3>
              <p className="text-sm text-purple-200/70 titillium-web-light">Automatically request media from your connected lists</p>
            </div>
            
            <div className="glass-card p-6 purple-gradient-subtle">
              <div className="w-12 h-12 rounded-lg bg-purple-600/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎉</span>
              </div>
              <h3 className="font-semibold text-purple-100 mb-2 titillium-web-semibold">Enjoy</h3>
              <p className="text-sm text-purple-200/70 titillium-web-light">Watch your content as it becomes available</p>
            </div>
          </div>
          
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/dashboard/lists" 
              className="glass-button-primary px-6 py-3 rounded-lg font-medium transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/25 titillium-web-semibold"
            >
              Manage Lists
            </a>
            <a 
              href="/dashboard/settings" 
              className="glass-button px-6 py-3 rounded-lg font-medium text-purple-200 hover:text-purple-100 titillium-web-regular"
            >
              Configure Settings
            </a>
          </div>
        </div>
      </div>
    </div>
  )
} 
