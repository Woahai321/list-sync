import { NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import path from "path"
import fs from "fs"

const execAsync = promisify(exec)

export async function GET() {
  try {
    // Check if ListSync database exists
    const dbPath = path.join(process.cwd(), "../data/list_sync.db")
    const databaseStatus = fs.existsSync(dbPath) ? "healthy" : "error"

    // Get system uptime (mock for now)
    const uptime = process.uptime()

    // Try to get Overseerr connection status from Python backend
    let overseerrConnection: {
      isConnected: boolean
      lastChecked: string
      error?: string
    } = {
      isConnected: false,
      lastChecked: new Date().toISOString(),
      error: "Not configured"
    }

    try {
      // This would call the Python ListSync to check Overseerr connection
      // For now, we'll mock this and implement the actual Python bridge later
      const { stdout } = await execAsync("python --version")
      if (stdout) {
        overseerrConnection = {
          isConnected: true,
          lastChecked: new Date().toISOString(),
          error: undefined
        }
      }
    } catch {
      overseerrConnection.error = "Python backend unavailable"
    }

    const systemHealth = {
      overseerrConnection,
      databaseStatus: databaseStatus as "healthy" | "error",
      uptime: Math.floor(uptime),
      lastSyncTime: null, // Will be populated from database
      nextSyncTime: null, // Will be calculated based on sync interval
    }

    return NextResponse.json(systemHealth)
  } catch (error) {
    console.error("Health check failed:", error)
    return NextResponse.json(
      { error: "Health check failed" },
      { status: 500 }
    )
  }
} 