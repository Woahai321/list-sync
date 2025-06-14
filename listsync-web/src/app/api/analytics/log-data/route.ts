import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  try {
    // Try multiple possible log file paths
    const logPaths = [
      path.join(process.cwd(), '..', '..', 'logs', 'listsync-core.log'),
      path.join(process.cwd(), '..', 'logs', 'listsync-core.log'), 
      path.join(process.cwd(), 'logs', 'listsync-core.log'),
      '/var/log/supervisor/listsync-core.log',
      '/usr/src/app/logs/listsync-core.log',
      'data/list_sync.log'
    ]

    let logContent = ''
    let foundPath = ''

    for (const logPath of logPaths) {
      try {
        if (fs.existsSync(logPath)) {
          logContent = fs.readFileSync(logPath, 'utf-8')
          foundPath = logPath
          break
        }
      } catch (err) {
        // Continue to next path
        continue
      }
    }

    if (!logContent) {
      return NextResponse.json(
        { error: 'Log file not found in any expected locations' },
        { status: 404 }
      )
    }

    return new NextResponse(logContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain',
        'X-Log-Path': foundPath
      }
    })

  } catch (error) {
    console.error('Error reading log file:', error)
    return NextResponse.json(
      { error: 'Failed to read log file' },
      { status: 500 }
    )
  }
} 